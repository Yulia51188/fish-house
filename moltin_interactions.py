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


def upload_file(token, file_path, public=True, url=MOLTIN_URL):
    headers = {
        "Authorization": f"Bearer {token}",
    }
    print(str(public).lower())
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
    print(headers)
    print(payload)
    print(f'URL: {url}/v2/products/{product_id}/relationships/main-image')
    response = requests.post(
        f'{url}/v2/products/{product_id}/relationships/main-image',
        headers=headers,
        json=payload,
    )
    response.raise_for_status()
    return response.json()


def download_file(token, file_id, url=MOLTIN_URL):
    headers = {
        "Authorization": f"Bearer {token}",
    }
    response = requests.get(
        f'{url}/v2/files/{file_id}',
        headers=headers,
    )
    response.raise_for_status()
    return response.json()


def main():
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    base_url = os.getenv("MOLTIN_API_BASE_URL", default=MOLTIN_URL)
    store_access_token = get_credentials(client_id, client_secret)
    products = get_products(store_access_token, base_url)
    treska_id = upload_file(store_access_token, 'Images/forel.jpg')["id"]
    main_image = set_main_image(store_access_token, products[2]["id"], treska_id)
    print(main_image)


if __name__ == '__main__':
    main()
