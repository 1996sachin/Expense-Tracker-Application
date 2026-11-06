from django.conf import settings
from django.db import models
class Transaction(models.Model):
    class Type(models.TextChoices):
        INCOME = 'income'
        EXPENSE = 'expense'
        TRANSFER = 'transfer'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey('bankaccounts.BankAccount', on_delete=models.PROTECT, related_name='transactions')
    category = models.ForeignKey('categories.Category', null=True, blank=True, on_delete=models.SET_NULL)
    type = models.CharField(max_length=10, choices=Type.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField()
    note = models.TextField(blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    attachment = models.ImageField(upload_to='receipts/', null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    transfer_to_account = models.ForeignKey('bankaccounts.BankAccount', null=True, blank=True, on_delete=models.PROTECT, related_name='incoming_transfers')
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # SMS Automation and Ingestion extensions
    reference_id = models.CharField(max_length=120, blank=True, null=True, db_index=True)
    raw_sms = models.TextField(blank=True)
    merchant = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ['-date', '-id']


class RecurringTransaction(models.Model):
    class Type(models.TextChoices):
        INCOME = 'income'
        EXPENSE = 'expense'

    class Frequency(models.TextChoices):
        DAILY = 'daily'
        WEEKLY = 'weekly'
        MONTHLY = 'monthly'
        YEARLY = 'yearly'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recurring_transactions')
    account = models.ForeignKey('bankaccounts.BankAccount', on_delete=models.PROTECT, related_name='recurring_transactions')
    category = models.ForeignKey('categories.Category', blank=True, null=True, on_delete=models.SET_NULL)
    amount = models.DecimalField(decimal_places=2, max_digits=14)
    type = models.CharField(choices=Type.choices, max_length=10)
    frequency = models.CharField(choices=Frequency.choices, max_length=20)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    next_run_date = models.DateField()
    note = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['next_run_date', '-created_at']


class CategorizationRule(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='categorization_rules')
    category = models.ForeignKey('categories.Category', on_delete=models.CASCADE, related_name='rules')
    keywords = models.TextField(help_text="Comma-separated keywords to match in merchant or SMS body")
    priority = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['priority', '-id']
