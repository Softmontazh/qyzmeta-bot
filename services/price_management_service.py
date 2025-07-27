# -*- coding: utf-8 -*-
# services/price_management_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional
from datetime import datetime

from database.models.orm_subscription_price import (
    orm_get_active_prices,
    orm_get_price_by_tier,
    orm_get_price_history,
    orm_create_price,
    orm_update_price,
    orm_get_prices_summary,
    orm_initialize_default_prices
)
from database.enums.subscription_enums import SubscriptionTier


class PriceManagementService:
    """Сервис для управления ценами подписок"""
    
    @staticmethod
    async def get_current_prices(session: AsyncSession) -> Dict[str, Dict]:
        """Получить текущие активные цены всех тарифов"""
        active_prices = await orm_get_active_prices(session)
        
        prices_dict = {}
        for price in active_prices:
            prices_dict[price.tier] = price.to_dict()
        
        # Добавляем отсутствующие тарифы с ценой 0
        for tier in SubscriptionTier:
            if tier.value not in prices_dict:
                prices_dict[tier.value] = {
                    "tier": tier.value,
                    "tier_display": tier.get_russian_name(),
                    "price": 0,
                    "formatted_price": "Не установлено",
                    "is_active": False
                }
        
        return prices_dict
    
    @staticmethod
    async def get_tier_price(session: AsyncSession, tier: SubscriptionTier) -> int:
        """Получить цену конкретного тарифа"""
        price_obj = await orm_get_price_by_tier(session, tier)
        return price_obj.price if price_obj else 0
    
    @staticmethod
    async def update_tier_price(
        session: AsyncSession,
        tier: SubscriptionTier,
        new_price: int,
        updated_by: int,
        notes: Optional[str] = None
    ) -> Dict:
        """Обновить цену тарифа"""
        
        # Валидация цены
        if new_price < 0:
            return {
                "success": False,
                "error": "Цена не может быть отрицательной"
            }
        
        # Для FREE тарифа цена всегда должна быть 0
        if tier == SubscriptionTier.FREE and new_price != 0:
            return {
                "success": False,
                "error": "Бесплатный тариф не может иметь цену больше 0"
            }
        
        try:
            updated_price = await orm_update_price(
                session=session,
                tier=tier,
                new_price=new_price,
                updated_by=updated_by,
                notes=notes
            )
            
            return {
                "success": True,
                "price": updated_price.to_dict(),
                "message": f"Цена тарифа {tier.get_russian_name()} обновлена на {new_price:,} ₸"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка при обновлении цены: {str(e)}"
            }
    
    @staticmethod
    async def get_price_history(
        session: AsyncSession,
        tier: Optional[SubscriptionTier] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Получить историю изменений цен"""
        history = await orm_get_price_history(session, tier, limit)
        return [price.to_dict() for price in history]
    
    @staticmethod
    async def get_management_summary(session: AsyncSession) -> Dict:
        """Получить сводку для управления ценами"""
        summary = await orm_get_prices_summary(session)
        current_prices = await PriceManagementService.get_current_prices(session)
        
        # Подсчитываем общую статистику
        total_revenue_potential = 0
        configured_tiers = 0
        
        for tier_data in current_prices.values():
            if tier_data["is_active"] and tier_data["price"] > 0:
                total_revenue_potential += tier_data["price"]
                configured_tiers += 1
        
        return {
            "current_prices": current_prices,
            "statistics": {
                "total_tiers": len(SubscriptionTier),
                "configured_tiers": configured_tiers,
                "total_changes": summary["total_changes"],
                "last_update": summary["last_update"],
                "revenue_potential": total_revenue_potential
            }
        }
    
    @staticmethod
    async def initialize_prices_if_needed(session: AsyncSession, created_by: int = 0) -> bool:
        """Инициализировать цены если они не настроены"""
        current_prices = await orm_get_active_prices(session)
        
        if not current_prices:
            await orm_initialize_default_prices(session, created_by)
            return True
        
        return False
    
    @staticmethod
    def validate_price_input(price_str: str) -> tuple[bool, int, str]:
        """Валидировать ввод цены"""
        try:
            # Убираем пробелы и запятые
            clean_price = price_str.replace(" ", "").replace(",", "").replace("₸", "")
            
            price = int(clean_price)
            
            if price < 0:
                return False, 0, "Цена не может быть отрицательной"
            
            if price > 100000:
                return False, 0, "Цена слишком высокая (максимум 100,000 ₸)"
            
            return True, price, ""
            
        except ValueError:
            return False, 0, "Введите корректное число"
    
    @staticmethod
    def format_price_change_message(
        tier: SubscriptionTier,
        old_price: int,
        new_price: int,
        updated_by: int
    ) -> str:
        """Форматировать сообщение об изменении цены"""
        tier_name = tier.get_russian_name()
        
        if old_price == 0:
            return f"💰 Установлена цена для тарифа <b>{tier_name}</b>: {new_price:,} ₸/мес"
        elif new_price == 0:
            return f"💰 Отменена цена для тарифа <b>{tier_name}</b> (было: {old_price:,} ₸/мес)"
        else:
            change = "📈" if new_price > old_price else "📉"
            return f"{change} Изменена цена тарифа <b>{tier_name}</b>: {old_price:,} → {new_price:,} ₸/мес"
