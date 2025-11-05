import unittest

from flask import json

from swagger_server.models.auth_change_password_post_request import AuthChangePasswordPostRequest  # noqa: E501
from swagger_server.models.auth_logout_post_request import AuthLogoutPostRequest  # noqa: E501
from swagger_server.models.auth_me_get200_response import AuthMeGet200Response  # noqa: E501
from swagger_server.models.auth_refresh_post200_response import AuthRefreshPost200Response  # noqa: E501
from swagger_server.models.auth_refresh_post_request import AuthRefreshPostRequest  # noqa: E501
from swagger_server.models.auth_register_post_request import AuthRegisterPostRequest  # noqa: E501
from swagger_server.models.error import Error  # noqa: E501
from swagger_server.models.login_request import LoginRequest  # noqa: E501
from swagger_server.models.login_response import LoginResponse  # noqa: E501
from swagger_server.test import BaseTestCase


class TestAuthenticationController(BaseTestCase):
    """AuthenticationController integration test stubs"""

    def test_auth_change_password_post(self):
        """Test case for auth_change_password_post

        Change password
        """
        auth_change_password_post_request = swagger_server.AuthChangePasswordPostRequest()
        headers = { 
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/auth/change-password',
            method='POST',
            headers=headers,
            data=json.dumps(auth_change_password_post_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_auth_login_post(self):
        """Test case for auth_login_post

        User login
        """
        login_request = {"password":"user123","username":"user1"}
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/auth/login',
            method='POST',
            headers=headers,
            data=json.dumps(login_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_auth_logout_post(self):
        """Test case for auth_logout_post

        Logout user
        """
        auth_logout_post_request = swagger_server.AuthLogoutPostRequest()
        headers = { 
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/auth/logout',
            method='POST',
            headers=headers,
            data=json.dumps(auth_logout_post_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_auth_me_get(self):
        """Test case for auth_me_get

        Get current user profile
        """
        headers = { 
            'Accept': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/auth/me',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_auth_refresh_post(self):
        """Test case for auth_refresh_post

        Refresh access token
        """
        auth_refresh_post_request = swagger_server.AuthRefreshPostRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/auth/refresh',
            method='POST',
            headers=headers,
            data=json.dumps(auth_refresh_post_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_auth_register_post(self):
        """Test case for auth_register_post

        Register new user
        """
        auth_register_post_request = swagger_server.AuthRegisterPostRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/auth/register',
            method='POST',
            headers=headers,
            data=json.dumps(auth_register_post_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
