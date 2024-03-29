import logging
import requests


MOLTIN_URL = 'https://api.moltin.com'

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


def get_credentials(client_id, client_secret, url=MOLTIN_URL):
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    response = requests.post(f'{url}/oauth/access_token', data=data)
    response.raise_for_status()
    return response.json()


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
    return response.json()["data"]


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


def delete_cart_items(token, cart_id, url=MOLTIN_URL):
    headers = {
        "Authorization": f"Bearer {token}",
    }
    response = requests.delete(
        f'{url}/v2/carts/{cart_id}/items',
        headers=headers,
    )
    response.raise_for_status()
    return response.text


def delete_cart_item(token, cart_id, item_id, url=MOLTIN_URL):
    headers = {
        "Authorization": f"Bearer {token}",
    }
    response = requests.delete(
        f'{url}/v2/carts/{cart_id}/items/{item_id}',
        headers=headers,
    )
    response.raise_for_status()
    return response.text


def create_customer(token, email, name='No name', password=None, url=MOLTIN_URL):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "data": {
            "type": "customer",
            "name": name,
            "email": email,
            "password": password or email,
        }
    }
    response = requests.post(
        f'{url}/v2/customers',
        headers=headers,
        json=payload,
    )
    if response.status_code == 409:
        logger.warning(f'Client with email "{email}" is already exists')
        return get_customer_by_email(token, email)
    response.raise_for_status()
    customer = response.json()["data"]
    logger.info(f"Create a new customer with email {email}")
    return customer


def get_customer_by_email(token, email, url=MOLTIN_URL):
    headers = {
        "Authorization": f"Bearer {token}",
    }
    params = {
        "filter": f"eq(email,{email})"
    }
    response = requests.get(
        f'{url}/v2/customers',
        headers=headers,
        params=params,
    )
    response.raise_for_status()
    return response.json()["data"][0]
