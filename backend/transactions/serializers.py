from rest_framework import serializers
from .models import Transaction
from bankaccounts.models import BankAccount
class TransactionSerializer(serializers.ModelSerializer):
    class Meta: model=Transaction; fields='__all__'; read_only_fields=['user','created_at']
    def validate(self,data):
        account=data.get('account',getattr(self.instance,'account',None)); target=data.get('transfer_to_account',getattr(self.instance,'transfer_to_account',None)); typ=data.get('type',getattr(self.instance,'type',None))
        if data.get('amount',getattr(self.instance,'amount',0)) <= 0: raise serializers.ValidationError({'amount':'Amount must be positive.'})
        if account and account.user != self.context['request'].user: raise serializers.ValidationError({'account':'Invalid account.'})
        if typ == 'transfer':
            if not target or target == account: raise serializers.ValidationError({'transfer_to_account':'Choose a different destination account.'})
            if target.user != self.context['request'].user or target.currency != account.currency: raise serializers.ValidationError({'transfer_to_account':'Transfers require one of your accounts with the same currency.'})
        return data
    def create(self,data): data['user']=self.context['request'].user; return super().create(data)
