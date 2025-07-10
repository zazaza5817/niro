import telebot # type: ignore
from telebot.types import LabeledPrice # type: ignore
from fastapi import HTTPException, status # type: ignore
import logging
from config import settings
from services.users import UserService
from services.pricing import PricingService
from services.referrals import ReferralService

logger = logging.getLogger("my_app")


class PaymentService:
    """Сервис для работы с платежами"""

    @staticmethod
    async def select_plan(selected_plan: str, auth_data: str):
        if not UserService.check_telegram_auth(auth_data, settings.telegram_bot_token):
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram auth data")
        
        auth_data = UserService.parse_telegram_data(auth_data)
        tg_id = auth_data['user']['id']

        # Получаем реферальные планы пользователя для поиска кастомных данных
        referral_plans = await ReferralService.get_user_referral_plans(tg_id)
        matching_plan = None
        for plan in referral_plans:
            if plan.payload == selected_plan:
                matching_plan = plan
                break
        
        if matching_plan:
            # Используем данные из реферального плана
            plan_data = {
                'title': matching_plan.title,
                'description': matching_plan.description,
                'label': matching_plan.label,
                'payload': matching_plan.payload,
                'price': matching_plan.price
            }
            logger.info(f"Using referral plan data for user {tg_id}, plan {selected_plan}")
        else:
            # Используем дефолтные данные из settings
            plan_data = settings.plans_invoice.get(selected_plan)
            if not plan_data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan selected")
            logger.info(f"Using default plan data for user {tg_id}, plan {selected_plan}")
        
        PaymentService.send_invoice(tg_id, plan_data, settings.telegram_bot_token)

    @staticmethod
    def send_invoice(tg_id: int, plan: dict, telegram_bot_token: str):
        prices = [LabeledPrice(label=plan['label'], amount=plan['price'])]
        bot = telebot.TeleBot(telegram_bot_token)
        
        logger.info(f"Sending invoice to {tg_id} - price: {plan['price']}")
        
        bot.send_message(tg_id, "Приобрести звезды вы можете непосредственно при оплате подписки (через интерфейс telegram) или с помощью @PremiumBot")
        bot.send_invoice(
            tg_id,
            title=plan['title'],
            description=plan['description'],
            invoice_payload=plan['payload'],
            provider_token=None,
            currency="XTR",
            prices=prices,
            is_flexible=False
        )
