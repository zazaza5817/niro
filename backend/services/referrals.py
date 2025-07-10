import logging
import random
import string
import json
import psycopg2 # type: ignore
from psycopg2.extras import RealDictCursor # type: ignore
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from fastapi import HTTPException, status # type: ignore
from config import settings
from models.referral import CreateReferralRequest, ReferralResponse, AddReferralPlanRequest, ReferralPlanResponse

logger = logging.getLogger("my_app")

class ReferralService:
    """Сервис для работы с реферальными кодами и скидками"""

    @staticmethod
    def get_db_connection():
        """Создаёт соединение с PostgreSQL базой данных."""
        try:
            connection = psycopg2.connect(settings.database_url)
            return connection
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail="Database connection failed")


    def generate_referral_code(length: int = 8) -> str:
        """Генерирует уникальный реферальный код"""
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))


    async def create_referral_code(request: CreateReferralRequest) -> ReferralResponse:
        """Создает новый реферальный код"""
        conn = None
        try:
            conn = ReferralService.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Генерируем уникальный код
            max_attempts = 10
            for _ in range(max_attempts):
                code = ReferralService.generate_referral_code()
                
                # Проверяем, что код уникален
                cursor.execute("SELECT id FROM referral_codes WHERE code = %s", (code,))
                if not cursor.fetchone():
                    break
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Не удалось сгенерировать уникальный код")
            
            # Вычисляем дату истечения
            expires_at = None
            if request.expires_days:
                expires_at = datetime.now() + timedelta(days=request.expires_days)
            
            # Сохраняем в БД
            cursor.execute("""
                INSERT INTO referral_codes (code, max_uses, expires_at)
                VALUES (%s, %s, %s)
                RETURNING id, created_at
            """, (code, request.max_uses, expires_at))
            
            result = cursor.fetchone()
            conn.commit()
            
            logger.info(f"Created referral code: {code} with ID: {result['id']}")
            
            # Формируем ссылку для Telegram бота
            referral_link = f"https://t.me/{settings.telegram_bot_username}?start={code}"
            
            return ReferralResponse(
                id=result['id'],
                code=code,
                referral_link=referral_link,
                max_uses=request.max_uses,
                expires_at=expires_at
            )
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error creating referral code: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Ошибка создания реферального кода")
        finally:
            if conn:
                conn.close()


    async def apply_referral_code(user_tg_id: int, referral_code: str) -> bool:
        """Применяет реферальный код для пользователя"""
        conn = None
        try:
            conn = ReferralService.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Проверяем код
            cursor.execute("""
                SELECT * FROM referral_codes 
                WHERE code = %s AND is_active = TRUE
            """, (referral_code,))
            
            ref_code = cursor.fetchone()
            if not ref_code:
                logger.warning(f"Invalid or inactive referral code: {referral_code}")
                return False
            
            # Проверяем срок действия
            if ref_code['expires_at'] and ref_code['expires_at'] < datetime.now():
                logger.warning(f"Expired referral code: {referral_code}")
                return False
            
            # Проверяем лимит использований
            if ref_code['max_uses'] and ref_code['current_uses'] >= ref_code['max_uses']:
                logger.warning(f"Referral code usage limit exceeded: {referral_code}")
                return False
            
            # Проверяем, не использовал ли уже этот пользователь этот код
            cursor.execute("""
                SELECT id FROM referral_usage 
                WHERE referral_code_id = %s AND user_tg_id = %s
            """, (ref_code['id'], user_tg_id))
            
            if cursor.fetchone():
                logger.warning(f"User {user_tg_id} already used referral code: {referral_code}")
                return False
            
            cursor.execute("""
                SELECT tg_id FROM users WHERE tg_id = %s
            """, (user_tg_id,))
            
            existing_user = cursor.fetchone()
            if not existing_user:
                # Создаём пользователя с базовыми данными
                logger.info(f"Creating new user record for tg_id: {user_tg_id} (referral code application)")
                cursor.execute("""
                    INSERT INTO users (tg_id, status, expiry, connection_link, email, id, server_id, jwt_token)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_tg_id,
                    'inactive',  # Статус неактивный до покупки подписки
                    None,  # Минимальная дата истечения
                    None,  # Пустая ссылка подключения
                    None,  # Пустой email
                    None,  # Пустой id клиента
                    None,  # Пустой server_id
                    None   # Пустой JWT token
                ))
                logger.info(f"Successfully created user record for tg_id: {user_tg_id}")
            
            # Записываем использование реферального кода
            cursor.execute("""
                INSERT INTO referral_usage (referral_code_id, user_tg_id)
                VALUES (%s, %s)
            """, (ref_code['id'], user_tg_id))
            
            # Увеличиваем счетчик использований
            cursor.execute("""
                UPDATE referral_codes SET current_uses = current_uses + 1
                WHERE id = %s
            """, (ref_code['id'],))
            
            conn.commit()
            
            logger.info(f"Successfully applied referral code {referral_code} for user {user_tg_id}")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error applying referral code: {e}")
            return False
        finally:
            if conn:
                conn.close()

    async def deactivate_referral_code(referral_code: str) -> bool:
        """Деактивирует реферальный код (все скидки по этому коду перестают действовать)"""
        conn = None
        try:
            conn = ReferralService.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                UPDATE referral_codes 
                SET is_active = FALSE 
                WHERE code = %s
            """, (referral_code,))
            
            result = cursor.fetchone()
            if not result:
                logger.warning(f"Referral code not found: {referral_code}")
                return False
            
            conn.commit()
            
            logger.info(f"Deactivated referral code: {referral_code}")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
                conn.close()
            logger.error(f"Error deactivating referral code: {e}")
            return False

    @staticmethod
    def load_default_plans() -> Dict:
        """Загружает дефолтные планы из файла plans.json"""
        try:
            with open('settings/plans.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading default plans: {e}")
            return {}

    @staticmethod
    async def add_referral_plan(request: AddReferralPlanRequest) -> Optional[int]:
        """Добавляет план к реферальному коду"""
        conn = None
        try:
            conn = ReferralService.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Проверяем, что реферальный код существует
            cursor.execute("SELECT id FROM referral_codes WHERE id = %s", (request.referral_code_id,))
            if not cursor.fetchone():
                logger.error(f"Referral code with id {request.referral_code_id} not found")
                return None
            
            if request.is_default:
                # Для дефолтного плана проверяем, что payload существует
                default_plans = ReferralService.load_default_plans()
                if request.default_plan_payload not in default_plans:
                    logger.error(f"Default plan payload {request.default_plan_payload} not found")
                    return None
                
                # Добавляем дефолтный план
                cursor.execute("""
                    INSERT INTO referral_plans (
                        referral_code_id, is_default, default_plan_payload, discount_percent
                    ) VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (request.referral_code_id, True, request.default_plan_payload, request.discount_percent))
            else:
                # Добавляем кастомный план
                cursor.execute("""
                    INSERT INTO referral_plans (
                        referral_code_id, is_default, discount_percent,
                        price, duration, title, description, label, payload, name, price_per_month
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    request.referral_code_id, False, request.discount_percent,
                    request.price, request.duration, request.title, request.description,
                    request.label, request.payload, request.name, request.price_per_month
                ))
            
            result = cursor.fetchone()
            plan_id = result['id']
            conn.commit()
            
            logger.info(f"Added referral plan {plan_id} to referral code {request.referral_code_id}")
            return plan_id
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error adding referral plan: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    async def delete_referral_plan(plan_id: int) -> bool:
        """Удаляет план реферального кода"""
        conn = None
        try:
            conn = ReferralService.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("DELETE FROM referral_plans WHERE id = %s", (plan_id,))
            rows_affected = cursor.rowcount
            conn.commit()
            
            if rows_affected > 0:
                logger.info(f"Deleted referral plan {plan_id}")
                return True
            else:
                logger.warning(f"Referral plan {plan_id} not found")
                return False
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error deleting referral plan: {e}")
            return False
        finally:
            if conn:
                conn.close()


    @staticmethod
    async def get_referral_plans_by_code(referral_code: str) -> List[ReferralPlanResponse]:
        """Получает планы по реферальному коду"""
        conn = None
        try:
            conn = ReferralService.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT rp.*, rc.code
                FROM referral_plans rp
                JOIN referral_codes rc ON rp.referral_code_id = rc.id
                WHERE rc.code = %s AND rc.is_active = TRUE
                    AND (rc.expires_at IS NULL OR rc.expires_at > CURRENT_TIMESTAMP)
                ORDER BY rp.created_at
            """, (referral_code,))
            
            plans = cursor.fetchall()
            default_plans = ReferralService.load_default_plans()
            
            result = []
            for plan in plans:
                if plan['is_default'] and plan['default_plan_payload'] in default_plans:
                    # Берем данные из дефолтного плана
                    default_plan = default_plans[plan['default_plan_payload']]
                    result.append(ReferralPlanResponse(
                        id=plan['id'],
                        referral_code_id=plan['referral_code_id'],
                        is_default=True,
                        discount_percent=plan['discount_percent'],
                        price=default_plan['price'],
                        duration=default_plan['duration'],
                        title=default_plan['title'],
                        description=default_plan['description'],
                        label=default_plan['label'],
                        payload=default_plan['payload'],
                        name=default_plan['name'],
                        price_per_month=default_plan['price_per_month'],
                        created_at=plan['created_at']
                    ))
                elif not plan['is_default']:
                    # Используем кастомные данные
                    result.append(ReferralPlanResponse(
                        id=plan['id'],
                        referral_code_id=plan['referral_code_id'],
                        is_default=False,
                        discount_percent=plan['discount_percent'],
                        price=plan['price'],
                        duration=plan['duration'],
                        title=plan['title'],
                        description=plan['description'],
                        label=plan['label'],
                        payload=plan['payload'],
                        name=plan['name'],
                        price_per_month=plan['price_per_month'],
                        created_at=plan['created_at']
                    ))
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting referral plans by code: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    async def get_user_referral_plans(user_tg_id: int) -> List[ReferralPlanResponse]:
        """Получает все реферальные планы для пользователя (из всех его примененных кодов)"""
        conn = None
        try:
            conn = ReferralService.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Получаем все планы из реферальных кодов, которые применил пользователь
            cursor.execute("""
                SELECT DISTINCT rp.*
                FROM referral_usage ru
                JOIN referral_codes rc ON ru.referral_code_id = rc.id
                JOIN referral_plans rp ON rc.id = rp.referral_code_id
                WHERE ru.user_tg_id = %s 
                    AND rc.is_active = TRUE
                    AND (rc.expires_at IS NULL OR rc.expires_at > CURRENT_TIMESTAMP)
                ORDER BY rp.created_at
            """, (user_tg_id,))
            
            plans = cursor.fetchall()
            default_plans = ReferralService.load_default_plans()
            
            result = []
            for plan in plans:
                if plan['is_default'] and plan['default_plan_payload'] in default_plans:
                    # Берем данные из дефолтного плана
                    default_plan = default_plans[plan['default_plan_payload']]
                    result.append(ReferralPlanResponse(
                        id=plan['id'],
                        referral_code_id=plan['referral_code_id'],
                        is_default=True,
                        discount_percent=plan['discount_percent'],
                        price=default_plan['price'],
                        duration=default_plan['duration'],
                        title=default_plan['title'],
                        description=default_plan['description'],
                        label=default_plan['label'],
                        payload=default_plan['payload'],
                        name=default_plan['name'],
                        price_per_month=default_plan['price_per_month'],
                        created_at=plan['created_at']
                    ))
                elif not plan['is_default']:
                    # Используем кастомные данные
                    result.append(ReferralPlanResponse(
                        id=plan['id'],
                        referral_code_id=plan['referral_code_id'],
                        is_default=False,
                        discount_percent=plan['discount_percent'],
                        price=plan['price'],
                        duration=plan['duration'],
                        title=plan['title'],
                        description=plan['description'],
                        label=plan['label'],
                        payload=plan['payload'],
                        name=plan['name'],
                        price_per_month=plan['price_per_month'],
                        created_at=plan['created_at']
                    ))
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting user referral plans: {e}")
            return []
        finally:
            if conn:
                conn.close()
