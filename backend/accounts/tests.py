from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import LoginSession

User = get_user_model()


class LoginSessionTests(APITestCase):
    def setUp(self):
        self.password = 'StrongPass123!'
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password=self.password,
            first_name='Test',
            last_name='User',
        )
        self.other_user = User.objects.create_user(
            email='otheruser@example.com',
            username='otheruser',
            password=self.password,
            first_name='Other',
            last_name='User',
        )

    def test_login_creates_login_session(self):
        response = self.client.post(
            '/api/auth/login/',
            {'email': 'testuser@example.com', 'password': self.password},
            format='json',
            HTTP_USER_AGENT='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            REMOTE_ADDR='127.0.0.1',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('session_id', response.data)

        session = LoginSession.objects.filter(user=self.user).first()
        self.assertIsNotNone(session)
        self.assertEqual(session.id, response.data['session_id'])
        self.assertEqual(session.ip_address, '127.0.0.1')
        self.assertEqual(session.location, 'Localhost')
        self.assertIn('Chrome', session.device)
        self.assertIn('macOS', session.device)
        self.assertFalse(session.is_revoked)

    def test_get_sessions_list_and_is_current(self):
        # Perform login to get JWT with session_id claim
        login_res = self.client.post(
            '/api/auth/login/',
            {'email': 'testuser@example.com', 'password': self.password},
            format='json',
            HTTP_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            REMOTE_ADDR='192.168.1.50',
        )
        access_token = login_res.data['access']
        current_session_id = login_res.data['session_id']

        # Create an older session for this user
        old_session = LoginSession.objects.create(
            user=self.user,
            ip_address='10.0.0.1',
            device='Mozilla Firefox on Linux',
            location='Local Network',
        )

        # Create a session for another user
        other_session = LoginSession.objects.create(
            user=self.other_user,
            ip_address='8.8.8.8',
            device='Safari on iOS',
            location='Unknown location',
        )

        # Query session list with Bearer token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('/api/auth/sessions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        session_ids = [s['id'] for s in response.data['results']] if 'results' in response.data else [s['id'] for s in response.data]
        self.assertIn(current_session_id, session_ids)
        self.assertIn(old_session.id, session_ids)
        self.assertNotIn(other_session.id, session_ids)

        items = response.data.get('results', response.data)
        for s in items:
            if s['id'] == current_session_id:
                self.assertTrue(s['is_current'])
            else:
                self.assertFalse(s['is_current'])

    def test_revoke_session(self):
        login_res = self.client.post(
            '/api/auth/login/',
            {'email': 'testuser@example.com', 'password': self.password},
            format='json',
        )
        access_token = login_res.data['access']

        old_session = LoginSession.objects.create(
            user=self.user,
            ip_address='10.0.0.2',
            device='Safari on macOS',
            location='Local Network',
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        del_res = self.client.delete(f'/api/auth/sessions/{old_session.id}/')
        self.assertEqual(del_res.status_code, status.HTTP_200_OK)

        old_session.refresh_from_db()
        self.assertTrue(old_session.is_revoked)

        # It should no longer appear in session list
        list_res = self.client.get('/api/auth/sessions/')
        items = list_res.data.get('results', list_res.data)
        item_ids = [s['id'] for s in items]
        self.assertNotIn(old_session.id, item_ids)

    def test_revoke_other_user_session_returns_404(self):
        login_res = self.client.post(
            '/api/auth/login/',
            {'email': 'testuser@example.com', 'password': self.password},
            format='json',
        )
        access_token = login_res.data['access']

        other_session = LoginSession.objects.create(
            user=self.other_user,
            ip_address='1.2.3.4',
            device='Chrome on Windows',
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        del_res = self.client.delete(f'/api/auth/sessions/{other_session.id}/')
        self.assertEqual(del_res.status_code, status.HTTP_404_NOT_FOUND)
        
        other_session.refresh_from_db()
        self.assertFalse(other_session.is_revoked)

    def test_logout_revokes_current_session(self):
        login_res = self.client.post(
            '/api/auth/login/',
            {'email': 'testuser@example.com', 'password': self.password},
            format='json',
        )
        access_token = login_res.data['access']
        refresh_token = login_res.data['refresh']
        session_id = login_res.data['session_id']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_res = self.client.post('/api/auth/logout/', {'refresh': refresh_token}, format='json')
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)

        session = LoginSession.objects.get(id=session_id)
        self.assertTrue(session.is_revoked)
