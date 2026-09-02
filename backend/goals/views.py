from decimal import Decimal, InvalidOperation
from django.db.models import Case, ExpressionWrapper, F, FloatField, Value, When
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Goal
from .serializers import GoalSerializer


class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    filterset_fields = ['status', 'linked_account']
    search_fields = ['name']
    ordering_fields = [
        'name',
        'target_amount',
        'current_amount',
        'target_date',
        'created_at',
        'progress_percent',
    ]

    def get_queryset(self):
        return (
            Goal.objects.filter(user=self.request.user)
            .select_related('linked_account')
            .annotate(
                progress_percent=Case(
                    When(
                        target_amount__gt=0,
                        then=ExpressionWrapper(
                            F('current_amount') * 100.0 / F('target_amount'),
                            output_field=FloatField(),
                        ),
                    ),
                    default=Value(0.0),
                    output_field=FloatField(),
                )
            )
        )

    @action(detail=True, methods=['post'], url_path='add-funds')
    def add_funds(self, request, pk=None):
        goal = self.get_object()
        raw_amount = request.data.get('amount')
        if raw_amount is None:
            return Response({'amount': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(str(raw_amount))
        except (ValueError, TypeError, InvalidOperation):
            return Response({'amount': ['Valid positive amount is required.']}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({'amount': ['Amount must be greater than 0.']}, status=status.HTTP_400_BAD_REQUEST)

        goal.current_amount += amount
        if goal.current_amount >= goal.target_amount and goal.status == Goal.Status.ACTIVE:
            goal.status = Goal.Status.COMPLETED
        goal.save()

        serializer = self.get_serializer(goal)
        return Response(serializer.data, status=status.HTTP_200_OK)
