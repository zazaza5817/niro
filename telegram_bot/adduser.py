import requests # type: ignore
import json
from datetime import datetime, timedelta
import telebot # type: ignore
import psycopg2 # type: ignore
import os

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='logs/adduser.log',
    filemode='a'
)

connect_str = os.environ.get('DATABASE_URL')
bot = telebot.TeleBot("123:qwer")
servers = {
    '1': {
        'BASE_URL': "https://url.com/123/panel",
        'PUBLIC_KEY': "pbk",
        'SHORT_ID': "sh_id",
        'SUB_ID': "sub_id",
        'CONNECTION_NAME': "some_name",
        'SERVER_ADDRESS': "url.com",
        'SERVER_PORT': "123",
        'login_url': "https://url.com/123/login",
        'limit': 100,
        'login': "l",
        'password': "veryStrong",
        'id': 1
    }
}

MAX_RETRIES = 10

def calculate_expiry_time(days):
    expiry_date = datetime.now() + timedelta(days=days)
    expiry_time = int(expiry_date.timestamp() * 1000)
    return expiry_time

def update_user(user_id, email, new_expiry, server_id):
    server = servers[str(server_id)]
    session = create_ssesion(server)


    payload = {
        "id": 1,
        "settings": {
            "clients": [
                {
                    "id": user_id,
                    "flow": "xtls-rprx-vision",
                    "email": email,
                    "limitIp": 0,
                    "totalGB": 0,
                    "expiryTime": new_expiry,
                    "enable": True,
                    "tgId": 0,
                    "subId": server['SUB_ID'],
                    "reset": 0
                }
            ]
        }
    }  
    url = f"{server['BASE_URL']}/inbound/updateClient/{user_id}"
    retries = 0
    while retries < MAX_RETRIES:
        response = session.post(url, data={"id": 1, "settings": json.dumps(payload["settings"])})
        if response.status_code == 200:
            logging.info("user updated plan")
            bot.send_message(-123, f"(update expiry) new expiry set for {user_id}")
            return "ok"
    else:
        logging.error("cannot update user plan")
        bot.send_message(-123, f"(update expiry)max retries on {user_id} {response}")
        return "error"


def update_expired_status():
    with psycopg2.connect(connect_str) as conn:
        cursor = conn.cursor()

        current_time = datetime.now()

        cursor.execute("""
            UPDATE users
            SET status = 'expired'
            WHERE expiry < %s AND status != 'expired'
        """, (current_time.strftime('%Y-%m-%d %H:%M'),))

        conn.commit()


def select_server():
    update_expired_status()
    with psycopg2.connect(connect_str) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT server_id, COUNT(*) AS active_users_count
            FROM users
            WHERE status = 'active'
            GROUP BY server_id
        """)

        results = cursor.fetchall()
    candidates = []
    for key in servers.keys():
        limit = servers[key]['limit']
        current_value = 0
        for server_id, active_count in results:
            if str(server_id) == key:
                current_value = active_count
                break
        if limit >= current_value:
            print("FOUND AVAILABLE SERVER")
            return servers[key]
        candidates.append((current_value - limit, key))
    candidates.sort(key=lambda x: x[0])
    
    print(candidates)
    print(f"SERVERS OVERLOADED BUT SELECTED SERVER {candidates[0][1]}")
    serverinfo = f"limit: {servers[candidates[0][1]]['limit']} \ncurrent overload: {candidates[0][0]}"
    bot.send_message(-123, f"SERVERS OVERLOADED BUT SELECTED SERVER {candidates[0][1]}\n{serverinfo}")
    return servers[candidates[0][1]]


def create_ssesion(server):
    retries = 0
    while True:
        try:
            if retries > MAX_RETRIES:
                logging.error('ошибка создания сессии максимальное количество повторений')
                return None
            session = requests.Session()
            login_payload = {
                "username": server['login'],
                "password": server['password']
            }
            # если инстанс vless без домена
            # verify = "server.crt"
            session.post(server['login_url'], data=login_payload)
            return session
        except Exception as e:
            logging.exception("ошибка поптыки create_session")
            print("ошибка поптыки create_session")
            print(e)
            retries += 1


def add_client(email, client_id, total_gb, expiry_days):
    server = select_server()
    url = f"{server['BASE_URL']}/inbound/addClient"

    # Преобразование гигабайтов в байты
    total_gb_in_bytes = total_gb * 1024 * 1024 * 1024

    # Расчет времени истечения
    expiry_time = calculate_expiry_time(expiry_days)

    # Формирование payload
    payload = {
        "id": 1,
        "settings": {
            "clients": [
                {
                    "id": client_id,
                    "flow": "xtls-rprx-vision",
                    "email": email,
                    "limitIp": 0,
                    "totalGB": total_gb_in_bytes,
                    "expiryTime": expiry_time,
                    "enable": True,
                    "tgId": 0,
                    "subId": server['SUB_ID'],
                    "reset": 0
                }
            ]
        }
    }
    session = create_ssesion(server)
    retries = 0
    while retries < MAX_RETRIES:
        response = session.post(url, data={"id": 1, "settings": json.dumps(payload["settings"])})

        # Проверка успешности добавления клиента
        if response.status_code == 200:
            # Формирование ссылки на подключение
            connection_url = (
                f"vless://{client_id}@{server['SERVER_ADDRESS']}:{server['SERVER_PORT']}/?"
                f"type=tcp&security=reality&pbk={server['PUBLIC_KEY']}&fp=chrome&sni=google.com&"
                f"sid={server['SHORT_ID']}&spx=%2F&flow=xtls-rprx-vision#{server['CONNECTION_NAME']}-{email}"
            )
            logging.info("user added")
            bot.send_message(-123, f"new user added ok")
            return response.status_code, response.text, connection_url, server['id']
    else:
        logging.error("cannot add user")
        bot.send_message(-123, f"ERROR ADDING USER")
        return response.status_code, response.text, None, None, None
