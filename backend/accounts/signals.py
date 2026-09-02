from django.db.models.signals import post_save
from django.dispatch import receiver

from bankaccounts.models import BankAccount
from .models import User


@receiver(post_save, sender=User)
def create_cash_wallet(sender, instance, created, **kwargs):
    if created:
        BankAccount.objects.get_or_create(
            user=instance,
            name='Cash Wallet',
            defaults={'account_type': BankAccount.Type.CASH, 'currency': instance.currency_preference, 'opening_balance': 0, 'current_balance': 0, 'icon': 'wallet'},
        )
