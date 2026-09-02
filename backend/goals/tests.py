from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from rest_framework import status
from rest_framework.test import APITestCase
from bankaccounts.models import BankAccount
from .models import Goal

User = get_user_model()


class GoalAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='goals-user@example.com',
            username='goals-user',
            password='testpassword123',
        )
        self.other_user = User.objects.create_user(
            email='other-user@example.com',
            username='other-user',
            password='testpassword123',
        )
        self.account = BankAccount.objects.create(
            user=self.user,
            name='Savings Account',
            account_type=BankAccount.Type.SAVINGS,
            currency='NPR',
            opening_balance=Decimal('50000'),
            current_balance=Decimal('50000'),
        )
        self.other_account = BankAccount.objects.create(
            user=self.other_user,
            name='Other Account',
            account_type=BankAccount.Type.SAVINGS,
            currency='NPR',
            opening_balance=Decimal('10000'),
            current_balance=Decimal('10000'),
        )
        self.client.force_authenticate(user=self.user)

    def test_create_goal(self):
        target_date = (now().date() + timedelta(days=30)).isoformat()
        payload = {
            'name': 'Trip to Pokhara',
            'target_amount': '25000.00',
            'current_amount': '5000.00',
            'target_date': target_date,
            'linked_account': self.account.id,
            'icon': '✈️',
            'color': '#29bb97',
        }
        response = self.client.post('/api/goals/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Trip to Pokhara')
        self.assertEqual(response.data['progress_percent'], 20.0)
        self.assertEqual(Decimal(str(response.data['remaining_amount'])), Decimal('20000.00'))
        self.assertEqual(response.data['days_remaining'], 30)
        self.assertEqual(response.data['status'], 'active')

    def test_cannot_link_other_user_account(self):
        payload = {
            'name': 'Hacked Goal',
            'target_amount': '10000.00',
            'linked_account': self.other_account.id,
        }
        response = self.client.post('/api/goals/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_and_scope(self):
        Goal.objects.create(user=self.user, name='My Goal 1', target_amount=Decimal('10000'), current_amount=Decimal('2000'))
        Goal.objects.create(user=self.other_user, name='Other Goal', target_amount=Decimal('50000'))

        response = self.client.get('/api/goals/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'My Goal 1')

    def test_patch_and_delete_goal(self):
        goal = Goal.objects.create(user=self.user, name='Emergency Fund', target_amount=Decimal('100000'))
        patch_res = self.client.patch(f'/api/goals/{goal.id}/', {'name': 'Updated Emergency Fund'}, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.name, 'Updated Emergency Fund')

        del_res = self.client.delete(f'/api/goals/{goal.id}/')
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Goal.objects.filter(id=goal.id).exists())

    def test_other_user_goal_unauthorized(self):
        other_goal = Goal.objects.create(user=self.other_user, name='Secret Goal', target_amount=Decimal('50000'))
        response = self.client.get(f'/api/goals/{other_goal.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_funds_action(self):
        goal = Goal.objects.create(
            user=self.user,
            name='New Laptop',
            target_amount=Decimal('100000'),
            current_amount=Decimal('90000'),
            status=Goal.Status.ACTIVE,
        )
        response = self.client.post(f'/api/goals/{goal.id}/add-funds/', {'amount': '15000'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.current_amount, Decimal('105000'))
        self.assertEqual(goal.status, Goal.Status.COMPLETED)
        self.assertEqual(response.data['progress_percent'], 105.0)
        self.assertEqual(Decimal(str(response.data['remaining_amount'])), Decimal('0'))

    def test_ordering(self):
        today = now().date()
        Goal.objects.create(user=self.user, name='B Goal', target_amount=Decimal('3000'), current_amount=Decimal('1500'), target_date=today + timedelta(days=10)) # 50%
        Goal.objects.create(user=self.user, name='A Goal', target_amount=Decimal('1000'), current_amount=Decimal('800'), target_date=today + timedelta(days=5))   # 80%
        Goal.objects.create(user=self.user, name='C Goal', target_amount=Decimal('5000'), current_amount=Decimal('1000'), target_date=today + timedelta(days=20)) # 20%

        # Sort by name
        res = self.client.get('/api/goals/?ordering=name')
        names = [x['name'] for x in res.data['results']]
        self.assertEqual(names, ['A Goal', 'B Goal', 'C Goal'])

        # Sort by target_amount
        res = self.client.get('/api/goals/?ordering=target_amount')
        amounts = [float(x['target_amount']) for x in res.data['results']]
        self.assertEqual(amounts, [1000.0, 3000.0, 5000.0])

        # Sort by progress_percent
        res = self.client.get('/api/goals/?ordering=progress_percent')
        pcts = [x['progress_percent'] for x in res.data['results']]
        self.assertEqual(pcts, [20.0, 50.0, 80.0])

        # Sort by target_date
        res = self.client.get('/api/goals/?ordering=target_date')
        dates_names = [x['name'] for x in res.data['results']]
        self.assertEqual(dates_names, ['A Goal', 'B Goal', 'C Goal'])
