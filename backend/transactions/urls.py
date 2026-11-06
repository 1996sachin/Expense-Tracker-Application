from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet
from .sms_views import SMSIngestView, SMSTestParseView, CategorizationRuleViewSet

router = DefaultRouter()
router.register('transactions', TransactionViewSet, basename='transaction')
router.register('rules', CategorizationRuleViewSet, basename='rule')

urlpatterns = [
    path('transactions/sms-ingest/', SMSIngestView.as_view(), name='sms-ingest'),
    path('transactions/sms-test/', SMSTestParseView.as_view(), name='sms-test'),
] + router.urls
