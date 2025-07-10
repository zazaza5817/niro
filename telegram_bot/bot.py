import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='logs/bot.log',
    filemode='a'
)

import telebot # type: ignore
import uuid
import datetime
from adduser import add_client, update_user
from datetime import datetime, timedelta
import jwt # type: ignore
import psycopg2 # type: ignore
from telebot import types # type: ignore
import os
import json
import requests # type: ignore

SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
connect_str = os.environ.get('DATABASE_URL')
tg_token = os.environ.get('TG_TOKEN')
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://backend:8000')
INTERNAL_API_KEY = os.environ.get('INTERNAL_API_KEY', 'default_internal_key_change_me')


with open('/app/data/plans.json', 'r') as file:
    plans_invoice = json.load(file)
    logging.info(plans_invoice)


def apply_referral_code_sync(user_tg_id, referral_code):
    """Применяет реферальный код через API"""
    try:
        logging.info(f"Applying referral code {referral_code} for user {user_tg_id}")
        logging.info(f"{API_BASE_URL}/api/referrals/apply_referral")
        response = requests.post(f"{API_BASE_URL}/api/referrals/apply_referral", 
                               json={"user_tg_id": user_tg_id, "referral_code": referral_code},
                               headers={"X-Internal-API-Key": INTERNAL_API_KEY},
                               timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result.get('success', False)
        return False
    except Exception as e:
        logging.error(f"Error applying referral code: {e}")
        return False


def get_plan_data_sync(user_tg_id, payload):
    """Получает данные плана из реферальных планов или дефолтных настроек"""
    try:
        # Ищем кастомный план пользователя напрямую в БД
        with psycopg2.connect(connect_str) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT rp.duration, rp.title, rp.description, rp.price 
                FROM referral_plans rp 
                JOIN referral_usage ru ON rp.referral_code_id = ru.referral_code_id 
                WHERE ru.user_tg_id = %s AND rp.payload = %s
            """, (user_tg_id, payload))
            
            result = cursor.fetchone()
            if result:
                logging.info(f"Found referral plan for user {user_tg_id}, payload {payload}")
                return {
                    'duration': result[0],
                    'title': result[1],
                    'description': result[2],
                    'price': result[3]
                }
        
        # Если реферальный план не найден, используем дефолтный
        plan = plans_invoice.get(payload)
        if plan:
            logging.info(f"Using default plan for user {user_tg_id}, payload {payload}")
            return plan
        else:
            logging.error(f"Plan not found for payload {payload}")
            return None
            
    except Exception as e:
        logging.error(f"Error getting plan data: {e}")


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
    # Генерация JWT токена
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

def generate_conf_for_existing_user(message, plan, user_id):
    """Создает конфигурацию для уже существующего пользователя (обновляет запись)"""
    email = str(uuid.uuid4())
    client_id = str(uuid.uuid4())
    logging.info(f"Generating configuration for existing user {user_id}")
    status_code, response_text, connection_url, server_id = add_client(email, client_id, 0, plan['duration'])
    if status_code != 200:
        bot.send_message(-4516170921, f"(generate conf for existing)max retries on {message.chat.id} {response_text}")
        bot.send_message(message.chat.id, f"Ошибка! Обратитесь в поддержку")
        logging.error("MAX RETRIES for existing user")
        return
    logging.info("CONFIGURATION CREATED for existing user")
    # Генерация JWT токена
    token_data = {
        'user_id': user_id,
        'email': email
    }
    jwt_token = jwt.encode(token_data, SECRET_KEY, algorithm='HS256')
    logging.info("jwt created for existing user")

    with psycopg2.connect(connect_str) as conn:
        cursor = conn.cursor()
        current_datetime = datetime.now()
        expiry_datetime = current_datetime + timedelta(days=plan['duration'])
        expiry_datetime_str = expiry_datetime.strftime('%Y-%m-%d %H:%M')
        # Обновляем существующего пользователя вместо создания нового
        cursor.execute('''
            UPDATE users 
            SET status = %s, expiry = %s, connection_link = %s, email = %s, id = %s, server_id = %s, jwt_token = %s
            WHERE tg_id = %s
        ''', ('active', expiry_datetime_str, connection_url, email, client_id, server_id, jwt_token, user_id))
        conn.commit()
        bot.send_message(-4516170921, f"(generate conf for existing) conf updated for @{message.from_user.username}")
        logging.info("db updated for existing user")

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
    # Проверяем, есть ли реферальный код в команде
    args = message.text.split()
    if len(args) > 1:
        referral_code = args[1]
        user_tg_id = message.from_user.id
        
        # Применяем реферальный код
        try:
            is_applied = apply_referral_code_sync(user_tg_id, referral_code)
            if is_applied:
                bot.send_message(message.chat.id, 
                               f"🎉 Код активирован!\n\n")
                logging.info(f"Applied referral code {referral_code} for user {user_tg_id}")
            else:
                bot.send_message(message.chat.id, 
                               "❌ Код недействителен или уже использован\n\n")
                logging.warning(f"Failed to apply referral code {referral_code} for user {user_tg_id}")
        except Exception as e:
            logging.error(f"Error processing referral code: {e}")
    
    markup = types.InlineKeyboardMarkup()
    web_app_info = types.WebAppInfo("https://nirovpn.com")
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
    web_app_info = types.WebAppInfo("https://nirovpn.com")
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
    user_tg_id = pre_checkout_query.from_user.id
    
    # Получаем данные плана (может быть из реферальных планов или дефолтные)
    plan_data = get_plan_data_sync(user_tg_id, payload)
    
    if plan_data:
        plan_price = plan_data.get('price', 0)
        try:
            if pre_checkout_query.total_amount == plan_price:
                bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
                logging.info(f"payment precheck ok (fallback)! {plan_price}")
            else:
                bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False, 
                                              error_message="Неверная сумма платежа.")
                logging.info(f"err payment amount (fallback) {pre_checkout_query.total_amount}, but needed {plan_price}")
        except Exception as e:
            logging.error(f"Error checking price info for user {user_tg_id}: {e}")

    else:
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False,
                                      error_message="Ошибка оплаты.")
        logging.info(f"payment err - plan not found for payload {payload}")



@bot.message_handler(content_types=['successful_payment'])
def handle_payment(message):
    try:
        payload = message.successful_payment.invoice_payload
        bot.send_message(-4516170921, f"new payment from @{message.from_user.username} ({message.from_user.id})")
        
        user_id = message.from_user.id
        # Получаем данные плана (может быть из реферальных планов или дефолтные)
        plan = get_plan_data_sync(user_id, payload)
        
        if not plan:
            bot.send_message(-4516170921, f"не нашелся план после оплаты уже @{message.from_user.username} ({message.from_user.id})")

            logging.error(f"Could not get plan data for payload {payload}")
            bot.send_message(message.chat.id, "Ошибка обработки платежа. Обратитесь в поддержку.")
            return
        
        with psycopg2.connect(connect_str) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, expiry, server_id FROM users WHERE tg_id = %s", (user_id,))
            res = cursor.fetchone()
        
        if not res:
            logging.info("New user - creating configuration")
            generate_conf(message, plan)
            bot.send_message(message.chat.id, f"Подписка активна! Для использования vpn необходимо установить конфигурацию")
            return
        
        user_status = res[0]
        user_expiry = res[1]
        
        # Обрабатываем пользователей со статусом inactive (созданы через реферальную систему)
        if user_status == "inactive" or user_expiry is None:
            logging.info(f"User {user_id} is inactive - creating first configuration")
            # Создаем конфигурацию для существующего пользователя
            generate_conf_for_existing_user(message, plan, user_id)
            bot.send_message(message.chat.id, f"Подписка активна! Для использования vpn необходимо установить конфигурацию")
            return
            
        # Для активных/истекших пользователей проверяем дату
        expiry_datetime = datetime.strptime(user_expiry, '%Y-%m-%d %H:%M')
        current_datetime = datetime.now()
        time_left = expiry_datetime - current_datetime
        
        if time_left.total_seconds() <= 0:
            logging.info(f"User {user_id} subscription expired - recreating configuration")
            # Пересоздаем конфигурацию для существующего пользователя
            generate_conf_for_existing_user(message, plan, user_id)
            bot.send_message(message.chat.id, f"Подписка снова активна! Для продолжения использования vpn необходимо переустановить конфигурацию")
            logging.info("Renew subscription")
        else:
            logging.info(f"User {user_id} extending existing subscription")
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