import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='logs/bot.log',
    filemode='a'
)

import telebot
import uuid
import datetime
from adduser import add_client, update_user
from datetime import datetime, timedelta
import jwt
import psycopg2
from telebot import types
import os
import json

SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
connect_str = os.environ.get('DATABASE_URL')
tg_token = os.environ.get('TG_TOKEN')


with open('/app/data/plans.json', 'r') as file:
    plans_invoice = json.load(file)
    logging.info(plans_invoice)


def get_price(payload):
    plan = plans_invoice.get(payload)
    return plan['price']

bot = telebot.TeleBot(tg_token)


def generate_conf(message, plan):
    email = str(uuid.uuid4())
    client_id = str(uuid.uuid4())
    user_id = message.from_user.id
    logging.info("email generated")
    status_code, response_text, connection_url, server_id = add_client(email, client_id, 0, plan['duration'])
    if status_code != 200:
        print(-4516170921, f"(generate conf)max retries on {message.chat.id} {response_text}")
        print(message.chat.id, f"Ошибка! Обратитесь в поддержку")
        logging.error("MAX RETRIES")
        return
    logging.info("CONFIGURATION CREATED")
    token_data = {
        'user_id': user_id,
        'email': email
    }
    jwt_token = jwt.encode(token_data, SECRET_KEY, algorithm='HS256')
    logging.info("jwt created")

    with psycopg2.connect(connect_str) as conn:
        cursor = conn.cursor()
        current_datetime = datetime.now()
        expiry_datetime = current_datetime + timedelta(days=plan['duration'])
        expiry_datetime_str = expiry_datetime.strftime('%Y-%m-%d %H:%M')
        cursor.execute('''
            INSERT INTO users (tg_id, status, expiry, connection_link, email, id, server_id, jwt_token)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, 'active', expiry_datetime_str, connection_url, email, client_id, server_id, jwt_token))
        conn.commit()
        bot.send_message(-4516170921, f"(generate conf) new conf created for @{message.from_user.username}")
        logging.info("db updated")

def set_expiry(message, new_expiry):
    new_expiry_str = new_expiry.strftime('%Y-%m-%d %H:%M')
    new_expiry_time = int(new_expiry.timestamp() * 1000)
    user_id = message.from_user.id
    with psycopg2.connect(connect_str) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT email, id, server_id FROM users WHERE tg_id = %s", (user_id,))
            res = cursor.fetchone()
            update_user(res[1], res[0], new_expiry_time, res[2])

            cursor.execute("UPDATE users SET expiry = %s WHERE tg_id = %s", (new_expiry_str, user_id))
            conn.commit()

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.InlineKeyboardMarkup()
    web_app_info = types.WebAppInfo("https://nirovpn.com")  # Замените на URL вашего миниприложения
    miniapp_button = types.InlineKeyboardButton(text="niro vpn", web_app=web_app_info)
    markup.add(miniapp_button)
    bot.send_message(message.chat.id,
                    "🚀Наш сервис обеспечивает быстрое, надежное и приватное подключение к интернету. Мы гарантируем, "
                    "что *никакие пользовательские данные не собираются* и не отслеживаются.\n\n✅ Настройка "
                    "конфигурации VPN в несколько простых кликов.\n✅ Защитите свою приватность и обеспечьте "
                    "безопасность в сети.\n✅ Наш сервис кросс-платформенный, вы можете использовать купленную подписку "
                    "на любом своем устройстве\n✅ Для использования нашего сервиса нужно приобрести подписку.\n\n📋 "
                    "Чтобы узнать подробнее, как всё работает, напишите /info", parse_mode="markdown", reply_markup=markup)


@bot.message_handler(commands=['info'])
def start_message(message):
    markup = types.InlineKeyboardMarkup()
    web_app_info = types.WebAppInfo("https://nirovpn.com")  # Замените на URL вашего миниприложения
    miniapp_button = types.InlineKeyboardButton(text="niro vpn", web_app=web_app_info)
    markup.add(miniapp_button)

    bot.send_message(message.chat.id, "🔒Наш сервис использует протокол VLESS, который обеспечивает высокую степень "
                                      "шифрования и обфусцирования интернет-трафика. Это делает его надежным и "
                                      "значительно усложняет возможность блокировки в России.\n📍 Быстрый сервер "
                                      "расположен в Германии. Благодаря оптимизированной инфраструктуре, "
                                      "ваше соединение будет стабильным и быстрым.\n🔧 Процесс первоначальной "
                                      "настройки прост и не требует специальных навыков — настройка занимает всего "
                                      "несколько минут.\n"
                                      "👩‍💻Если у вас возникнут вопросы, наша поддержка всегда готова помочь.", reply_markup=markup)


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    payload = pre_checkout_query.invoice_payload
    plan_price = get_price(payload)
    
    if plan_price:
        if pre_checkout_query.total_amount == plan_price:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
            logging.info(f"payment precheck ok! {plan_price}")
        else:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False, 
                                          error_message="Неверная сумма платежа.")
            logging.info(f"err payment amount {pre_checkout_query.total_amount}, but neded {plan_price}")
    else:
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False,
                                      error_message="Ошибка оплаты.")
        logging.info(f"payment err {pre_checkout_query}")



@bot.message_handler(content_types=['successful_payment'])
def handle_payment(message):
    try:
        payload = message.successful_payment.invoice_payload
        bot.send_message(-4516170921, f"new payment (ENVELOPE) from @{message.from_user.username} ({message.from_user.id})")
        plan = plans_invoice[payload]
        user_id = message.from_user.id
        with psycopg2.connect(connect_str) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, expiry, server_id FROM users WHERE tg_id = %s", (user_id,))
            res = cursor.fetchone()
        if not res:
            logging.info("New user")
            generate_conf(message, plan)
            bot.send_message(message.chat.id, f"Подписка активна! Для использования vpn необходимо установить конфигурацию")
            return
            
        expiry_datetime = datetime.strptime(res[1], '%Y-%m-%d %H:%M')
        current_datetime = datetime.now()
        time_left = expiry_datetime - current_datetime
        
        if time_left.total_seconds() <= 0:
            with psycopg2.connect(connect_str) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE tg_id = %s", (user_id,))
                conn.commit()
            generate_conf(message, plan)
            bot.send_message(message.chat.id, f"Подписка снова активна! Для продолжения использования vpn необходимо переустановить конфигурацию")
            logging.info("renew subscription")
        else:
            new_expiry = expiry_datetime + timedelta(days=plan['duration'])
            set_expiry(message, new_expiry)
            bot.send_message(message.chat.id, f"Подписка продлена!")
            logging.info("just add time")
    except:
        logging.exception("Ошибка обработки оплаты!")
        bot.send_message(-4516170921, f"payment process error @{message.from_user.username} ({message.from_user.id})")


while True:
    print("starting")
    logging.info("starting")
    try:
        bot.polling()
    except:
        logging.exception("ошибка bot.polling")