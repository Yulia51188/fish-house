"""
Работает с этими модулями:

python-telegram-bot==11.1.0
redis==3.2.1
"""
import logging
import moltin_interactions as moltin
import os
import redis

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler,
                            MessageHandler)
from textwrap import dedent


_database = None
_store_token = None


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger('fish_store')


CALLBACKS = {
    "BACK": 'back',
    "CART": 'cart',
}


def handle_error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def start(bot, update):
    """
    Хэндлер для состояния START.

    Бот отвечает пользователю фразой "Привет!" и переводит его в состояние ECHO.
    Теперь в ответ на его команды будет запускаеться хэндлер echo.
    """
    keyboard = get_products_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    return "HANDLE_MENU"


def handle_description(bot, update):
    if update.callback_query.data == CALLBACKS["BACK"]:
        keyboard = get_products_keyboard()
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.reply_text('Please choose:',
                                                    reply_markup=reply_markup)
        bot.delete_message(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id
        )
        return "HANDLE_MENU"
    product_id, quantity = update.callback_query.data.split('\t')
    cart_id = update.callback_query.message.chat_id
    old_quantity_in_cart = moltin.get_quantity_in_cart(
        get_store_token(),
        product_id,
        cart_id,
    )
    add_to_cart_result = moltin.add_item_to_cart(
        product_id,
        int(quantity),
        cart_id,
        get_store_token()
    )
    new_quantity_in_cart = moltin.get_quantity_in_cart(
        get_store_token(),
        product_id,
        cart_id,
    )
    if not (new_quantity_in_cart - old_quantity_in_cart) == int(quantity):
        logger.error(f'Failed to add product {product_id} x {quantity} '
                        f'to cart {cart_id} with error: {add_to_cart_result}')
    else:
        logger.info(f'Add product {product_id} x {quantity} to cart {cart_id}')
    return "HANDLE_DESCRIPTION"


def handle_menu(bot, update):
    query = update.callback_query
    product_id = query.data
    logger.info(product_id)
    if product_id == CALLBACKS["CART"]:
        query.message.reply_text(f'Корзина: {query.message.chat_id}')
        return "HANDLE_MENU"
    product = moltin.get_product_details(get_store_token(), product_id)
    image_url = moltin.get_main_image_url(get_store_token(), product)
    reply_markup = InlineKeyboardMarkup(get_description_keyboard(product))
    logger.info('Create keyboard')
    bot.send_photo(
        chat_id=query.message.chat_id,
        photo=image_url,
        caption=create_product_message(product),
        reply_markup=reply_markup,
    )
    bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id
    )
    return "HANDLE_DESCRIPTION"


def create_product_message(product):
    price = product["meta"]["display_price"]["with_tax"]["formatted"]
    message = f'''
        {product["name"]}\n
        {price} per {product["weight"]["kg"]} kg
        {product["meta"]["stock"]["level"]} items on stock\n
        {product["description"]}
    '''
    return dedent(message)


def echo(bot, update):
    """
    Хэндлер для состояния ECHO.

    Бот отвечает пользователю тем же, что пользователь ему написал.
    Оставляет пользователя в состоянии ECHO.
    """
    users_reply = update.message.text
    update.message.reply_text(users_reply)
    return "ECHO"


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
    else:
        user_state = db.get(chat_id).decode("utf-8")

    states_functions = {
        'START': start,
        'ECHO': echo,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,

    }
    state_handler = states_functions[user_state]
    # Если вы вдруг не заметите, что python-telegram-bot перехватывает ошибки.
    # Оставляю этот try...except, чтобы код не падал молча.
    # Этот фрагмент можно переписать.
    try:
        next_state = state_handler(bot, update)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def get_products_keyboard():
    products = moltin.get_products(get_store_token())
    buttons = [
        [InlineKeyboardButton(product["name"], callback_data=product["id"])]
        for product in products
    ]
    buttons.append([InlineKeyboardButton('Корзина',
        callback_data=CALLBACKS["CART"])])
    logger.info(buttons)
    return buttons


def get_description_keyboard(product):
    quantity_factors = (1, 5, 10)
    unit_weight = product["weight"]["kg"]
    quantity_buttons = []
    for factor in quantity_factors:
        callback_data = f'{product["id"]}\t{factor}'
        button_text = f"x{factor} ({unit_weight * factor} kg)"
        quantity_buttons.append(InlineKeyboardButton(button_text,
            callback_data=callback_data))
    back_button = [InlineKeyboardButton("Назад",
        callback_data=CALLBACKS["BACK"])]
    keyboard = [quantity_buttons, back_button]
    return keyboard


def get_database_connection():
    """
    Возвращает конекшн с базой данных Redis, либо создаёт новый, если он ещё не создан.
    """
    global _database
    if _database is None:
        database_password = os.getenv("DATABASE_PASSWORD", default=None)
        database_host = os.getenv("DATABASE_HOST", default='localhost')
        database_port = os.getenv("DATABASE_PORT", default=6379)
        _database = redis.Redis(host=database_host, port=database_port,
            password=database_password)
    return _database


def get_store_token():
    """
    Возвращает токен CRM магазина, либо запрашивает новый по client_id
    """
    global _store_token
    if _store_token is None:
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")
        _store_token = moltin.get_credentials(client_id, client_secret)
        logger.info(f'Store token is received {_store_token}')
    return _store_token


if __name__ == '__main__':
    load_dotenv()
    token = os.getenv("TG_TOKEN")

    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.dispatcher.add_error_handler(handle_error)
    updater.start_polling()
