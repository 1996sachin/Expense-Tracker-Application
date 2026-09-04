import os
from pathlib import Path
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / '.env')
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'development-only-key')
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = ['*']
INSTALLED_APPS = ['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','corsheaders','rest_framework','rest_framework_simplejwt','django_filters','drf_spectacular','accounts.apps.AccountsConfig','bankaccounts','categories','transactions.apps.TransactionsConfig','budgets','notifications','goals']
MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware','django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR / 'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {'ENGINE':'django.db.backends.mysql','NAME':os.getenv('MYSQL_DATABASE','expense_tracker'),'USER':os.getenv('MYSQL_USER','expense_user'),'PASSWORD':os.getenv('MYSQL_PASSWORD','expense_password'),'HOST':os.getenv('MYSQL_HOST','localhost'),'PORT':os.getenv('MYSQL_PORT','3306'),'OPTIONS':{'charset':'utf8mb4'}}}
AUTH_USER_MODEL = 'accounts.User'
DEFAULT_CURRENCY = os.getenv('DEFAULT_CURRENCY', 'NPR').upper()
REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework_simplejwt.authentication.JWTAuthentication'], 'DEFAULT_PERMISSION_CLASSES':['rest_framework.permissions.IsAuthenticated'], 'DEFAULT_SCHEMA_CLASS':'drf_spectacular.openapi.AutoSchema','DEFAULT_FILTER_BACKENDS':['django_filters.rest_framework.DjangoFilterBackend','rest_framework.filters.SearchFilter','rest_framework.filters.OrderingFilter'],'DEFAULT_PAGINATION_CLASS':'rest_framework.pagination.PageNumberPagination','PAGE_SIZE':25}
SPECTACULAR_SETTINGS = {'TITLE':'Expense Tracker API','VERSION':'1.0.0'}
CORS_ALLOWED_ORIGINS = [os.getenv('FRONTEND_ORIGIN','http://localhost:5173')]
CORS_ALLOWED_ORIGIN_REGEXES = [r'^https?://(localhost|127\.0\.0\.1)(:\d+)?$']
STATIC_URL = 'static/'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CELERY_BROKER_URL = os.getenv('REDIS_URL','redis://localhost:6379/0')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_BEAT_SCHEDULE = {'recurring-transactions': {'task':'transactions.tasks.generate_recurring_transactions','schedule': 86400}}
CACHES = {'default': {'BACKEND':'django.core.cache.backends.redis.RedisCache','LOCATION':CELERY_BROKER_URL}}
FRONTEND_URL = os.getenv('FRONTEND_ORIGIN', 'http://localhost:5173')
PASSWORD_RESET_TIMEOUT_MINUTES = int(os.getenv('PASSWORD_RESET_TIMEOUT_MINUTES', '30'))
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.locmem.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Pocketly <noreply@pocketly.local>')
SMTP_HOST = os.getenv('SMTP_HOST', EMAIL_HOST)
SMTP_PORT = int(os.getenv('SMTP_PORT', str(EMAIL_PORT)))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', EMAIL_HOST_USER)
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', EMAIL_HOST_PASSWORD)
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', str(EMAIL_USE_TLS)).lower() == 'true'
EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_USE_TLS = SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_USE_TLS
EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'Pocketly')
EMAIL_FROM_ADDRESS = os.getenv('EMAIL_FROM_ADDRESS', '')
if EMAIL_FROM_ADDRESS: DEFAULT_FROM_EMAIL = f'{EMAIL_FROM_NAME} <{EMAIL_FROM_ADDRESS}>'
SEND_LOGIN_NOTIFICATION_EMAIL = os.getenv('SEND_LOGIN_NOTIFICATION_EMAIL', 'false').lower() == 'true'
MFA_CHALLENGE_TIMEOUT_MINUTES = int(os.getenv('MFA_CHALLENGE_TIMEOUT_MINUTES', '5'))
MFA_ENCRYPTION_KEY = os.getenv('MFA_ENCRYPTION_KEY', '')
