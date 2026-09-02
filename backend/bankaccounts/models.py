from decimal import Decimal
from django.conf import settings
from django.db import models
class BankAccount(models.Model):
    class Type(models.TextChoices): SAVINGS='savings'; CHECKING='checking'; CREDIT='credit_card'; CASH='cash'; WALLET='wallet'
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='bank_accounts')
    name = models.CharField(max_length=100); bank_name = models.CharField(max_length=100,blank=True)
    account_type = models.CharField(max_length=20,choices=Type.choices); currency = models.CharField(max_length=3,default=settings.DEFAULT_CURRENCY)
    opening_balance = models.DecimalField(max_digits=14,decimal_places=2,default=Decimal('0'))
    current_balance = models.DecimalField(max_digits=14,decimal_places=2,default=Decimal('0'))
    color = models.CharField(max_length=7,default='#6366f1'); icon = models.CharField(max_length=40,blank=True); is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-is_active','name']
