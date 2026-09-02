from django.conf import settings
from django.db import models
class Category(models.Model):
    class Type(models.TextChoices): INCOME='income'; EXPENSE='expense'
    user = models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.CASCADE,related_name='categories')
    name=models.CharField(max_length=60); type=models.CharField(max_length=10,choices=Type.choices); parent_category=models.ForeignKey('self',null=True,blank=True,on_delete=models.CASCADE,related_name='subcategories'); color=models.CharField(max_length=7,default='#64748b')
    class Meta: constraints=[models.UniqueConstraint(fields=['user','name','type','parent_category'],name='unique_category_per_user')]
