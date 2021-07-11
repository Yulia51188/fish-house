from telegram import InlineKeyboardButton

import moltin_interactions as moltin


def get_products_keyboard(token, callbacks, page_limit=None, page_index=0):
    products = moltin.get_products(token)
    service_buttons = []
    product_buttons = [
        [InlineKeyboardButton(product["name"], callback_data=product["id"])]
        for product in products
    ]
    if page_limit and len(product_buttons) > page_limit:
        product_buttons = product_buttons[page_index * page_limit:]
        if page_index > 0:
            service_buttons.append([InlineKeyboardButton('Previous',
                callback_data=callbacks["PREVIOUS_PAGE"])])
        if len(product_buttons) > page_limit:
            product_buttons = product_buttons[:page_limit]
            service_buttons.append([InlineKeyboardButton('Next',
                callback_data=callbacks["NEXT_PAGE"])])
    service_buttons.append([InlineKeyboardButton('Go to cart',
        callback_data=callbacks["CART"])])
    return [*product_buttons, *service_buttons]


def get_description_keyboard(product, callbacks):
    quantity_factors = (1, 5, 10)
    unit_weight = product["weight"]["kg"]
    quantity_buttons = []
    for factor in quantity_factors:
        callback_data = f'{product["id"]}\t{factor}'
        button_text = f"x{factor} ({unit_weight * factor} kg)"
        quantity_buttons.append(InlineKeyboardButton(button_text,
            callback_data=callback_data))
    back_button = [InlineKeyboardButton("Return to menu",
        callback_data=callbacks["BACK"])]
    keyboard = [quantity_buttons, back_button]
    return keyboard


def get_cart_keyboard(cart_id, token, callbacks):
    back_button = [[
        InlineKeyboardButton(
            "Return to menu",
            callback_data=callbacks["BACK"]
        )
    ]]
    products = moltin.get_cart_items(token, cart_id)
    if not any(products):
        return back_button
    delete_button = [[InlineKeyboardButton(
        "Delete all items",
        callback_data=callbacks["DELETE_ALL"]
    )]]
    payment_button = [[InlineKeyboardButton(
        "Buy",
        callback_data=callbacks["BUY"]
    )]]
    product_buttons = [
        [InlineKeyboardButton(f'Remove {product["name"]}',
            callback_data=product["id"])]
        for product in products
    ]
    return [*product_buttons, *delete_button, *payment_button, *back_button]
