from django.contrib.auth.models import User
from django.test import TestCase, Client

import base64
import mock
import adal


class AuthTestCase(TestCase):
    client = Client()
    auth_url = '/auth'
    auth_ip_url = '/auth_ip'
    auth_dual_url = '/auth_dual'
    username = 'testu'
    email = 'test.user@test.domain'
    password = 'testpass'

    def setUp(self):
        self.test_user = User.objects.create(username=self.username, email=self.email)

    def basic_auth(self, username, password):
        return 'Basic {}'.format(base64.b64encode('{}:{}'.format(username, password).encode('utf-8')).decode('utf-8'))

    @mock.patch('adal.AuthenticationContext.acquire_token_with_username_password')
    def test_auth_adal_with_username(self, mock_api_call):
        mock_api_call.return_value = {
            'userId': self.email
        }
        # fetch a reponse using basic auth
        response = self.client.get(self.auth_url,
            HTTP_AUTHORIZATION=self.basic_auth(self.username, self.password)
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.json())
        self.assertEqual(response.json()['email'], self.email)

        # fetch again to test auth credential caching
        response = self.client.get(self.auth_url,
            HTTP_AUTHORIZATION=self.basic_auth(self.username, self.password)
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.json())
        self.assertEqual(response.json()['email'], self.email)

        # fetch again to test session credential caching
        response = self.client.get(self.auth_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.json())
        self.assertEqual(response.json()['email'], self.email)

    @mock.patch('adal.AuthenticationContext.acquire_token_with_username_password')
    def test_auth_adal_with_invalid_username(self, mock_api_call):
        mock_api_call.side_effect = adal.adal_error.AdalError('Azure AD disagrees!')
        response = self.client.get(self.auth_url,
            HTTP_AUTHORIZATION=self.basic_auth(self.username, self.password)
        )
        self.assertEqual(response.status_code, 401)

    def test_auth_adal_without_creds(self):
        response = self.client.get(self.auth_url)
        self.assertEqual(response.status_code, 401)

    @mock.patch('adal.AuthenticationContext.acquire_token_with_username_password')
    def test_auth_ip_with_username(self, mock_api_call):
        mock_api_call.return_value = {
            'userId': self.email
        }
        # perform call to auth_ip with full creds
        response = self.client.get(self.auth_ip_url,
            HTTP_AUTHORIZATION=self.basic_auth(self.username, self.password)
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.json())
        self.assertEqual(response.json()['email'], self.email)

    def test_auth_ip_without_creds(self):
        response = self.client.get(self.auth_ip_url)
        self.assertEqual(response.status_code, 200)

    @mock.patch('adal.AuthenticationContext.acquire_token_with_username_password')
    def test_auth_ip_with_session(self, mock_api_call):
        mock_api_call.return_value = {
            'userId': self.email
        }
        # perform call to auth with full creds
        response = self.client.get(self.auth_url,
            HTTP_AUTHORIZATION=self.basic_auth(self.username, self.password)
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.json())
        self.assertEqual(response.json()['email'], self.email)

        # perform call to auth_ip
        response = self.client.get(self.auth_ip_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.json())
        self.assertEqual(response.json()['email'], self.email)

    @mock.patch('adal.AuthenticationContext.acquire_token_with_username_password')
    def test_auth_dual(self, mock_api_call):
        mock_api_call.return_value = {
            'userId': self.email
        }
        # perform call to auth with full creds
        response = self.client.get(self.auth_url,
            HTTP_AUTHORIZATION=self.basic_auth(self.username, self.password)
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.json())
        self.assertEqual(response.json()['email'], self.email)

        # perform call to auth_dual
        response = self.client.get(self.auth_dual_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.json())
        self.assertEqual(response.json()['email'], self.email)



