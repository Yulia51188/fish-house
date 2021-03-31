import os
import requests

from dotenv import load_dotenv

MOLTIN_URL = 'https://api.moltin.com'


def get_products(token, url=MOLTIN_URL):
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(f'{url}/v2/products', headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_access_token(client_id, url=MOLTIN_URL):
    data = {
        'client_id': client_id,
        'grant_type': 'implicit',
    }
    response = requests.post(f'{url}/oauth/access_token', data=data)
    response.raise_for_status()
    return response.json()["access_token"]


def add_item_to_cart(item_id, quantity, token, url=MOLTIN_URL):
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
        f'{url}/v2/carts/:reference/items',
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    return response.json()["data"]


def get_cart(token, url=MOLTIN_URL):
    headers = {
        "Authorization": f"Bearer {token}",
    }
    response = requests.get(
        f'{url}/v2/carts/:reference',
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def get_cart_items(token, url=MOLTIN_URL):
    headers = {
        "Authorization": f"Bearer {token}",
    }
    response = requests.get(
        f'{url}/v2/carts/:reference/items',
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def main():
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    base_url = os.getenv("MOLTIN_API_BASE_URL", default=MOLTIN_URL)
    store_access_token = get_access_token(client_id, base_url)
    products = get_products(store_access_token, base_url)
    add_item_to_cart(products[1]["id"], 1, store_access_token, base_url)
    cart = get_cart(store_access_token, base_url)
    cart_items = get_cart_items(store_access_token, base_url)


if __name__ == '__main__':
    main()
