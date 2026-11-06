import re
from datetime import datetime, date
from decimal import Decimal


KNOWN_BANKS = [
    'Nabil', 'Global IME', 'NIC Asia', 'Sanima', 'Himalayan', 'Siddhartha',
    'Prabhu', 'Rastriya Banijya Bank', 'RBB', 'Everest', 'Standard Chartered',
    'Kumari', 'Prime', 'NMB', 'Machhapuchchhre', 'Nepal Bank', 'Citizens',
    'Laxmi Sunrise', 'Agricultural Development Bank', 'ADBL', 'eSewa', 'Khalti', 'Fonepay'
]

OTP_KEYWORDS = [
    r'\botp\b',
    r'\bone[- ]time[- ]password\b',
    r'\bverification[- ]code\b',
    r'\bsecurity[- ]code\b',
    r'\blogin[- ]code\b',
    r'\bdo not share\b',
    r'\bdon\'t share\b',
]


def parse_sms(sms_text: str, sender: str = '') -> dict:
    """
    Parses incoming SMS from Nepali banks, eSewa, wallets, or card payments.
    Extracts:
      - is_transaction: bool
      - type: 'expense' | 'income'
      - amount: Decimal
      - currency: str (default 'NPR')
      - merchant: str
      - reference_id: str
      - balance: Decimal | None
      - account_hint: str
      - bank_name: str
      - date: datetime.date
      - raw_text: str
    """
    cleaned = (sms_text or '').strip()
    if not cleaned:
        return {'is_transaction': False, 'error': 'Empty message'}

    # 1. OTP / Spam Check
    is_debit = bool(re.search(r'\b(debit|debited|paid|spent|deducted|withdrawn|purchase|payment|transferred to|sent to)\b', cleaned, re.IGNORECASE))
    is_credit = bool(re.search(r'\b(credit|credited|received|cash[- ]?in|deposited|load|refund|transferred from)\b', cleaned, re.IGNORECASE))

    if not is_debit and not is_credit:
        for otp_pat in OTP_KEYWORDS:
            if re.search(otp_pat, cleaned, re.IGNORECASE):
                return {'is_transaction': False, 'reason': 'OTP/Security code message'}
        return {'is_transaction': False, 'reason': 'No debit or credit indication found'}

    tx_type = 'income' if (is_credit and not is_debit) else 'expense'

    # 2. Amount and Currency Extraction
    amount = None
    currency = 'NPR'

    # Look for explicit currency prefix/suffix: NPR, Rs, NRs, Tk, BDT, USD, $
    curr_match = re.search(r'\b(NPR|NRs\.?|Rs\.?|Tk\.?|BDT|USD)\b', cleaned, re.IGNORECASE)
    if curr_match:
        found_curr = curr_match.group(1).upper().replace('.', '')
        if found_curr in ('RS', 'NRS'):
            currency = 'NPR'
        elif found_curr in ('TK',):
            currency = 'BDT'
        else:
            currency = found_curr

    # Matches: NPR 1,200.00 | Rs. 850 | Rs 350.50 | 500.00 NPR | debited by 850.00
    amt_patterns = [
        r'(?:NPR|NRs\.?|Rs\.?|Tk\.?|BDT|\$|USD)\s*([0-9,]+(?:\.[0-9]{1,2})?)',
        r'([0-9,]+(?:\.[0-9]{1,2})?)\s*(?:NPR|NRs\.?|Rs\.?|Tk\.?|BDT)',
        r'(?:debited|credited|paid|spent|received|for)\s+(?:by\s+)?(?:NPR|NRs\.?|Rs\.?)?\s*([0-9,]+(?:\.[0-9]{1,2})?)',
    ]

    for pat in amt_patterns:
        match = re.search(pat, cleaned, re.IGNORECASE)
        if match:
            raw_amt = match.group(1).replace(',', '')
            try:
                val = Decimal(raw_amt)
                if val > 0:
                    amount = val
                    break
            except Exception:
                continue

    if amount is None:
        return {'is_transaction': False, 'reason': 'Could not extract amount from message'}

    # 3. Reference ID / Transaction ID Extraction
    reference_id = ''
    ref_patterns = [
        r'(?:Trx\s*ID|Txn\s*ID|TrxID|TxnID|Ref\s*\/Txn|Ref\s*No|RefNo|Ref|Reference\s*ID|Txn\s*Ref)\s*[:#-]?\s*([A-Za-z0-9_\-]+)',
        r'(?:Code)\s*[:#-]\s*([A-Za-z0-9_\-]+)',
    ]
    for pat in ref_patterns:
        match = re.search(pat, cleaned, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # Exclude words that are accidentally matched
            if candidate.lower() not in ('npr', 'rs', 'avl', 'bal', 'is', 'successful'):
                reference_id = candidate
                break

    # 4. Balance Extraction
    balance = None
    bal_patterns = [
        r'(?:Avl\s*Bal|Available\s*Balance|Remaining\s*Balance|Bal|Current\s*Balance)\s*[:#-]?\s*(?:NPR|NRs\.?|Rs\.?|Tk\.?|BDT)?\s*([0-9,]+(?:\.[0-9]{1,2})?)',
    ]
    for pat in bal_patterns:
        match = re.search(pat, cleaned, re.IGNORECASE)
        if match:
            raw_bal = match.group(1).replace(',', '')
            try:
                bal_val = Decimal(raw_bal)
                balance = bal_val
                break
            except Exception:
                pass

    # 5. Account & Bank Hints
    combined_source = f"{sender} {cleaned}"
    bank_name = ''
    for b in KNOWN_BANKS:
        if re.search(rf'\b{re.escape(b)}\b', combined_source, re.IGNORECASE):
            bank_name = b
            break

    account_hint = ''
    if 'esewa' in combined_source.lower():
        account_hint = 'eSewa'
    elif 'khalti' in combined_source.lower():
        account_hint = 'Khalti'
    else:
        # Check for account ending patterns: a/c ...1234, a/c *1234, ending 1234
        ac_match = re.search(r'(?:a\/c|account)\s*(?:\.{2,3}|\*+|ending\s*)?([0-9]{3,6})', cleaned, re.IGNORECASE)
        if ac_match:
            account_hint = ac_match.group(1)
        elif bank_name:
            account_hint = bank_name

    # 6. Merchant / Counterparty Extraction
    merchant = ''
    merchant_patterns = [
        r'for payment to\s+([^.,\n]+)',
        r'for\s+([^.,\n]+?)(?:\.\s*(?:Ref|Trx|Bal|Available)|$)',
        r'paid for\s+([^.,\n]+)',
        r'paid to\s+([^.,\n]+)',
        r'purchase at\s+([^.,\n]+)',
        r'towards\s+Fonepay\s*[:\/]?\s*([^.,\n]+)',
        r'towards\s+([^.,\n]+)',
        r'at\s+([^.,\n]+?)\s+(?:through|via)\s+Fonepay',
        r'at\s+([^.,\n]+?)(?:\s+on|\.\s*Ref|\.\s*Txn|\.\s*Bal|$)',
        r'done via Mobile Banking to\s+([^.,\n]+)',
        r'to\s+([^.,\n]+?)\s+is successful',
        r'from\s+([^.,\n]+?)(?:\.\s*Ref|\.\s*Trx|\.\s*Bal|$)',
        r'by\s+([^.,\n]+?)(?:\.\s*Ref|\.\s*Txn|\.\s*Avl|\.\s*Bal|$)',
    ]

    for pat in merchant_patterns:
        match = re.search(pat, cleaned, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # Clean noise from merchant string
            candidate = re.sub(r'\b(POS\/QR purchase|QR purchase|POS purchase|through Fonepay|via Fonepay|via Mobile Banking|Mobile Banking)\b', '', candidate, flags=re.IGNORECASE).strip()
            candidate = re.sub(r'^(at|to|for|from)\s+', '', candidate, flags=re.IGNORECASE).strip()
            candidate = re.sub(r'[:\-_]+$', '', candidate).strip()
            if candidate and len(candidate) > 1 and not candidate.isdigit():
                merchant = candidate
                break

    if not merchant:
        if tx_type == 'income':
            merchant = 'Deposit / Transfer'
        elif account_hint:
            merchant = f'Payment via {account_hint}'
        else:
            merchant = 'General Purchase'

    # Date extraction (optional, default to today)
    tx_date = date.today()
    # Matches patterns like 28-SEP-26 or 2026-09-28 or 28-09-2026
    date_match = re.search(r'\b(\d{4}[-/]\d{2}[-/]\d{2})\b', cleaned)
    if date_match:
        try:
            tx_date = datetime.strptime(date_match.group(1).replace('/', '-'), '%Y-%m-%d').date()
        except Exception:
            pass

    return {
        'is_transaction': True,
        'type': tx_type,
        'amount': amount,
        'currency': currency,
        'merchant': merchant,
        'reference_id': reference_id,
        'balance': balance,
        'account_hint': account_hint,
        'bank_name': bank_name,
        'date': tx_date,
        'raw_text': cleaned,
    }
