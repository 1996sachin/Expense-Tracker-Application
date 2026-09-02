from django.conf import settings
from django.db import models
class Transaction(models.Model):
    class Type(models.TextChoices): INCOME='income'; EXPENSE='expense'; TRANSFER='transfer'
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='transactions'); account=models.ForeignKey('bankaccounts.BankAccount',on_delete=models.PROTECT,related_name='transactions'); category=models.ForeignKey('categories.Category',null=True,blank=True,on_delete=models.SET_NULL)
    type=models.CharField(max_length=10,choices=Type.choices); amount=models.DecimalField(max_digits=14,decimal_places=2); date=models.DateField(); note=models.TextField(blank=True); payment_method=models.CharField(max_length=50,blank=True); attachment=models.ImageField(upload_to='receipts/',null=True,blank=True); tags=models.JSONField(default=list,blank=True)
    transfer_to_account=models.ForeignKey('bankaccounts.BankAccount',null=True,blank=True,on_delete=models.PROTECT,related_name='incoming_transfers'); is_recurring=models.BooleanField(default=False); recurrence_rule=models.CharField(max_length=10,blank=True); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-date','-id']
