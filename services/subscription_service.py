# -*- coding: utf-8 -*-
# services/subscription_service.py

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.orm_user_subscription import (
    orm_get_user_subscription,
    orm_create_user_subscription,
    orm_check_address_limit,
    orm_can_register_address,
    orm_update_subscription_tier,
    orm_get_subscription_statistics,
    orm_search_user_subscription,
    orm_expire_overdue_subscriptions,
    orm_get_expiring_subscriptions,
    orm_get_all_subscriptions
)
from database.enums.subscription_enums import SubscriptionTier, SubscriptionStatus


class SubscriptionService:
    """Сервис для управления подписками пользователей"""
    
    @staticmethod
    async def get_user_subscription_info(
        session: AsyncSession, 
        user_id: int
    ) -> Dict:
        """Получить полную информацию о подписке пользователя"""
        subscription = await orm_get_user_subscription(session, user_id)
        current_count, max_allowed = await orm_check_address_limit(session, user_id)
        
        if not subscription:
            # Пользователь на бесплатном тарифе
            return {
                "has_subscription": False,
                "tier": SubscriptionTier.FREE,
                "tier_name": SubscriptionTier.FREE.get_russian_name(),
                "status": "active",
                "current_addresses": current_count,
                "max_addresses": max_allowed,
                "can_add_address": current_count < max_allowed,
                "days_left": None,
                "expires_at": None,
                "is_expiring_soon": False,
                "monthly_price": 0,
                "payment_info": None,
                "started_at": None,
                "notes": None
            }
        
        return {
            "has_subscription": True,
            "tier": subscription.tier,
            "tier_name": subscription.get_tier_display(),
            "status": subscription.get_status_display(),
            "current_addresses": current_count,
            "max_addresses": max_allowed,
            "can_add_address": current_count < max_allowed,
            "days_left": subscription.days_left,
            "expires_at": subscription.expires_at,
            "is_expiring_soon": subscription.is_expiring_soon,
            "monthly_price": subscription.tier.get_monthly_price(),
            "payment_info": subscription.payment_info,
            "started_at": subscription.started_at,
            "notes": subscription.notes
        }
    
    @staticmethod
    async def check_can_register_address(
        session: AsyncSession, 
        user_id: int
    ) -> Tuple[bool, Dict]:
        """Проверить возможность регистрации нового адреса"""
        can_register = await orm_can_register_address(session, user_id)
        subscription_info = await SubscriptionService.get_user_subscription_info(
            session, user_id
        )
        
        return can_register, subscription_info
    
    @staticmethod
    async def upgrade_user_subscription(
        session: AsyncSession,
        user_id: int,
        new_tier: SubscriptionTier,
        duration_days: int = 30,
        payment_info: Optional[str] = None,
        admin_notes: Optional[str] = None
    ) -> Dict:
        """Обновить подписку пользователя"""
        
        # Создаем заметку об обновлении
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        notes = f"[{timestamp}] Тариф обновлен до {new_tier.get_russian_name()}"
        if admin_notes:
            notes += f". Заметка: {admin_notes}"
        
        subscription = await orm_update_subscription_tier(
            session=session,
            user_id=user_id,
            new_tier=new_tier,
            duration_days=duration_days,
            payment_info=payment_info,
            notes=notes
        )
        
        return {
            "success": True,
            "subscription_id": subscription.id,
            "tier": subscription.tier,
            "tier_name": subscription.get_tier_display(),
            "expires_at": subscription.expires_at,
            "max_addresses": subscription.max_addresses
        }
    
    @staticmethod
    async def get_admin_statistics(session: AsyncSession) -> Dict:
        """Получить статистику для админ панели"""
        stats = await orm_get_subscription_statistics(session)
        expiring_soon = await orm_get_expiring_subscriptions(session, 7)
        
        # Форматируем статистику для отображения
        formatted_stats = {
            "summary": {
                "total_active": stats["total_active"],
                "total_expired": stats["total_expired"],
                "total_cancelled": stats["total_cancelled"],
                "expiring_soon": stats["expiring_soon"],
                "monthly_revenue": stats["monthly_revenue"]
            },
            "tier_breakdown": []
        }
        
        # Детализация по тарифам
        for tier_value, tier_stats in stats["tier_stats"].items():
            formatted_stats["tier_breakdown"].append({
                "tier": tier_value,
                "name": tier_stats["name"],
                "count": tier_stats["count"],
                "monthly_revenue": tier_stats["monthly_revenue"]
            })
        
        # Список истекающих подписок
        expiring_list = []
        for sub in expiring_soon:
            expiring_list.append({
                "user_id": sub.user_id,
                "tier": sub.get_tier_display(),
                "expires_at": sub.expires_at,
                "days_left": sub.days_left
            })
        
        formatted_stats["expiring_subscriptions"] = expiring_list
        
        return formatted_stats
    
    @staticmethod
    async def search_subscriptions(
        session: AsyncSession,
        search_query: str
    ) -> List[Dict]:
        """Поиск подписок для админ панели"""
        subscriptions = await orm_search_user_subscription(session, search_query)
        
        result = []
        for sub in subscriptions:
            current_count, max_allowed = await orm_check_address_limit(
                session, sub.user_id
            )
            
            result.append({
                "id": sub.id,
                "user_id": sub.user_id,
                "tier": sub.get_tier_display(),
                "status": sub.get_status_display(),
                "current_addresses": current_count,
                "max_addresses": max_allowed,
                "started_at": sub.started_at,
                "expires_at": sub.expires_at,
                "days_left": sub.days_left,
                "payment_info": sub.payment_info
            })
        
        return result
    
    @staticmethod
    async def expire_overdue_subscriptions(session: AsyncSession) -> int:
        """Автоматически истечь просроченные подписки"""
        return await orm_expire_overdue_subscriptions(session)
    
    @staticmethod
    def get_upgrade_suggestions(current_tier: SubscriptionTier) -> List[Dict]:
        """Получить предложения по апгрейду тарифа"""
        suggestions = []
        
        # Определяем доступные тарифы для апгрейда
        current_limit = current_tier.get_address_limit()
        
        for tier in SubscriptionTier:
            if tier.get_address_limit() > current_limit:
                suggestions.append({
                    "tier": tier,
                    "name": tier.get_russian_name(),
                    "address_limit": tier.get_address_limit(),
                    "monthly_price": tier.get_monthly_price(),
                    "benefits": SubscriptionService._get_tier_benefits(tier)
                })
        
        return suggestions
    
    @staticmethod
    def _get_tier_benefits(tier: SubscriptionTier) -> List[str]:
        """Получить список преимуществ тарифа"""
        benefits = {
            SubscriptionTier.FREE: [
                "1 адрес для регистрации",
                "Базовые уведомления"
            ],
            SubscriptionTier.BASIC: [
                "До 3 адресов",
                "Приоритетные уведомления",
                "Поддержка в чате"
            ],
            SubscriptionTier.PREMIUM: [
                "До 10 адресов",
                "Эксклюзивные предложения",
                "Персональный менеджер",
                "Аналитика по объектам"
            ],
            SubscriptionTier.VIP: [
                "Неограниченные адреса",
                "VIP статус",
                "Приоритет во всех сделках",
                "Персональный консультант",
                "Ранний доступ к новым ЖК"
            ]
        }
        
        return benefits.get(tier, [])
    
    @staticmethod
    def format_subscription_message(subscription_info: Dict) -> str:
        """Форматировать информацию о подписке для отображения"""
        info = subscription_info
        
        message = f"📋 <b>Ваша подписка</b>\n\n"
        message += f"🎯 <b>Тариф:</b> {info['tier_name']}\n"
        message += f"🏠 <b>Адреса:</b> {info['current_addresses']}/{info['max_addresses']}\n"
        
        if info['has_subscription'] and info['expires_at']:
            if info['days_left']:
                message += f"⏰ <b>Осталось дней:</b> {info['days_left']}\n"
                
                if info['is_expiring_soon']:
                    message += "⚠️ <i>Подписка скоро истечет!</i>\n"
            else:
                message += "⚠️ <b>Подписка истекла</b>\n"
        
        if info['monthly_price'] > 0:
            message += f"💰 <b>Стоимость:</b> {info['monthly_price']:,} ₸/мес\n"
        
        return message
