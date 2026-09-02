from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet, RecurringTransactionViewSet

router = DefaultRouter()
router.register('transactions', TransactionViewSet, basename='transaction')
router.register('recurring-transactions', RecurringTransactionViewSet, basename='recurring-transaction')
router.register('recurring', RecurringTransactionViewSet, basename='recurring')
urlpatterns = router.urls
