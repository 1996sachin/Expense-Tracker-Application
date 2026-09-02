from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import BankAccount
from .serializers import BankAccountSerializer
class BankAccountViewSet(viewsets.ModelViewSet):
    serializer_class = BankAccountSerializer
    def get_queryset(self): return BankAccount.objects.filter(user=self.request.user)
    @action(detail=False)
    def summary(self,request):
        qs = self.get_queryset().filter(is_active=True); return Response({'net_worth':qs.aggregate(total=Sum('current_balance'))['total'] or 0,'accounts':self.get_serializer(qs,many=True).data})
