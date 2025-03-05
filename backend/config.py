from pydantic_settings import BaseSettings # type: ignore
from typing import Dict
import os

class Settings(BaseSettings):
    telegram_bot_token: str = os.environ.get("TG_TOKEN")
    database_url: str = os.environ.get("DATABASE_URL")
    secret_key: str = os.environ.get("JWT_SECRET_KEY") 
    plans: Dict = {
        "6month": {
            "name": "6 месяцев",
            "price_per_month": 115
        },
        "3month": {
            "name": "3 месяца",
            "price_per_month": 125
        },
        "1month": {
            "name": "1 месяц",
            "price_per_month": 150
        }
    }
    plans_invoice: Dict = {
        "1month": {
            "price": 150,
            "duration": 30,
            "title": "Подписка на месяц",
            "description": "Действует 30 дней",
            "label": "Подписка",
            "payload": "1month"
        },
        "3month": {
            "price": 375,
            "duration": 90,
            "title": "Подписка на 3 месяца",
            "description": "Действует 90 дней",
            "label": "Подписка",
            "payload": "3month"
        },
        "6month": {
            "price": 690,
            "duration": 180,
            "title": "Подписка на 6 месяцев",
            "description": "Действует 180 дней",
            "label": "Подписка",
            "payload": "6month"
        }
    }
    
    class Config:
        env_file = ".env"

settings = Settings()