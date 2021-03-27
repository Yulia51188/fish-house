import os
import requests

from dotenv import load_dotenv


def get_products(url, token):
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(f'{url}/v2/products', headers=headers)
    response.raise_for_status()
    return response.json()


def get_access_token(url, client_id):
    data = {
        'client_id': client_id,
        'grant_type': 'implicit',
    }
    response = requests.post(f'{url}/oauth/access_token', data=data)
    response.raise_for_status()
    return response.json()["access_token"]


def main():
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    base_url = os.getenv("MOLTIN_API_BASE_URL")
    store_access_token = get_access_token(base_url, client_id)
    products = get_products(base_url, store_access_token)
    print(products)


if __name__ == '__main__':
    main()
