from decimal import Decimal
from django.utils.timezone import now
from rest_framework import serializers
from .models import Goal


class GoalSerializer(serializers.ModelSerializer):
    progress_percent = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    linked_account_name = serializers.CharField(source='linked_account.name', read_only=True)

    class Meta:
        model = Goal
        fields = [
            'id',
            'name',
            'target_amount',
            'current_amount',
            'target_date',
            'linked_account',
            'linked_account_name',
            'icon',
            'color',
            'status',
            'created_at',
            'progress_percent',
            'remaining_amount',
            'days_remaining',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'progress_percent',
            'remaining_amount',
            'days_remaining',
            'linked_account_name',
        ]

    def get_progress_percent(self, obj):
        if not obj.target_amount or obj.target_amount <= 0:
            return 0.0
        pct = (Decimal(str(obj.current_amount)) / Decimal(str(obj.target_amount))) * Decimal('100')
        return round(float(pct), 2)

    def get_remaining_amount(self, obj):
        target = Decimal(str(obj.target_amount or 0))
        current = Decimal(str(obj.current_amount or 0))
        remaining = target - current
        return max(Decimal('0'), remaining)

    def get_days_remaining(self, obj):
        if not obj.target_date:
            return None
        today = now().date()
        diff = (obj.target_date - today).days
        return diff

    def validate(self, data):
        request = self.context.get('request')
        target_amount = data.get('target_amount', getattr(self.instance, 'target_amount', None))
        current_amount = data.get('current_amount', getattr(self.instance, 'current_amount', Decimal('0')))
        linked_account = data.get('linked_account', getattr(self.instance, 'linked_account', None))

        if target_amount is not None and target_amount <= 0:
            raise serializers.ValidationError({'target_amount': 'Target amount must be greater than 0.'})

        if current_amount is not None and current_amount < 0:
            raise serializers.ValidationError({'current_amount': 'Current amount cannot be negative.'})

        if linked_account and request and linked_account.user != request.user:
            raise serializers.ValidationError({'linked_account': 'Invalid account.'})

        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
