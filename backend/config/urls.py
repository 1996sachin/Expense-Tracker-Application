from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
urlpatterns = [path('admin/',admin.site.urls),path('api/auth/',include('accounts.urls')),path('api/',include('bankaccounts.urls')),path('api/',include('categories.urls')),path('api/',include('transactions.urls')),path('api/',include('budgets.urls')),path('api/schema/',SpectacularAPIView.as_view()),path('api/docs/',SpectacularSwaggerView.as_view(url_name='schema'))] + static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
