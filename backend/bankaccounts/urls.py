from rest_framework.routers import DefaultRouter
from .views import BankAccountViewSet
router=DefaultRouter(); router.register('accounts',BankAccountViewSet,basename='account')
urlpatterns=router.urls
