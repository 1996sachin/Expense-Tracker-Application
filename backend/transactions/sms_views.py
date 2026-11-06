from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import CategorizationRule
from .serializers import CategorizationRuleSerializer
from .authentication import SMSApiKeyAuthentication, IsInsertOnly
from .sms_service import process_incoming_sms
from .sms_parser import parse_sms
from .categorizer import resolve_category_for_sms


class SMSIngestView(APIView):
    """
    Dedicated endpoint for iOS Shortcuts and Android SMS automations.
    - Security: Authenticates via persistent SMS Ingest Key ('X-Pocketly-Key' or JWT).
    - Insert-Only: Enforces POST-only permission. Cannot read, list, update, or delete data.
    - Idempotent: Automatic deduplication using transaction reference ID (TrxID).
    """
    authentication_classes = [SMSApiKeyAuthentication, JWTAuthentication]
    permission_classes = [IsInsertOnly]

    def post(self, request, *args, **kwargs):
        # Extract body from JSON, form-data, or raw text
        sms_text = ''
        sender = ''

        if isinstance(request.data, dict):
            sms_text = (
                request.data.get('body')
                or request.data.get('message')
                or request.data.get('sms')
                or request.data.get('text')
                or ''
            )
            sender = request.data.get('sender') or request.data.get('from') or ''
        elif isinstance(request.data, str):
            sms_text = request.data

        # Fallback to raw request body
        if not sms_text and request.body:
            try:
                sms_text = request.body.decode('utf-8')
            except Exception:
                pass

        if not sender and 'HTTP_X_SENDER' in request.META:
            sender = request.META['HTTP_X_SENDER']

        if not sms_text:
            return Response(
                {'status': 'error', 'message': 'No SMS text provided in request body.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = process_incoming_sms(request.user, sms_text=sms_text, sender=sender)

        # Return 200 even for duplicate/ignored so automated phone shortcuts don't error out
        return Response(result, status=status.HTTP_200_OK)


class SMSTestParseView(APIView):
    """
    Preview and test SMS parsing without writing to the database.
    Useful for testing how various bank and eSewa SMS strings will be extracted and categorized.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        sms_text = request.data.get('body') or request.data.get('message') or request.data.get('sms') or ''
        sender = request.data.get('sender') or ''

        if not sms_text:
            return Response({'error': 'Please provide "body" with SMS text to test.'}, status=400)

        parsed = parse_sms(sms_text, sender)
        if not parsed.get('is_transaction'):
            return Response({
                'is_transaction': False,
                'reason': parsed.get('reason', 'Not recognized as a financial transaction.'),
                'parsed': parsed
            })

        predicted_category = resolve_category_for_sms(
            user=request.user,
            merchant=parsed.get('merchant', ''),
            raw_sms=sms_text,
            tx_type=parsed.get('type', 'expense')
        )

        return Response({
            'is_transaction': True,
            'parsed': {
                'type': parsed['type'],
                'amount': float(parsed['amount']),
                'currency': parsed['currency'],
                'merchant': parsed['merchant'],
                'reference_id': parsed['reference_id'],
                'balance': float(parsed['balance']) if parsed['balance'] is not None else None,
                'account_hint': parsed['account_hint'],
                'bank_name': parsed['bank_name'],
                'date': str(parsed['date'])
            },
            'predicted_category': {
                'id': predicted_category.id if predicted_category else None,
                'name': predicted_category.name if predicted_category else 'Uncategorized',
                'color': predicted_category.color if predicted_category else '#94a3b8'
            }
        })


class CategorizationRuleViewSet(viewsets.ModelViewSet):
    """
    Allows user to manage custom merchant-to-category rules:
    - E.g. 'Foodmandu, Bhoj' -> 'Food'
    - 'Pathao' -> 'Transport'
    """
    serializer_class = CategorizationRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CategorizationRule.objects.filter(user=self.request.user).select_related('category')
