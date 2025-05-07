# backend/config.py
from pydantic_settings import BaseSettings # type: ignore
from typing import Dict, Optional
import os
import json
from dotenv import load_dotenv # type: ignore
import logging

logger = logging.getLogger("my_app")

load_dotenv()

plans_json = {}
plans_path = '/app/data/plans.json'
try:
    if os.path.exists(plans_path):
        with open(plans_path, 'r') as file:
            plans_json = json.load(file)
            logger.info(f"Планы успешно загружены из {plans_path}")
except Exception as e:
    logger.error(f"Ошибка при загрузке файла планов: {str(e)}")
    plans_json = {}

class Settings(BaseSettings):
    telegram_bot_token: str
    database_url: str
    secret_key: str
    plans: Dict
    plans_invoice: Dict
    debug: Optional[bool] = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
        @classmethod
        def parse_obj(cls, obj):
            if "plans" in obj:
                obj["plans"] = {k: {"name": v["name"], "price_per_month": v["price_per_month"]}
                                  for k, v in obj["plans"].items()}
            if "plans_invoice" in obj:
                obj["plans_invoice"] = {k: {"price": v["price"],
                                             "duration": v["duration"],
                                             "title": v["title"],
                                             "description": v["description"],
                                             "label": v["label"],
                                             "payload": v["payload"]
                                            }
                                   for k, v in obj["plans_invoice"].items()}

            return super().parse_obj(obj)
    
plans_data = {}
plans_invoice_data = {}

if plans_json:
    for key, plan in plans_json.items():
        plans_data[key] = {
            "name": plan["name"],
            "price_per_month": plan["price_per_month"]
        }
        
        plans_invoice_data[key] = {
            "price": plan["price"],
            "duration": plan["duration"],
            "title": plan["title"],
            "description": plan["description"],
            "label": plan["label"],
            "payload": plan["payload"]
        }


settings = Settings(
    telegram_bot_token = os.getenv('TG_TOKEN'),
    database_url = os.getenv('DATABASE_URL'),
    secret_key = os.getenv('JWT_SECRET_KEY'),
    debug = os.getenv('DEBUG', '0').lower() in ('1', 'true', 't', 'yes', 'y'),
    plans = plans_data,
    plans_invoice = plans_invoice_data
)
