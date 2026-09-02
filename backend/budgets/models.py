from django.conf import settings
from django.db import models
class Budget(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE); category=models.ForeignKey('categories.Category',on_delete=models.CASCADE); period_start=models.DateField(); period_end=models.DateField(); limit_amount=models.DecimalField(max_digits=14,decimal_places=2)
    class Meta: ordering=['-period_start']
