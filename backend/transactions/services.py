from django.db.models import F
from bankaccounts.models import BankAccount
def apply_balance(transaction, multiplier=1):
    sign = 1 if transaction.type == 'income' else -1
    BankAccount.objects.filter(pk=transaction.account_id).update(current_balance=F('current_balance') + sign * transaction.amount * multiplier)
    if transaction.type == 'transfer' and transaction.transfer_to_account_id:
        BankAccount.objects.filter(pk=transaction.transfer_to_account_id).update(current_balance=F('current_balance') + transaction.amount * multiplier)
