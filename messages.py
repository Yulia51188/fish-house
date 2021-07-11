import logging
from textwrap import dedent

import moltin_interactions as moltin


logger = logging.getLogger('fish_store')


def create_product_message(product):
    price = product["meta"]["display_price"]["with_tax"]["formatted"]
    message = f'''
        {product["name"]}\n
        {price} per {product["weight"]["kg"]} kg
        {product["meta"]["stock"]["level"]} items on stock\n
        {product["description"]}
    '''
    return dedent(message)


def create_product_in_cart_message(product, token):
    product_details = moltin.get_product_details(
        token,
        product["product_id"]
    )
    price = product["meta"]["display_price"]["with_tax"]["unit"]["formatted"]
    cost = product["meta"]["display_price"]["with_tax"]["value"]["formatted"]
    unit_weight = product_details["weight"]["kg"]
    total_weight = float(product["quantity"]) * unit_weight
    message = f'''
        {product["name"]}
        {product["description"]}
        {price} per unit ({unit_weight} kg)
        {total_weight} kg ({product["quantity"]} units) in cart for {cost}
    '''
    return dedent(message)


def create_cart_message(cart_id, token):
    cart = moltin.get_cart(token, cart_id)
    logger.info(f"Cart {cart_id} is received")
    products = moltin.get_cart_items(token, cart_id)
    if not any(products):
        return 'Your cart is empty'
    total_cost = cart["meta"]["display_price"]["with_tax"]["formatted"]
    products_description = ''.join(
        [
            create_product_in_cart_message(product, token) 
            for product in products
        ]
    )
    message = f'{products_description}\nTotal: {total_cost}'
    return dedent(message)
