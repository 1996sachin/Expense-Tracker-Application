import calendar
from datetime import date, timedelta
from celery import shared_task
from django.db import transaction as db_transaction
from django.utils.timezone import now
from .models import Transaction, RecurringTransaction


def advance_date(d: date, frequency: str) -> date:
    if frequency in (RecurringTransaction.Frequency.DAILY, 'daily'):
        return d + timedelta(days=1)
    elif frequency in (RecurringTransaction.Frequency.WEEKLY, 'weekly'):
        return d + timedelta(days=7)
    elif frequency in (RecurringTransaction.Frequency.MONTHLY, 'monthly'):
        year = d.year + (d.month // 12)
        month = (d.month % 12) + 1
        max_day = calendar.monthrange(year, month)[1]
        day = min(d.day, max_day)
        return d.replace(year=year, month=month, day=day)
    elif frequency in (RecurringTransaction.Frequency.YEARLY, 'yearly'):
        year = d.year + 1
        try:
            return d.replace(year=year)
        except ValueError:
            return d.replace(year=year, day=28)
    return d + timedelta(days=1)


@shared_task
def generate_recurring_transactions():
    today = now().date()
    due_items = RecurringTransaction.objects.filter(
        is_active=True,
        next_run_date__lte=today,
    ).select_related('account', 'category', 'user')

    created_count = 0
    for item in due_items:
        if item.end_date and item.next_run_date > item.end_date:
            item.is_active = False
            item.save(update_fields=['is_active'])
            continue

        with db_transaction.atomic():
            Transaction.objects.create(
                user=item.user,
                account=item.account,
                category=item.category,
                type=item.type,
                amount=item.amount,
                date=item.next_run_date,
                note=item.note or f"Recurring {item.frequency} {item.type}",
                is_recurring=True,
                recurrence_rule=item.frequency,
            )
            created_count += 1

            next_date = advance_date(item.next_run_date, item.frequency)
            if item.end_date and next_date > item.end_date:
                item.is_active = False
            item.next_run_date = next_date
            item.save(update_fields=['next_run_date', 'is_active'])

    return created_count
