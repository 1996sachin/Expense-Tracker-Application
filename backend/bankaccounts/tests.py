from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import BankAccount

User = get_user_model()


class BankAccountUpdateTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='accounts-test@example.com',
            username='accounts-test',
            password='testpass123',
        )
        self.other = User.objects.create_user(
            email='other@example.com',
            username='other',
            password='testpass123',
        )
        self.account = BankAccount.objects.create(
            user=self.user,
            name='Cash Wallet',
            bank_name='',
            account_type=BankAccount.Type.CASH,
            currency='NPR',
            opening_balance=Decimal('1000'),
            current_balance=Decimal('1000'),
        )
        self.client.force_authenticate(user=self.user)

    def test_patch_updates_own_account(self):
        response = self.client.patch(
            f'/api/accounts/{self.account.id}/',
            {'name': 'Savings', 'bank_name': 'Nabil Bank'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.account.refresh_from_db()
        self.assertEqual(self.account.name, 'Savings')
        self.assertEqual(self.account.bank_name, 'Nabil Bank')
        self.assertEqual(self.account.current_balance, Decimal('1000'))

    def test_patch_other_users_account_returns_404(self):
        other_account = BankAccount.objects.create(
            user=self.other,
            name='Other',
            account_type=BankAccount.Type.CHECKING,
            currency='NPR',
        )

        response = self.client.patch(
            f'/api/accounts/{other_account.id}/',
            {'name': 'Hacked'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
