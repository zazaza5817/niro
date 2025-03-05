import telebot
from telebot.types import LabeledPrice
from fastapi import HTTPException, status
from config import settings
import services.users as user_service


async def select_plan(selected_plan: str, auth_data: str):
    if not user_service.check_telegram_auth(auth_data, settings.telegram_bot_token):
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Telegram auth data")

    plan = settings.plans_invoice.get(selected_plan)
    if not plan:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan selected")

    auth_data = user_service.parse_telegram_data(auth_data)
    tg_id = auth_data['user']['id']

    send_invoice(tg_id, plan, settings.telegram_bot_token)


def send_invoice(tg_id: int, plan: dict, telegram_bot_token: str):
    prices = [LabeledPrice(label=plan['label'], amount=plan['price'])]
    bot = telebot.TeleBot(telegram_bot_token)
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