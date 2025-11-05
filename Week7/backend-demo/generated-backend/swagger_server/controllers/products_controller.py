import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from swagger_server.models.api_products_get200_response import ApiProductsGet200Response  # noqa: E501
from swagger_server.models.api_products_post201_response import ApiProductsPost201Response  # noqa: E501
from swagger_server.models.api_products_post_request import ApiProductsPostRequest  # noqa: E501
from swagger_server.models.api_products_product_id_delete200_response import ApiProductsProductIdDelete200Response  # noqa: E501
from swagger_server.models.api_products_product_id_get200_response import ApiProductsProductIdGet200Response  # noqa: E501
from swagger_server.models.api_products_product_id_put200_response import ApiProductsProductIdPut200Response  # noqa: E501
from swagger_server.models.api_products_product_id_put_request import ApiProductsProductIdPutRequest  # noqa: E501
from swagger_server import util

# MongoDB Integration
from swagger_server.mongodb import (
    get_all_products,
    get_product_by_id,
    create_product,
    update_product,
    delete_product
)


def api_products_get(category=None, min_price=None, max_price=None):  # noqa: E501
    """Get all products

    Retrieve list of all products (public endpoint) # noqa: E501

    :param category: Filter by category
    :type category: str
    :param min_price: Minimum price filter
    :type min_price: 
    :param max_price: Maximum price filter
    :type max_price: 

    :rtype: Union[ApiProductsGet200Response, Tuple[ApiProductsGet200Response, int], Tuple[ApiProductsGet200Response, int, Dict[str, str]]
    """
    try:
        products = get_all_products(category, min_price, max_price)
        return {'products': products}, 200
    except Exception as e:
        return {'error': str(e)}, 500


def api_products_post(body):  # noqa: E501
    """Create new product

    Create a new product (requires authentication) # noqa: E501

    :param api_products_post_request: 
    :type api_products_post_request: dict | bytes

    :rtype: Union[ApiProductsPost201Response, Tuple[ApiProductsPost201Response, int], Tuple[ApiProductsPost201Response, int, Dict[str, str]]
    """
    api_products_post_request = body
    if connexion.request.is_json:
        api_products_post_request = ApiProductsPostRequest.from_dict(connexion.request.get_json())  # noqa: E501
    
    try:
        product_data = connexion.request.get_json()
        # For demo, use static user_id (in production, get from JWT token)
        user_id = product_data.get('created_by', 'demo_user')
        new_product = create_product(product_data, user_id)
        return new_product, 201
    except Exception as e:
        return {'error': str(e)}, 500


def api_products_product_id_delete(product_id):  # noqa: E501
    """Delete product

    Delete a product (owner or admin only) # noqa: E501

    :param product_id: 
    :type product_id: int

    :rtype: Union[ApiProductsProductIdDelete200Response, Tuple[ApiProductsProductIdDelete200Response, int], Tuple[ApiProductsProductIdDelete200Response, int, Dict[str, str]]
    """
    try:
        success = delete_product(str(product_id))
        if success:
            return {'message': 'Product deleted successfully'}, 200
        return {'error': 'Product not found'}, 404
    except Exception as e:
        return {'error': str(e)}, 500


def api_products_product_id_get(product_id):  # noqa: E501
    """Get product by ID

    Retrieve a specific product by its ID # noqa: E501

    :param product_id: 
    :type product_id: int

    :rtype: Union[ApiProductsProductIdGet200Response, Tuple[ApiProductsProductIdGet200Response, int], Tuple[ApiProductsProductIdGet200Response, int, Dict[str, str]]
    """
    try:
        product = get_product_by_id(str(product_id))
        if product:
            return product, 200
        return {'error': 'Product not found'}, 404
    except Exception as e:
        return {'error': str(e)}, 500


def api_products_product_id_put(product_id, body):  # noqa: E501
    """Update product

    Update an existing product (owner or admin only) # noqa: E501

    :param product_id: 
    :type product_id: int
    :param api_products_product_id_put_request: 
    :type api_products_product_id_put_request: dict | bytes

    :rtype: Union[ApiProductsProductIdPut200Response, Tuple[ApiProductsProductIdPut200Response, int], Tuple[ApiProductsProductIdPut200Response, int, Dict[str, str]]
    """
    api_products_product_id_put_request = body
    if connexion.request.is_json:
        api_products_product_id_put_request = ApiProductsProductIdPutRequest.from_dict(connexion.request.get_json())  # noqa: E501
    
    try:
        product_data = connexion.request.get_json()
        updated_product = update_product(str(product_id), product_data)
        if updated_product:
            return updated_product, 200
        return {'error': 'Product not found'}, 404
    except Exception as e:
        return {'error': str(e)}, 500
