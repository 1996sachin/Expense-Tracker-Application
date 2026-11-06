from django.db import transaction as db_transaction
from .models import Transaction
from .sms_parser import parse_sms
from .categorizer import resolve_category_for_sms
from .account_resolver import resolve_bank_account_for_sms


def process_incoming_sms(user, sms_text: str, sender: str = '') -> dict:
    """
    Core SMS Ingestion Pipeline:
    1. Parse SMS using regex (extracts amount, type, merchant, TrxID, balance, bank hint)
    2. Check for duplicate transactions (via reference_id / TrxID or same-day fingerprint)
    3. Auto-resolve or create matching BankAccount (eSewa, Nabil, etc.)
    4. Auto-categorize via CategorizationRules and Nepali keyword dictionary
    5. Save Transaction and synchronize account balance
    """
    parsed = parse_sms(sms_text, sender)

    if not parsed.get('is_transaction'):
        return {
            'status': 'ignored',
            'reason': parsed.get('reason', 'Message was not recognized as a financial transaction (e.g. OTP, promotional alert).'),
            'parsed': parsed
        }

    # 2. Deduplication check (Crucial for iOS Shortcuts / Android automations)
    ref_id = parsed.get('reference_id')
    if ref_id:
        existing = Transaction.objects.filter(user=user, reference_id=ref_id).first()
        if existing:
            return {
                'status': 'duplicate',
                'message': f"Transaction already recorded with Reference ID: {ref_id}",
                'transaction': {
                    'id': existing.id,
                    'type': existing.type,
                    'amount': float(existing.amount),
                    'merchant': existing.merchant or existing.note,
                    'date': str(existing.date),
                    'reference_id': existing.reference_id,
                    'category': existing.category.name if existing.category else 'Uncategorized',
                    'account': existing.account.name
                }
            }
    else:
        # Fallback deduplication: check identical user, date, amount, type and merchant
        existing = Transaction.objects.filter(
            user=user,
            date=parsed['date'],
            amount=parsed['amount'],
            type=parsed['type'],
            merchant=parsed['merchant']
        ).first()
        if existing:
            return {
                'status': 'duplicate',
                'message': 'An identical transaction was already recorded today.',
                'transaction': {
                    'id': existing.id,
                    'type': existing.type,
                    'amount': float(existing.amount),
                    'merchant': existing.merchant or existing.note,
                    'date': str(existing.date),
                    'category': existing.category.name if existing.category else 'Uncategorized',
                    'account': existing.account.name
                }
            }

    # 3. Resolve Account (eSewa, Bank, Wallet)
    account = resolve_bank_account_for_sms(user, parsed)

    # 4. Resolve Category (Rules engine + default categories)
    category = resolve_category_for_sms(
        user=user,
        merchant=parsed['merchant'],
        raw_sms=sms_text,
        tx_type=parsed['type']
    )

    # 5. Create Transaction with atomic balance update
    with db_transaction.atomic():
        tx = Transaction.objects.create(
            user=user,
            account=account,
            category=category,
            type=parsed['type'],
            amount=parsed['amount'],
            date=parsed['date'],
            note=f"{parsed['merchant']} (SMS auto-tracked)",
            merchant=parsed['merchant'],
            reference_id=ref_id or None,
            raw_sms=sms_text,
            payment_method=account.name,
            tags=['sms-auto', account.name.lower()]
        )

        # If SMS contained the bank's authoritative balance, sync it directly
        if parsed.get('balance') is not None:
            account.current_balance = parsed['balance']
            account.save(update_fields=['current_balance'])

    return {
        'status': 'success',
        'message': f"Successfully recorded {parsed['type']} of {parsed['currency']} {parsed['amount']} at {parsed['merchant']}",
        'transaction': {
            'id': tx.id,
            'type': tx.type,
            'amount': float(tx.amount),
            'currency': account.currency,
            'merchant': tx.merchant,
            'category': category.name if category else 'Uncategorized',
            'account': account.name,
            'reference_id': tx.reference_id,
            'date': str(tx.date),
            'balance': float(account.current_balance)
        },
        'parsed': {
            'amount': float(parsed['amount']),
            'currency': parsed['currency'],
            'type': parsed['type'],
            'merchant': parsed['merchant'],
            'reference_id': parsed['reference_id'],
            'account_hint': parsed['account_hint'],
            'bank_name': parsed['bank_name']
        }
    }
