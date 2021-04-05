"""
Работает с этими модулями:

python-telegram-bot==11.1.0
redis==3.2.1
"""
import os
import logging
import redis
import moltin_interactions as moltin

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
logger = logging.getLogger(__name__)


def handle_error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def start(bot, update):
    """
    Хэндлер для состояния START.

    Бот отвечает пользователю фразой "Привет!" и переводит его в состояние ECHO.
    Теперь в ответ на его команды будет запускаеться хэндлер echo.
    """
    keyboard = get_products_keyboard(get_store_token())
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    return "HANDLE_MENU"


def handle_description(bot, update):
    if update.callback_query.data == 'back':
        keyboard = get_products_keyboard(get_store_token())
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.reply_text('Please choose:',
                                                    reply_markup=reply_markup)
        return "HANDLE_MENU"


def handle_menu(bot, update):
    query = update.callback_query
    product_id = query.data
    product = moltin.get_product_details(get_store_token(), product_id)

    image_url = moltin.get_main_image_url(get_store_token(), product)

    keyboard = [[InlineKeyboardButton("Назад", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

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
    logger.info(dedent(message))
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
        'HANDLE_DESCRIPTION': handle_backward,

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


def get_products_keyboard(token):
    products = moltin.get_products(token)
    buttons = [
        [InlineKeyboardButton(product["name"], callback_data=product["id"])]
        for product in products
    ]
    return buttons


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
