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
from psycopg2.extras import RealDictCursor # type: ignore
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
    except Exception as e:
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
    except Exception as e:
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


def get_db_connection():
    """Создаёт соединение с PostgreSQL базой данных."""
    try:
        conn = psycopg2.connect(settings.database_url)
        return conn
    except Exception as e:
        logger.error(f"Ошибка при подключении к базе данных: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail="Ошибка подключения к базе данных")


def get_user_by_id(conn, telegram_id: int):
    """Получает информацию о пользователе из PostgreSQL."""
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT status, expiry, jwt_token, connection_link, server_id 
            FROM users WHERE tg_id = %s
        """, (telegram_id,))
        user_info = cur.fetchone()
        cur.close()
        
        if user_info:
            return User(
                tg_id=telegram_id, 
                status=user_info["status"], 
                expiry=user_info["expiry"], 
                jwt_token=user_info["jwt_token"], 
                connection_link=user_info["connection_link"], 
                server_id=user_info["server_id"]
            )
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении пользователя: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Ошибка базы данных: {str(e)}")


def update_user_status(conn, telegram_id: int, status: str):
    """Обновляет статус пользователя в PostgreSQL."""
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET status = %s WHERE tg_id = %s", (status, telegram_id))
        conn.commit()
        cur.close()
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса: {e}")
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Ошибка обновления статуса: {str(e)}")


def generate_jwt_token(user_id: int):
    payload = {
        "user_id": user_id,
    }
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    return token


async def get_current_user(token: str):
    try:
        logger.info(f"get_current_user called with token: {token}")
        payload = jwt.decode(token.credentials, settings.secret_key, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        conn = get_db_connection()
        try:
            user = get_user_by_id(conn, user_id)
        finally:
            conn.close()

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
        
        conn = get_db_connection()
        try:
            user_info = get_user_by_id(conn, user_id)
        finally:
            conn.close()

        if not user_info:
            logger.warning(f"User not found for tg_id: {user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        links = [user_info.connection_link]
        html_content = "\n".join([f'{link}' for link in links])
        
        date_format = "%Y-%m-%d %H:%M"
        date_object = datetime.strptime(user_info.expiry, date_format)
        unix_time = int(date_object.timestamp())

        headers = {
            "Server": 'nginx',
            "Subscription-Userinfo": f'expire={unix_time}',
            "profile-title": 'niro vpn subscription',
            "profile-web-page-url": 'https://niro.com',
            "profile-update-interval": '1'
        }
        
        logger.info(f"Returning subscription data for user: {user_id}")
        return html_content, headers
    except Exception as e:
        logger.error(f"Error in get_subscription: {e}")
        raise e


def _handle_telegram_auth(auth_data: str):
    if not check_telegram_auth(auth_data, settings.telegram_bot_token):
        logger.warning("Invalid Telegram auth data")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ошибка авторизации")

    data = parse_telegram_data(auth_data)
    if not data or 'user' not in data:
        logger.error("Failed to parse Telegram data or user not found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ошибка аутентификации")
    return data['user']['id']


def _get_user_subscription_info(conn, telegram_id: int):
    user_info = get_user_by_id(conn, telegram_id)
    logger.info(f"User info retrieved: {user_info}")
    if not user_info:
        logger.info(f"Subscription inactive for user {telegram_id}")
        return SubscriptionCheckResponse(status="inactive", display_text="Подписка не активна", config_url=None)
    return user_info


def _handle_active_subscription(conn, user_info: User, telegram_id: int):
    try:
        expiry_datetime = datetime.strptime(user_info.expiry, '%Y-%m-%d %H:%M')
        current_datetime = datetime.now()

        if expiry_datetime < current_datetime:
            update_user_status(conn, telegram_id, "expired")
            logger.info(f"Subscription expired for user {telegram_id}")
            return SubscriptionCheckResponse(
                status="expired",
                display_text="Подписка истекла\nВыберите план для продления",
                config_url=None
            )

        timeleft = format_time_left(user_info.expiry)
        jwt_token = user_info.jwt_token
        config_url = f"https://nirovpn.com/api/sub/{jwt_token}"

        logger.info(f"Subscription active for user {telegram_id}")
        return SubscriptionCheckResponse(
            status="active",
            display_text=f"Подписка активна\n{timeleft}",
            config_url=config_url
        )
    except ValueError as e:
        logger.error(f"Error parsing date format: {e}")
        return SubscriptionCheckResponse(
            status="error",
            display_text="Ошибка формата даты",
            config_url=None
        )


def _handle_expired_subscription(telegram_id: int):
    logger.info(f"Subscription expired for user {telegram_id}")
    return SubscriptionCheckResponse(
        status="expired",
        display_text="Подписка истекла\nВыберите план для продления",
        config_url=None
    )


def _handle_unknown_subscription_status(telegram_id: int, user_status: str):
    logger.warning(f"Unexpected status for user {telegram_id}: {user_status}")
    return SubscriptionCheckResponse(
        status="error",
        display_text="Неизвестный статус подписки",
        config_url=None
    )


async def check_subscription(auth_data: str) -> SubscriptionCheckResponse:
    logger.info(f"check_subscription called with auth_data: {auth_data}")
    conn = None
    try:
        telegram_id = _handle_telegram_auth(auth_data)
        logger.info(f"Checking subscription for user with telegram_id: {telegram_id}")

        conn = get_db_connection()
        logger.info("Database connection successful")

        user_info = _get_user_subscription_info(conn, telegram_id)

        if isinstance(user_info, SubscriptionCheckResponse):
            return user_info
        if user_info.status == "active":
            return _handle_active_subscription(conn, user_info, telegram_id)
        elif user_info.status == "expired":
            return _handle_expired_subscription(telegram_id)
        else:
            return _handle_unknown_subscription_status(telegram_id, user_info.status)

    except HTTPException as http_exc:
        logger.error(f"HTTP exception in check_subscription: {http_exc.detail}")
        if http_exc.detail == "Ошибка аутентификации":
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                                detail="Ошибка аутентификации")
        raise http_exc
    except Exception as e:
        logger.error(f"Error processing user data: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Ошибка обработки данных")
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")