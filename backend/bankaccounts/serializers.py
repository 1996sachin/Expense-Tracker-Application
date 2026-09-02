from rest_framework import serializers
from .models import BankAccount
class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount; fields = '__all__'; read_only_fields = ['user','current_balance','created_at']
    def validate_opening_balance(self,v):
        if v < 0 and self.initial_data.get('account_type') != 'credit_card': raise serializers.ValidationError('Only credit accounts may have a negative opening balance.')
        return v
    def create(self, data):
        data['user'] = self.context['request'].user; data['current_balance'] = data.get('opening_balance',0); return super().create(data)
