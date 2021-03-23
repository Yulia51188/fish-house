import os
import requests

from dotenv import load_dotenv


def main():
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    base_url = os.getenv("MOLTIN_API_BASE_URL")
    data = {
        'client_id': client_id,
        'grant_type': 'implicit',
    }
    response = requests.post(f'{base_url}/oauth/access_token', data=data)
    response.raise_for_status()
    store_access_token = response.json()["access_token"]
    print(store_access_token)

    headers = {
        'Authorization': f'Bearer {store_access_token}',
    }
    response = requests.get(f'{base_url}/v2/products', headers=headers)
    response.raise_for_status()
    print(response.text)


if __name__ == '__main__':
    main()
