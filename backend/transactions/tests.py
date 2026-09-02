from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from rest_framework import status
from rest_framework.test import APITestCase
from bankaccounts.models import BankAccount
from categories.models import Category
from .models import Transaction, RecurringTransaction
from .tasks import advance_date, generate_recurring_transactions

User = get_user_model()


class RecurringTransactionAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='recurring-user@example.com',
            username='recurring-user',
            password='testpassword123',
        )
        self.other_user = User.objects.create_user(
            email='other-rec@example.com',
            username='other-rec',
            password='testpassword123',
        )
        self.account = BankAccount.objects.create(
            user=self.user,
            name='Checking Account',
            account_type=BankAccount.Type.CHECKING,
            currency='NPR',
            opening_balance=Decimal('20000'),
            current_balance=Decimal('20000'),
        )
        self.other_account = BankAccount.objects.create(
            user=self.other_user,
            name='Other Checking',
            account_type=BankAccount.Type.CHECKING,
            currency='NPR',
            opening_balance=Decimal('10000'),
            current_balance=Decimal('10000'),
        )
        self.category = Category.objects.create(
            user=self.user,
            name='Subscriptions',
            type='expense',
            color='#ec6e89',
        )
        self.client.force_authenticate(user=self.user)

    def test_create_recurring_transaction(self):
        payload = {
            'account': self.account.id,
            'category': self.category.id,
            'amount': '1500.00',
            'type': 'expense',
            'frequency': 'monthly',
            'start_date': '2026-09-01',
            'note': 'Netflix Subscription',
        }
        response = self.client.post('/api/recurring-transactions/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['note'], 'Netflix Subscription')
        self.assertEqual(response.data['frequency'], 'monthly')
        self.assertEqual(response.data['next_run_date'], '2026-09-01')
        self.assertTrue(response.data['is_active'])
        self.assertEqual(response.data['account_name'], 'Checking Account')
        self.assertEqual(response.data['category_name'], 'Subscriptions')

    def test_cannot_use_other_user_account(self):
        payload = {
            'account': self.other_account.id,
            'amount': '500.00',
            'type': 'expense',
            'frequency': 'daily',
            'start_date': '2026-09-01',
        }
        response = self.client.post('/api/recurring-transactions/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_and_user_scoping(self):
        RecurringTransaction.objects.create(
            user=self.user,
            account=self.account,
            amount=Decimal('100'),
            type='expense',
            frequency='daily',
            start_date=date(2026, 9, 1),
            next_run_date=date(2026, 9, 1),
            note='My Recurring',
        )
        RecurringTransaction.objects.create(
            user=self.other_user,
            account=self.other_account,
            amount=Decimal('500'),
            type='expense',
            frequency='daily',
            start_date=date(2026, 9, 1),
            next_run_date=date(2026, 9, 1),
            note='Other Recurring',
        )

        response = self.client.get('/api/recurring-transactions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['note'], 'My Recurring')

    def test_toggle_active_action_and_patch(self):
        rec = RecurringTransaction.objects.create(
            user=self.user,
            account=self.account,
            amount=Decimal('100'),
            type='expense',
            frequency='daily',
            start_date=date(2026, 9, 1),
            next_run_date=date(2026, 9, 1),
            is_active=True,
        )
        # Toggle action
        res = self.client.post(f'/api/recurring-transactions/{rec.id}/toggle/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['is_active'])

        # Patch is_active
        res = self.client.patch(f'/api/recurring-transactions/{rec.id}/', {'is_active': True}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['is_active'])

    def test_ordering(self):
        cat_b = Category.objects.create(user=self.user, name='Utilities', type='expense')
        RecurringTransaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category, # Subscriptions
            amount=Decimal('300'),
            type='expense',
            frequency='weekly',
            start_date=date(2026, 9, 1),
            next_run_date=date(2026, 9, 10),
            note='Item 3',
        )
        RecurringTransaction.objects.create(
            user=self.user,
            account=self.account,
            category=cat_b, # Utilities
            amount=Decimal('100'),
            type='expense',
            frequency='daily',
            start_date=date(2026, 9, 1),
            next_run_date=date(2026, 9, 5),
            note='Item 1',
        )
        RecurringTransaction.objects.create(
            user=self.user,
            account=self.account,
            amount=Decimal('500'),
            type='expense',
            frequency='monthly',
            start_date=date(2026, 9, 1),
            next_run_date=date(2026, 9, 15),
            note='Item 2',
        )

        # Ordering by amount
        res = self.client.get('/api/recurring-transactions/?ordering=amount')
        amounts = [float(x['amount']) for x in res.data['results']]
        self.assertEqual(amounts, [100.0, 300.0, 500.0])

        # Ordering by next_run_date
        res = self.client.get('/api/recurring-transactions/?ordering=next_run_date')
        dates = [x['next_run_date'] for x in res.data['results']]
        self.assertEqual(dates, ['2026-09-05', '2026-09-10', '2026-09-15'])

        # Ordering by frequency
        res = self.client.get('/api/recurring-transactions/?ordering=frequency')
        freqs = [x['frequency'] for x in res.data['results']]
        self.assertEqual(freqs, ['daily', 'monthly', 'weekly'])


class RecurringCeleryTaskTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='task-user@example.com',
            username='task-user',
            password='testpassword123',
        )
        self.account = BankAccount.objects.create(
            user=self.user,
            name='Main Wallet',
            account_type=BankAccount.Type.WALLET,
            currency='NPR',
            opening_balance=Decimal('10000'),
            current_balance=Decimal('10000'),
        )
        self.category = Category.objects.create(
            user=self.user,
            name='Gym',
            type='expense',
        )

    def test_advance_date_logic(self):
        self.assertEqual(advance_date(date(2026, 1, 15), 'daily'), date(2026, 1, 16))
        self.assertEqual(advance_date(date(2026, 1, 15), 'weekly'), date(2026, 1, 22))
        self.assertEqual(advance_date(date(2026, 1, 31), 'monthly'), date(2026, 2, 28))
        self.assertEqual(advance_date(date(2024, 2, 29), 'yearly'), date(2025, 2, 28))

    def test_generate_recurring_transactions_execution(self):
        today = now().date()
        # Due daily recurring transaction
        rec_due = RecurringTransaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category,
            amount=Decimal('500'),
            type='expense',
            frequency='daily',
            start_date=today - timedelta(days=1),
            next_run_date=today,
            note='Gym Daily',
            is_active=True,
        )

        # Future recurring transaction (not due)
        rec_future = RecurringTransaction.objects.create(
            user=self.user,
            account=self.account,
            amount=Decimal('1000'),
            type='income',
            frequency='monthly',
            start_date=today + timedelta(days=5),
            next_run_date=today + timedelta(days=5),
            note='Future Salary',
            is_active=True,
        )

        # Inactive recurring transaction
        rec_inactive = RecurringTransaction.objects.create(
            user=self.user,
            account=self.account,
            amount=Decimal('200'),
            type='expense',
            frequency='daily',
            start_date=today,
            next_run_date=today,
            is_active=False,
        )

        initial_balance = self.account.current_balance
        count = generate_recurring_transactions()
        self.assertEqual(count, 1)

        # Verify real transaction was created
        created_tx = Transaction.objects.filter(note='Gym Daily').first()
        self.assertIsNotNone(created_tx)
        self.assertEqual(created_tx.amount, Decimal('500.00'))
        self.assertEqual(created_tx.type, 'expense')
        self.assertEqual(created_tx.date, today)

        # Verify balance updated (-500)
        self.account.refresh_from_db()
        self.assertEqual(self.account.current_balance, initial_balance - Decimal('500.00'))

        # Verify next_run_date advanced
        rec_due.refresh_from_db()
        self.assertEqual(rec_due.next_run_date, today + timedelta(days=1))

    def test_recurring_transaction_with_end_date_deactivates(self):
        today = now().date()
        rec = RecurringTransaction.objects.create(
            user=self.user,
            account=self.account,
            amount=Decimal('300'),
            type='expense',
            frequency='daily',
            start_date=today,
            next_run_date=today,
            end_date=today,
            is_active=True,
        )

        count = generate_recurring_transactions()
        self.assertEqual(count, 1)
        rec.refresh_from_db()
        self.assertEqual(rec.next_run_date, today + timedelta(days=1))
        self.assertFalse(rec.is_active)
