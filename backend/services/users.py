import logging
logger = logging.getLogger("my_app")
import hashlib
import hmac
import urllib.parse
import json
from datetime import datetime
import jwt # type: ignore
from typing import Dict, Optional
import psycopg2 # type: ignore
from fastapi import HTTPException, status # type: ignore
from config import settings
from models.user import User
from models.subscription import SubscriptionCheckResponse


def check_telegram_auth(telegram_init_data: str, bot_token: str) -> bool:
    try:
        encoded = urllib.parse.unquote(telegram_init_data)
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        data_parts = encoded.split("&")
        hash_index = next((i for i, part in enumerate(data_parts) if part.startswith("hash=")), -1)
        if hash_index == -1:
            raise ValueError("Поле 'hash' отсутствует в данных.")
        received_hash = data_parts.pop(hash_index).split("=")[1]
        data_parts.sort()
        data_check_string = "\n".join(data_parts).encode()
        calculated_hash = hmac.new(secret_key, data_check_string, hashlib.sha256).hexdigest()
        return calculated_hash == received_hash
    except:
        return False

def parse_telegram_data(telegram_init_data: str) -> Optional[Dict]:
    try:
        decoded_data = urllib.parse.unquote(telegram_init_data)
        data_parts = decoded_data.split("&")
        data_dict = {}
        for part in data_parts:
            if "=" in part:
                key, value = part.split("=", 1)
                data_dict[key] = value
        if "user" in data_dict:
            try:
                data_dict["user"] = json.loads(data_dict["user"])
            except json.JSONDecodeError:
                return None
        return data_dict
    except:
        return None

def format_time_left(expiry_datetime_str: str) -> str:
    expiry_datetime = datetime.strptime(expiry_datetime_str, '%Y-%m-%d %H:%M')
    current_datetime = datetime.now()
    time_left = expiry_datetime - current_datetime
    days = time_left.days
    hours = time_left.seconds // 3600
    minutes = (time_left.seconds % 3600) // 60
    if days > 0:
        return f"осталось {days} дней, {hours} часов"
    elif hours > 0:
        return f"осталось {hours} часов, {minutes} минут"
    elif minutes > 0:
        return f"осталось {minutes} минут"
    else:
        return "осталось меньше минуты"

def get_user_by_id(conn: psycopg2.extensions.connection, telegram_id: int):
    with conn.cursor() as cur:
        cur.execute("SELECT status, expiry, jwt_token, connection_link, server_id FROM users WHERE tg_id = %s", (telegram_id,))
        user_info = cur.fetchone()
        if user_info:
            return User(
                tg_id=telegram_id,
                status=user_info[0],
                expiry=user_info[1],
                jwt_token=user_info[2],
                connection_link=user_info[3],
                server_id=user_info[4]
            )
        return None

def update_user_status(conn: psycopg2.extensions.connection, telegram_id: int, status: str):
    with conn.cursor() as cur:
        cur.execute("UPDATE users SET status = %s WHERE tg_id = %s", (status, telegram_id))
    conn.commit()

def generate_jwt_token(user_id: int):
    payload = {"user_id": user_id}
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    return token

async def get_current_user(token: str):
    try:
        logger.info(f"get_current_user called with token: {token}")
        payload = jwt.decode(token.credentials, settings.secret_key, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        with psycopg2.connect(settings.database_url) as conn:
            user = get_user_by_id(conn, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

async def get_subscription(jwt_token: str):
    logger.info(f"get_subscription called with jwt_token: {jwt_token}")
    try:
        payload = jwt.decode(jwt_token, settings.secret_key, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            logger.warning("Invalid token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        with psycopg2.connect(settings.database_url) as conn:
            user_info = get_user_by_id(conn, user_id)
            if not user_info:
                logger.warning(f"User not found for tg_id: {user_id}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            links = [user_info.connection_link]
            html_content = """{}""".format("\n".join([f'{link}' for link in links]))
            date_format = "%Y-%m-%d %H:%M"
            date_object = datetime.strptime(user_info.expiry, date_format)
            unix_time = int(date_object.timestamp())
            response = {
                "html_content": html_content,
                "headers": {
                    "Server": 'nginx',
                    "Subscription-Userinfo": f'expire={unix_time}',
                    "profile-title": 'niro vpn subscription',
                    "profile-web-page-url": 'https://niro.com',
                    "profile-update-interval": '1'
                }
            }
            logger.info(f"Response for user: {user_id} {response}")
            return response
    except Exception as e:
        logger.error(f"Error in get_subscription: {e}")
        raise e

async def check_subscription(auth_data: str) -> SubscriptionCheckResponse:
    logger.info(f"check_subscription called with auth_data: {auth_data}")
    try:
        if not check_telegram_auth(auth_data, settings.telegram_bot_token):
            logger.warning("Invalid Telegram auth data")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ошибка авторизации")
        data = parse_telegram_data(auth_data)
        telegram_id = data['user']['id']
        with psycopg2.connect(settings.database_url) as conn:
            user_info = get_user_by_id(conn, telegram_id)
        if not user_info:
            logger.info("Подписка не активна")
            return SubscriptionCheckResponse(
                status="inactive",
                display_text="Подписка не активна",
                config_url=None
            )
        if user_info.status == "active":
            expiry_datetime = datetime.strptime(user_info.expiry, '%Y-%m-%d %H:%M')
            current_datetime = datetime.now()
            if expiry_datetime < current_datetime:
                with psycopg2.connect(settings.database_url) as conn:
                    update_user_status(conn, telegram_id, "expired")
                logger.info("Подписка истекла")
                return SubscriptionCheckResponse(
                    status="expired",
                    display_text="Подписка истекла\nВыберите план для продления",
                    config_url=None
                )
            timeleft = format_time_left(user_info.expiry)
            jwt_token = user_info.jwt_token
            config_url = f"https://nirovpn.com/api/sub/{jwt_token}"
            logger.info("Подписка активна")
            return SubscriptionCheckResponse(
                status="active",
                display_text=f"Подписка активна\n{timeleft}",
                config_url=config_url
            )
        elif user_info.status == "expired":
            logger.info("Подписка истекла")
            return SubscriptionCheckResponse(
                status="expired",
                display_text="Подписка истекла\nВыберите план для продления",
                config_url=None
            )
        logger.warning("something went wrong")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="something went wrong")
    except Exception as e:
        logger.error(f"Error in check_subscription: {e}")
        raise e
