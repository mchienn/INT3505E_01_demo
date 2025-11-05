import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from swagger_server.models.auth_change_password_post_request import AuthChangePasswordPostRequest  # noqa: E501
from swagger_server.models.auth_logout_post_request import AuthLogoutPostRequest  # noqa: E501
from swagger_server.models.auth_me_get200_response import AuthMeGet200Response  # noqa: E501
from swagger_server.models.auth_refresh_post200_response import AuthRefreshPost200Response  # noqa: E501
from swagger_server.models.auth_refresh_post_request import AuthRefreshPostRequest  # noqa: E501
from swagger_server.models.auth_register_post_request import AuthRegisterPostRequest  # noqa: E501
from swagger_server.models.error import Error  # noqa: E501
from swagger_server.models.login_request import LoginRequest  # noqa: E501
from swagger_server.models.login_response import LoginResponse  # noqa: E501
from swagger_server import util


def auth_change_password_post(body):  # noqa: E501
    """Change password

    Change password for authenticated user # noqa: E501

    :param auth_change_password_post_request: 
    :type auth_change_password_post_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    auth_change_password_post_request = body
    if connexion.request.is_json:
        auth_change_password_post_request = AuthChangePasswordPostRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def auth_login_post(body):  # noqa: E501
    """User login

    Authenticate user and receive access &amp; refresh tokens # noqa: E501

    :param login_request: 
    :type login_request: dict | bytes

    :rtype: Union[LoginResponse, Tuple[LoginResponse, int], Tuple[LoginResponse, int, Dict[str, str]]
    """
    login_request = body
    if connexion.request.is_json:
        login_request = LoginRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def auth_logout_post(body=None):  # noqa: E501
    """Logout user

     # noqa: E501

    :param auth_logout_post_request: 
    :type auth_logout_post_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    auth_logout_post_request = body
    if connexion.request.is_json:
        auth_logout_post_request = AuthLogoutPostRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def auth_me_get():  # noqa: E501
    """Get current user profile

     # noqa: E501


    :rtype: Union[AuthMeGet200Response, Tuple[AuthMeGet200Response, int], Tuple[AuthMeGet200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def auth_refresh_post(body):  # noqa: E501
    """Refresh access token

    Exchange refresh token for new access &amp; refresh tokens (rotation) # noqa: E501

    :param auth_refresh_post_request: 
    :type auth_refresh_post_request: dict | bytes

    :rtype: Union[AuthRefreshPost200Response, Tuple[AuthRefreshPost200Response, int], Tuple[AuthRefreshPost200Response, int, Dict[str, str]]
    """
    auth_refresh_post_request = body
    if connexion.request.is_json:
        auth_refresh_post_request = AuthRefreshPostRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def auth_register_post(body):  # noqa: E501
    """Register new user

     # noqa: E501

    :param auth_register_post_request: 
    :type auth_register_post_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    auth_register_post_request = body
    if connexion.request.is_json:
        auth_register_post_request = AuthRegisterPostRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
