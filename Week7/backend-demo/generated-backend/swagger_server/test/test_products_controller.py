import unittest

from flask import json

from swagger_server.models.api_products_get200_response import ApiProductsGet200Response  # noqa: E501
from swagger_server.models.api_products_post201_response import ApiProductsPost201Response  # noqa: E501
from swagger_server.models.api_products_post_request import ApiProductsPostRequest  # noqa: E501
from swagger_server.models.api_products_product_id_delete200_response import ApiProductsProductIdDelete200Response  # noqa: E501
from swagger_server.models.api_products_product_id_get200_response import ApiProductsProductIdGet200Response  # noqa: E501
from swagger_server.models.api_products_product_id_put200_response import ApiProductsProductIdPut200Response  # noqa: E501
from swagger_server.models.api_products_product_id_put_request import ApiProductsProductIdPutRequest  # noqa: E501
from swagger_server.test import BaseTestCase


class TestProductsController(BaseTestCase):
    """ProductsController integration test stubs"""

    def test_api_products_get(self):
        """Test case for api_products_get

        Get all products
        """
        query_string = [('category', 'category_example'),
                        ('min_price', 3.4),
                        ('max_price', 3.4)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/products',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_api_products_post(self):
        """Test case for api_products_post

        Create new product
        """
        api_products_post_request = swagger_server.ApiProductsPostRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/api/products',
            method='POST',
            headers=headers,
            data=json.dumps(api_products_post_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_api_products_product_id_delete(self):
        """Test case for api_products_product_id_delete

        Delete product
        """
        headers = { 
            'Accept': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/api/products/{product_id}'.format(product_id=56),
            method='DELETE',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_api_products_product_id_get(self):
        """Test case for api_products_product_id_get

        Get product by ID
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/products/{product_id}'.format(product_id=56),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_api_products_product_id_put(self):
        """Test case for api_products_product_id_put

        Update product
        """
        api_products_product_id_put_request = swagger_server.ApiProductsProductIdPutRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/api/products/{product_id}'.format(product_id=56),
            method='PUT',
            headers=headers,
            data=json.dumps(api_products_product_id_put_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
