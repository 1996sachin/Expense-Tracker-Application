from datetime import timedelta
from django.db import transaction as db_transaction
from django.db.models import Sum, Case, When, DecimalField
from django.db.models.functions import TruncMonth
from django.utils.timezone import now
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Transaction
from .serializers import TransactionSerializer
class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class=TransactionSerializer; filterset_fields=['account','category','type','date']; search_fields=['note','payment_method','tags']; ordering_fields=['date','amount','created_at']
    def get_queryset(self): return Transaction.objects.filter(user=self.request.user).select_related('account','category')
    def perform_create(self, serializer):
        with db_transaction.atomic(): serializer.save()
    def perform_update(self, serializer):
        with db_transaction.atomic(): serializer.save()
    def perform_destroy(self, instance):
        with db_transaction.atomic(): instance.delete()
    @action(detail=False)
    def insights(self,request):
        period=request.query_params.get('period','month'); days={'week':56,'month':365,'year':1825}.get(period,365); start=now().date()-timedelta(days=days)
        qs=self.get_queryset().filter(date__gte=start).exclude(type='transfer').annotate(bucket=TruncMonth('date')).values('bucket').annotate(income=Sum(Case(When(type='income',then='amount'),default=0,output_field=DecimalField())),expense=Sum(Case(When(type='expense',then='amount'),default=0,output_field=DecimalField()))).order_by('bucket')
        trend=[{'date':x['bucket'].strftime('%b %Y'),'income':float(x['income'] or 0),'expense':float(x['expense'] or 0),'savings':float((x['income'] or 0)-(x['expense'] or 0))} for x in qs]
        cats=self.get_queryset().filter(type='expense',date__gte=start).values('category__name').annotate(total=Sum('amount')).order_by('-total')[:8]
        return Response({'trend':trend,'categories':[{'name':x['category__name'] or 'Uncategorized','value':float(x['total'])} for x in cats]})
