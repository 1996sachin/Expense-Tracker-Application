from rest_framework import serializers
from .models import Transaction, RecurringTransaction
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


class RecurringTransactionSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    category_color = serializers.CharField(source='category.color', read_only=True, allow_null=True)

    class Meta:
        model = RecurringTransaction
        fields = [
            'id',
            'account',
            'account_name',
            'category',
            'category_name',
            'category_color',
            'amount',
            'type',
            'frequency',
            'start_date',
            'end_date',
            'next_run_date',
            'note',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'account_name', 'category_name', 'category_color']
        extra_kwargs = {
            'next_run_date': {'required': False},
        }

    def validate(self, data):
        request = self.context.get('request')
        user = request.user if request else None

        amount = data.get('amount', getattr(self.instance, 'amount', None))
        if amount is not None and amount <= 0:
            raise serializers.ValidationError({'amount': 'Amount must be positive.'})

        account = data.get('account', getattr(self.instance, 'account', None))
        if account and user and account.user != user:
            raise serializers.ValidationError({'account': 'Invalid account.'})

        category = data.get('category', getattr(self.instance, 'category', None))
        if category and user and category.user and category.user != user:
            raise serializers.ValidationError({'category': 'Invalid category.'})

        start_date = data.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = data.get('end_date', getattr(self.instance, 'end_date', None))
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({'end_date': 'End date cannot be before start date.'})

        if not data.get('next_run_date') and not getattr(self.instance, 'next_run_date', None):
            if start_date:
                data['next_run_date'] = start_date

        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        if not validated_data.get('next_run_date'):
            validated_data['next_run_date'] = validated_data.get('start_date')
        return super().create(validated_data)
