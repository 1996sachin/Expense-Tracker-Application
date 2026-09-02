from django.db.models import Sum
from rest_framework import serializers
from .models import Budget
class BudgetSerializer(serializers.ModelSerializer):
    actual = serializers.SerializerMethodField()
    class Meta: model=Budget; fields=['id','category','period_start','period_end','limit_amount','actual'] ; read_only_fields=['actual']
    def get_actual(self,obj):
        from transactions.models import Transaction
        return Transaction.objects.filter(user=obj.user,category=obj.category,type='expense',date__range=(obj.period_start,obj.period_end)).aggregate(total=Sum('amount'))['total'] or 0
    def create(self,data): data['user']=self.context['request'].user; return super().create(data)
