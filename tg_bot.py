import logging
import os
import time

import redis
from dotenv import load_dotenv
from telegram import InlineKeyboardMarkup, ParseMode
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)

import keyboards
import messages
import moltin_interactions as moltin


_database = None
_store_token = None
_token_birthtime = 0


logger = logging.getLogger('fish_store')


CALLBACKS = {
    "BACK": "back",
    "CART": "cart",
    "DELETE_ALL": "delete_all",
    "BUY": "buy",
    "PREVIOUS_PAGE": "previous_page",
    "NEXT_PAGE": "next_page",
}
TOKEN_LIFETIME = 60 * 60
MENU_PAGE_LIMIT = 4


def handle_error(bot, update, error):
    logger.error('Update "%s" caused error "%s"', update, error)


def start(bot, update):
    send_start_menu_message(bot, update)
    return "HANDLE_MENU"


def handle_description(bot, update):
    if update.callback_query.data == CALLBACKS["BACK"]:
        send_start_menu_message(bot, update)
        bot.delete_message(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id
        )
        return "HANDLE_MENU"
    product_id, quantity = update.callback_query.data.split('\t')
    cart_id = update.callback_query.message.chat_id
    _add_to_cart_result = moltin.add_item_to_cart(
        product_id,
        int(quantity),
        cart_id,
        get_store_token()
    )
    update.callback_query.answer(text='Product is added to cart')
    logger.info(f'Add product {product_id} x {quantity} to cart {cart_id}')
    return "HANDLE_DESCRIPTION"


def handle_menu(bot, update):
    chat_id = update.callback_query.message.chat_id
    menu_page_index = get_current_page(chat_id)

    query = update.callback_query
    product_id = query.data
    if product_id == CALLBACKS["CART"]:
        send_cart_message(bot, update)
        return "HANDLE_CART"
    if product_id == CALLBACKS["NEXT_PAGE"]:
        menu_page_index = menu_page_index + 1
        update_current_page(chat_id, menu_page_index)
        send_start_menu_message(bot, update)
        bot.delete_message(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id
        )
        return "HANDLE_MENU"
    if product_id == CALLBACKS["PREVIOUS_PAGE"]:
        menu_page_index = menu_page_index - 1
        update_current_page(chat_id, menu_page_index)
        send_start_menu_message(bot, update)
        bot.delete_message(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id
        )
        return "HANDLE_MENU"
    
    product = moltin.get_product_details(get_store_token(), product_id)
    image_url = moltin.get_main_image_url(get_store_token(), product)
    reply_markup = InlineKeyboardMarkup(
        keyboards.get_description_keyboard(product, CALLBACKS))
    bot.send_photo(
        chat_id=query.message.chat_id,
        photo=image_url,
        caption=messages.create_product_message(product),
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
    )
    bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id
    )
    return "HANDLE_DESCRIPTION"


def handle_cart(bot, update):
    if update.callback_query.data == CALLBACKS["BACK"]:
        send_start_menu_message(bot, update)
        bot.delete_message(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id
        )
        return "HANDLE_MENU"
    if update.callback_query.data == CALLBACKS["BUY"]:
        update.callback_query.message.edit_text('Please input your email')
        return "WAITING_EMAIL"
    cart_id = update.callback_query.message.chat_id
    if update.callback_query.data == CALLBACKS["DELETE_ALL"]:
        moltin.delete_cart_items(
            get_store_token(),
            cart_id,
        )
        logger.info(f'Delete all items in cart {cart_id}')
    else:
        moltin.delete_cart_item(
            get_store_token(),
            cart_id,
            update.callback_query.data,
        )
        logger.info(
            f'Delete item {update.callback_query.data} in cart {cart_id}')
    send_cart_message(bot, update)
    return "HANDLE_CART"


def handle_waiting_email(bot, update):
    user_email = update.message.text
    customer = moltin.create_customer(get_store_token(), user_email)
    update.message.reply_text(
        f'Your email is: {user_email}\nYour customer ID is: {customer["id"]}'
    )
    return "ORDERING"


def handle_ordering(bot, update):
    #TODO: add ordering
    pass


def handle_users_reply(bot, update):
    """
    Функция, которая запускается при любом сообщении от пользователя и решает как его обработать.
    Эта функция запускается в ответ на эти действия пользователя:
        * Нажатие на inline-кнопку в боте
        * Отправка сообщения боту
        * Отправка команды боту
    Она получает стейт пользователя из базы данных и запускает соответствующую функцию-обработчик (хэндлер).
    Функция-обработчик возвращает следующее состояние, которое записывается в базу данных.
    Если пользователь только начал пользоваться ботом, Telegram форсит его написать "/start",
    поэтому по этой фразе выставляется стартовое состояние.
    Если пользователь захочет начать общение с ботом заново, он также может воспользоваться этой командой.
    """
    db = get_database_connection()

    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    
    if user_reply == '/start':
        user_state = 'START'
        db.set(f"{chat_id}_page", 0)
    else:
        user_state = db.get(chat_id).decode("utf-8")
    
    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': handle_waiting_email,
        'ORDERING': handle_ordering,
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(bot, update)
        db.set(chat_id, next_state)
    except Exception as error:
        logger.error(error)


def send_cart_message(bot, update):
    cart_id = update.callback_query.message.chat_id
    reply_markup = InlineKeyboardMarkup(keyboards.get_cart_keyboard(cart_id, 
        get_store_token(), CALLBACKS))
    logger.info(f"Cart keyboard is created: {reply_markup}")
    cart_message = messages.create_cart_message(cart_id, get_store_token())
    update.callback_query.message.edit_text(
        cart_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    return


def send_start_menu_message(bot, update):
    menu_page_index = get_current_page(update.callback_query.message.chat_id)

    keyboard = keyboards.get_products_keyboard(
        get_store_token(),
        CALLBACKS,
        MENU_PAGE_LIMIT,
        menu_page_index
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        update.callback_query.message.reply_text('Please choose:',
            reply_markup=reply_markup)
        return
    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    return


def get_database_connection():
    """Возвращает конекшн с базой данных Redis, либо создаёт новый, если он ещё не создан."""
    global _database
    if _database is None:
        database_password = os.getenv("DATABASE_PASSWORD", default=None)
        database_host = os.getenv("DATABASE_HOST", default='localhost')
        database_port = os.getenv("DATABASE_PORT", default=6379)
        _database = redis.Redis(host=database_host, port=database_port,
            password=database_password)
    return _database


def get_store_token():
    """Возвращает токен CRM магазина, либо запрашивает новый по client_id"""
    global _store_token
    global _token_birthtime
    if (_store_token is None or 
            (time.time() - _token_birthtime) > TOKEN_LIFETIME):
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")
        _store_token = moltin.get_credentials(client_id, client_secret)
        _token_birthtime = time.time()
        logger.info(f'Get new client credentials at {_token_birthtime}')
    return _store_token


def get_current_page(chat_id):
    db = get_database_connection()
    return db.get(f"{chat_id}_page")


def update_current_page(chat_id, new_page_index):
    db = get_database_connection()
    return db.set(f"{chat_id}_page", new_page_index)    


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    load_dotenv()
    token = os.getenv("TG_TOKEN")
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.dispatcher.add_error_handler(handle_error)
    updater.start_polling()
