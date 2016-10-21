from django.contrib.auth.models import User
from organisation.models import DepartmentUser
from django.test import TestCase, Client

from core import views

import base64
import mock
import adal


class AuthTestCase(TestCase):
    client = Client()
    auth_url = '/auth'
    auth_ip_url = '/auth_ip'
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
        response = self.client.get(self.auth_url, 
            HTTP_AUTHORIZATION=self.basic_auth(self.username, self.password)
        )
        self.assertEqual(response.status_code, 200)
        
    @mock.patch('adal.AuthenticationContext.acquire_token_with_username_password')
    def test_auth_adal_with_invalid_username(self, mock_api_call):
        mock_api_call.side_effect = adal.adal_error.AdalError
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


