from decimal import Decimal
from django.db.models import Q
from bankaccounts.models import BankAccount


def resolve_bank_account_for_sms(user, parsed_data: dict) -> BankAccount:
    """
    Finds or automatically creates the matching BankAccount for the SMS transaction:
    - eSewa / Wallets
    - Mobile Banking / Specific Bank (Nabil, NIC Asia, Global IME, etc.)
    - Account number last digits (e.g. 1234)
    """
    account_hint = (parsed_data.get('account_hint') or '').strip()
    bank_name = (parsed_data.get('bank_name') or '').strip()
    currency = parsed_data.get('currency', 'NPR')
    balance = parsed_data.get('balance')

    # 1. Match eSewa / digital wallet
    if account_hint.lower() == 'esewa' or 'esewa' in bank_name.lower():
        account = BankAccount.objects.filter(user=user, is_active=True).filter(
            Q(name__icontains='esewa') | Q(bank_name__icontains='esewa') | Q(account_type=BankAccount.Type.WALLET)
        ).first()
        if not account:
            account = BankAccount.objects.create(
                user=user,
                name='eSewa',
                bank_name='eSewa Wallet',
                account_type=BankAccount.Type.WALLET,
                currency=currency,
                opening_balance=balance or Decimal('0'),
                current_balance=balance or Decimal('0'),
                color='#10b981',
                icon='wallet'
            )
        return account

    # 2. Match bank name
    if bank_name:
        account = BankAccount.objects.filter(user=user, is_active=True).filter(
            Q(name__icontains=bank_name) | Q(bank_name__icontains=bank_name)
        ).first()
        if account:
            return account

    # 3. Match account ending digits
    if account_hint and account_hint.isdigit():
        account = BankAccount.objects.filter(user=user, is_active=True).filter(
            Q(name__icontains=account_hint) | Q(bank_name__icontains=account_hint)
        ).first()
        if account:
            return account

    # 4. Fallback to user's first active account
    first_active = BankAccount.objects.filter(user=user, is_active=True).first()
    if first_active:
        return first_active

    # 5. If no account exists for user, create a default Mobile Banking account
    acc_name = f"{bank_name} Bank" if bank_name else "Mobile Banking"
    return BankAccount.objects.create(
        user=user,
        name=acc_name,
        bank_name=bank_name or "Mobile Banking",
        account_type=BankAccount.Type.CHECKING,
        currency=currency,
        opening_balance=balance or Decimal('0'),
        current_balance=balance or Decimal('0'),
        color='#6366f1',
        icon='account_balance'
    )
