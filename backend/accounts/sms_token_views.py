from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class SMSTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        token = user.get_or_create_sms_api_key()
        webhook_url = request.build_absolute_uri('/api/transactions/sms-ingest/')
        return Response({
            'sms_api_key': token,
            'webhook_url': webhook_url,
            'curl_example': f'curl -X POST "{webhook_url}" -H "X-Pocketly-Key: {token}" -H "Content-Type: application/json" -d \'{{"body": "Your eSewa ID has been debited for NPR 500 for Foodmandu. Trx ID: 123", "sender": "eSewa"}}\'',
            'ios_instructions': {
                'trigger': 'When I get a message containing: debited, credited, eSewa, NPR, Rs',
                'action': 'Get Contents of URL',
                'method': 'POST',
                'headers': {
                    'X-Pocketly-Key': token,
                    'Content-Type': 'application/json'
                },
                'request_body': {
                    'body': 'Shortcut Input',
                    'sender': 'Sender'
                }
            }
        })


class SMSTokenRegenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        new_token = user.rotate_sms_api_key()
        webhook_url = request.build_absolute_uri('/api/transactions/sms-ingest/')
        return Response({
            'status': 'success',
            'message': 'New SMS API key generated successfully.',
            'sms_api_key': new_token,
            'webhook_url': webhook_url
        })
