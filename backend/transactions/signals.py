from django.db import transaction as db_transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from .models import Transaction
from .services import apply_balance
@receiver(pre_save, sender=Transaction)
def capture_old(sender, instance, **kwargs):
    if instance.pk: instance._old = Transaction.objects.get(pk=instance.pk)
@receiver(post_save, sender=Transaction)
def update_balance(sender, instance, created, **kwargs):
    with db_transaction.atomic():
        if not created: apply_balance(instance._old, -1)
        apply_balance(instance)
@receiver(post_delete, sender=Transaction)
def restore_balance(sender, instance, **kwargs):
    with db_transaction.atomic(): apply_balance(instance, -1)
