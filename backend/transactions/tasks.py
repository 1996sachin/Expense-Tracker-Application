from datetime import timedelta
from django.utils.timezone import now
from .models import Transaction


def generate_recurring_transactions():
    today = now().date()
    made = 0
    for tx in Transaction.objects.filter(is_recurring=True):
        delta = {'daily': 1, 'weekly': 7, 'monthly': 30}.get(tx.recurrence_rule)
        if delta and tx.date + timedelta(days=delta) <= today:
            Transaction.objects.create(
                user=tx.user,
                account=tx.account,
                category=tx.category,
                type=tx.type,
                amount=tx.amount,
                date=today,
                note=tx.note,
                payment_method=tx.payment_method,
                transfer_to_account=tx.transfer_to_account,
                is_recurring=True,
                recurrence_rule=tx.recurrence_rule,
            )
            made += 1
    return made
