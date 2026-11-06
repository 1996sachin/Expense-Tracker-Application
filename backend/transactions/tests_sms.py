from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from bankaccounts.models import BankAccount
from categories.models import Category
from .models import Transaction, CategorizationRule
from .sms_parser import parse_sms

User = get_user_model()


class SMSParserTests(TestCase):
    def test_esewa_debit_sms(self):
        sms = "Your eSewa ID has been debited for NPR 500.00 on 2026-09-28 for payment to Foodmandu. Trx ID: 12345ABC. Available Balance: NPR 1250.00"
        res = parse_sms(sms, 'eSewa')
        self.assertTrue(res['is_transaction'])
        self.assertEqual(res['type'], 'expense')
        self.assertEqual(res['amount'], Decimal('500.00'))
        self.assertEqual(res['currency'], 'NPR')
        self.assertEqual(res['merchant'], 'Foodmandu')
        self.assertEqual(res['reference_id'], '12345ABC')
        self.assertEqual(res['balance'], Decimal('1250.00'))
        self.assertEqual(res['account_hint'], 'eSewa')

    def test_mobile_banking_fonepay_sms(self):
        sms = "Dear Customer, your a/c ...1234 has been debited by NPR 850.00 on 2026-09-28 for POS/QR purchase at Bhatbhateni. Ref/Txn: FP123987. Avl Bal: NPR 25,400.00"
        res = parse_sms(sms, 'Nabil')
        self.assertTrue(res['is_transaction'])
        self.assertEqual(res['type'], 'expense')
        self.assertEqual(res['amount'], Decimal('850.00'))
        self.assertEqual(res['merchant'], 'Bhatbhateni')
        self.assertEqual(res['reference_id'], 'FP123987')
        self.assertEqual(res['balance'], Decimal('25400.00'))
        self.assertEqual(res['account_hint'], '1234')

    def test_salary_credit_sms(self):
        sms = "A/C ...4321 Credited with NPR 50,000.00 on 2026-09-28 by Salary. Avl Bal: NPR 65,000.00. Ref: 112233"
        res = parse_sms(sms, 'GlobalIME')
        self.assertTrue(res['is_transaction'])
        self.assertEqual(res['type'], 'income')
        self.assertEqual(res['amount'], Decimal('50000.00'))
        self.assertEqual(res['merchant'], 'Salary')
        self.assertEqual(res['reference_id'], '112233')

    def test_otp_ignored(self):
        sms = "Your eSewa verification code is 492019. Do not share this code with anyone."
        res = parse_sms(sms, 'eSewa')
        self.assertFalse(res['is_transaction'])


class SMSWebhookIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='Password123!'
        )
        self.api_key = self.user.get_or_create_sms_api_key()
        self.client = APIClient()

    def test_esewa_ingest_and_deduplication(self):
        url = '/api/transactions/sms-ingest/'
        headers = {'HTTP_X_POCKETLY_KEY': self.api_key}
        payload = {
            'body': 'Your eSewa ID has been debited for NPR 500.00 on 2026-09-28 for payment to Foodmandu. Trx ID: 12345ABC. Available Balance: NPR 1250.00',
            'sender': 'eSewa'
        }

        # 1. First trigger -> success
        resp1 = self.client.post(url, payload, format='json', **headers)
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.json()
        self.assertEqual(data1['status'], 'success')
        self.assertEqual(data1['transaction']['merchant'], 'Foodmandu')
        self.assertEqual(data1['transaction']['category'], 'Food & Dining')
        self.assertEqual(data1['transaction']['reference_id'], '12345ABC')
        self.assertEqual(data1['transaction']['account'], 'eSewa')

        # Check DB
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 1)
        account = BankAccount.objects.get(user=self.user, name='eSewa')
        self.assertEqual(account.current_balance, Decimal('1250.00'))

        # 2. Duplicate trigger (same TrxID from multi-keyword automation)
        resp2 = self.client.post(url, payload, format='json', **headers)
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertEqual(data2['status'], 'duplicate')
        # Check no second transaction was created
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 1)

    def test_least_privilege_insert_only(self):
        url = '/api/transactions/sms-ingest/'
        headers = {'HTTP_X_POCKETLY_KEY': self.api_key}

        # GET is rejected with 403 Forbidden
        resp_get = self.client.get(url, **headers)
        self.assertEqual(resp_get.status_code, 403)

        # DELETE is rejected with 403 Forbidden
        resp_delete = self.client.delete(url, **headers)
        self.assertEqual(resp_delete.status_code, 403)

    def test_custom_rule_override(self):
        # Create a custom category and rule
        custom_cat = Category.objects.create(user=self.user, name='Tea & Hangouts', type='expense')
        CategorizationRule.objects.create(
            user=self.user,
            category=custom_cat,
            keywords='Khaja Ghar, Chiya, Tea Corner',
            priority=1
        )

        url = '/api/transactions/sms-ingest/'
        headers = {'HTTP_X_POCKETLY_KEY': self.api_key}
        payload = {
            'body': 'Ac ...9876 debited by Rs 250.00 on 2026-09-28 towards Fonepay/Khaja Ghar. TrxId: 981247. Bal: Rs 15200.00',
            'sender': 'Nabil'
        }

        resp = self.client.post(url, payload, format='json', **headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['transaction']['category'], 'Tea & Hangouts')

    def test_sms_token_endpoint(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get('/api/auth/sms-token/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['sms_api_key'], self.api_key)
        self.assertIn('/api/transactions/sms-ingest/', data['webhook_url'])

        # Regenerate
        resp_regen = self.client.post('/api/auth/sms-token/regenerate/')
        self.assertEqual(resp_regen.status_code, 200)
        new_key = resp_regen.json()['sms_api_key']
        self.assertNotEqual(new_key, self.api_key)
