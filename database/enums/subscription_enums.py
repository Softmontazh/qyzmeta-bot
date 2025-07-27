# -*- coding: utf-8 -*-
# database/enums/subscription_enums.py

from enum import Enum


class SubscriptionTier(str, Enum):
    """Тарифные планы подписки"""
    FREE = "FREE"
    BASIC = "BASIC"
    PREMIUM = "PREMIUM"
    VIP = "VIP"
    
    def get_russian_name(self):
        """Возвращает русское название тарифа"""
        tier_names = {
            "FREE": "🆓 Бесплатный",
            "BASIC": "⭐ Базовый", 
            "PREMIUM": "💎 Премиум",
            "VIP": "👑 VIP"
        }
        return tier_names.get(self.value, self.value)
        
    def get_address_limit(self):
        """Возвращает лимит адресов для тарифа"""
        limits = {
            "FREE": 1,
            "BASIC": 3,
            "PREMIUM": 10,
            "VIP": 999  # Практически без ограничений
        }
        return limits.get(self.value, 1)
    
    def get_monthly_price(self):
        """Возвращает месячную стоимость тарифа в тенге"""
        prices = {
            "FREE": 0,
            "BASIC": 2990,     # ~$7
            "PREMIUM": 4990,   # ~$12  
            "VIP": 9990        # ~$24
        }
        return prices.get(self.value, 0)


class SubscriptionStatus(str, Enum):
    """Статусы подписки"""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"
    
    def get_russian_name(self):
        """Возвращает русское название статуса"""
        status_names = {
            "ACTIVE": "✅ Активна",
            "EXPIRED": "⏰ Истекла",
            "CANCELLED": "❌ Отменена", 
            "PENDING": "⏳ Ожидает активации"
        }
        return status_names.get(self.value, self.value)


class FeatureType(str, Enum):
    """Типы функций подписки"""
    MULTIPLE_ADDRESSES = "MULTIPLE_ADDRESSES"
    PRIORITY_SUPPORT = "PRIORITY_SUPPORT"
    ADVANCED_ANALYTICS = "ADVANCED_ANALYTICS"
    NO_ADS = "NO_ADS"
    EARLY_ACCESS = "EARLY_ACCESS"
    
    def get_russian_name(self):
        """Возвращает русское название функции"""
        feature_names = {
            "MULTIPLE_ADDRESSES": "🏠 Множественные адреса",
            "PRIORITY_SUPPORT": "🚀 Приоритетная поддержка",
            "ADVANCED_ANALYTICS": "📊 Расширенная аналитика",
            "NO_ADS": "🚫 Без рекламы",
            "EARLY_ACCESS": "⚡ Ранний доступ"
        }
        return feature_names.get(self.value, self.value)
