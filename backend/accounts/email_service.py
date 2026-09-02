import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def _send(template, subject, user, **context):
        context.update(username=user.get_full_name() or user.username, email=user.email, frontend_url=settings.FRONTEND_URL)
        html = render_to_string(f'emails/{template}.html', context)
        message = EmailMultiAlternatives(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email])
        message.attach_alternative(html, 'text/html')
        message.send(fail_silently=False)
    @classmethod
    def send_welcome_email(cls, user): cls._send('welcome', 'Welcome to Pocketly! 🎉', user)
    @classmethod
    def send_password_reset_email(cls, user, reset_url): cls._send('password_reset', 'Reset your Pocketly password', user, reset_url=reset_url, timeout=settings.PASSWORD_RESET_TIMEOUT_MINUTES)
    @classmethod
    def send_login_notification(cls, user, login_time, ip_address): cls._send('login_notification', 'New sign-in to your Pocketly account', user, login_time=login_time, ip_address=ip_address)
    @classmethod
    def send_email_otp(cls, user, code): cls._send('email_otp', 'Your Pocketly verification code', user, code=code)
    @classmethod
    def send_test_email(cls, user): cls._send('test_email', 'Pocketly email configuration test', user)
    @classmethod
    def safe_send(cls, method, *args, **kwargs):
        try: getattr(cls, method)(*args, **kwargs)
        except Exception: logger.exception('Authentication email delivery failed.')
