import logging
from typing import List, Optional, Dict
from config import settings
from services.referrals import ReferralService
from models.pricing import PlanWithDiscount, PriceInfo

logger = logging.getLogger("my_app")


class PricingService:
    """Сервис для расчета цен со скидками"""
    
    @staticmethod
    async def get_plans_with_discount(user_tg_id: Optional[int] = None) -> List[PlanWithDiscount]:
        """Получает список планов с учетом скидки пользователя"""
        """Нужен используется для get_plans"""
        
        # Если передан user_tg_id, пытаемся получить реферальные планы пользователя
        if user_tg_id:
            logger.info(f"Getting referral plans for user {user_tg_id}")
            referral_plans = await ReferralService.get_user_referral_plans(user_tg_id)
            
            # Если найдены реферальные планы, возвращаем их
            if referral_plans:
                result = []
                for plan in referral_plans:
                    result.append(PlanWithDiscount(
                        id=plan.payload,
                        name=plan.name,
                        price_per_month=plan.price_per_month,
                        original_price=None,
                        discount_percent=plan.discount_percent if plan.discount_percent > 0 else None
                    ))
                logger.info(f"Found {len(result)} referral plans for user {user_tg_id}")
                return result
            else:
                logger.info(f"No referral plans found for user {user_tg_id}, returning default plans")
        
        # Если user_tg_id не передан или не найдены реферальные планы, возвращаем дефолтные планы
        logger.info("Getting default plans")
        plans_list = []
        
        for key, plan in settings.plans.items():
            original_price = plan["price_per_month"]
            
            plans_list.append(PlanWithDiscount(
                id=key,
                name=plan["name"],
                price_per_month=plan.price_per_month,
                original_price=None,
                discount_percent=None
            ))
        
        return plans_list
