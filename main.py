import os
import requests

from dotenv import load_dotenv


def get_products(url, token):
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(f'{url}/v2/products', headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_access_token(url, client_id):
    data = {
        'client_id': client_id,
        'grant_type': 'implicit',
    }
    response = requests.post(f'{url}/oauth/access_token', data=data)
    response.raise_for_status()
    return response.json()["access_token"]


def add_item_to_cart(item_id, quantity, url, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "data": {
            "id": "157c27e4-82bf-46ba-8947-9c9cc8b28b19",
            "type": "cart_item",
            "quantity": 1
        }
    }
    response = requests.post(
        f'{url}/v2/carts/:reference/items',
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    return response.json()["data"]


def main():
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    base_url = os.getenv("MOLTIN_API_BASE_URL")
    store_access_token = get_access_token(base_url, client_id)
    products = get_products(base_url, store_access_token)
    add_item_to_cart(products[0]["id"], 2, base_url, store_access_token)
    

if __name__ == '__main__':
    main()
