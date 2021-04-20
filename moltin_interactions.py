import logging
import os
import requests

from dotenv import load_dotenv

MOLTIN_URL = 'https://api.moltin.com'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger('fish_store')


def get_products(token, url=MOLTIN_URL):
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(f'{url}/v2/products', headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_product_details(token, product_id, url=MOLTIN_URL):
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(f'{url}/v2/products/{product_id}', headers=headers)
    response.raise_for_status()
    return response.json()["data"]


def get_access_token(client_id, url=MOLTIN_URL):
    data = {
        'client_id': client_id,
        'grant_type': 'implicit',
    }
    response = requests.post(f'{url}/oauth/access_token', data=data)
    response.raise_for_status()
    return response.json()["access_token"]


def get_credentials(client_id, client_secret, url=MOLTIN_URL):
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    response = requests.post(f'{url}/oauth/access_token', data=data)
    response.raise_for_status()
    return response.json()["access_token"]


def add_item_to_cart(item_id, quantity, cart_id, token, url=MOLTIN_URL):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "data": {
            "id": item_id,
            "type": "cart_item",
            "quantity": quantity,
        }
    }
    response = requests.post(
        f'{url}/v2/carts/{cart_id}/items',
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    return response.json()["data"]


def get_cart(token, cart_id, url=MOLTIN_URL):
    headers = {
        "Authorization": f"Bearer {token}",
    }
    response = requests.get(
        f'{url}/v2/carts/{cart_id}',
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def get_cart_items(token, cart_id, url=MOLTIN_URL):
    headers = {
        "Authorization": f"Bearer {token}",
    }
    response = requests.get(
        f'{url}/v2/carts/{cart_id}/items',
        headers=headers
    )
    response.raise_for_status()
    return response.json()["data"]


def upload_file(token, file_path, public=True, url=MOLTIN_URL):
    headers = {
        "Authorization": f"Bearer {token}",
    }
    with open(file_path, 'rb') as file_obj:
        files = {
            "file": file_obj,
            "public": str(public).lower(),
        }
        response = requests.post(
            f'{url}/v2/files',
            headers=headers,
            files=files,
        )
    response.raise_for_status()
    return response.json()["data"]


def set_main_image(token, product_id, image_id, url=MOLTIN_URL):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "data": {
            "type": "main_image",
            "id": image_id,

        }
    }
    response = requests.post(
        f'{url}/v2/products/{product_id}/relationships/main-image',
        headers=headers,
        json=payload,
    )
    response.raise_for_status()
    return response.json()


def get_file(token, file_id, url=MOLTIN_URL):
    headers = {
        "Authorization": f"Bearer {token}",
    }
    response = requests.get(
        f'{url}/v2/files/{file_id}',
        headers=headers,
    )
    response.raise_for_status()
    return response.json()["data"]


def get_main_image_url(token, product):
    image_id = product["relationships"]["main_image"]["data"]["id"]
    return get_file(token, image_id)["link"]["href"]


def get_quantity_in_cart(token, product_id, cart_id):
    products = get_cart_items(token, cart_id)
    desired_product_in_cart = [product for product in products
                                if product["product_id"] == product_id]
    if not any(desired_product_in_cart):
        return 0
    return desired_product_in_cart[0]["quantity"]


def main():
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    base_url = os.getenv("MOLTIN_API_BASE_URL", default=MOLTIN_URL)
    store_access_token = get_credentials(client_id, client_secret)
    product = get_product_details(
        store_access_token,
        "03e5f7d3-5806-4022-af80-bc3a32e184c2"
    )
    logger.debug('PRODUCT\n', product)
    quantity = get_quantity_in_cart(
        store_access_token,
        product["id"],
        "test12345"
    )
    logger.debug('QUANTITY IN CART\n', quantity)


if __name__ == '__main__':
    main()
