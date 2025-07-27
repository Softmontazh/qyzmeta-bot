# -*- coding: utf-8 -*-
# database/models/model_user_subscription.py

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum as SqlEnum

from database.models.model_base import Base
from database.enums.subscription_enums import SubscriptionTier, SubscriptionStatus


class UserSubscription(Base):
    """Модель подписки пользователя"""
    
    __tablename__ = "user_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Связь с пользователем
    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True,
        comment="Telegram User ID"
    )
    
    # Параметры подписки
    tier: Mapped[SubscriptionTier] = mapped_column(
        SqlEnum(SubscriptionTier), 
        default=SubscriptionTier.FREE, 
        index=True,
        comment="Тарифный план"
    )
    
    status: Mapped[SubscriptionStatus] = mapped_column(
        SqlEnum(SubscriptionStatus),
        default=SubscriptionStatus.ACTIVE,
        index=True,
        comment="Статус подписки"
    )
    
    # Лимиты и ограничения
    max_addresses: Mapped[int] = mapped_column(
        Integer, 
        default=1,
        comment="Максимальное количество адресов"
    )
    
    # Временные рамки
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="Дата начала подписки"
    )
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        index=True,
        comment="Дата истечения подписки"
    )
    
    # Дополнительная информация
    payment_info: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="Информация о платеже"
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="Заметки администратора"
    )

    def __repr__(self):
        return f"<UserSubscription(user_id={self.user_id}, tier={self.tier}, status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Проверяет, активна ли подписка"""
        if self.status != SubscriptionStatus.ACTIVE:
            return False
            
        if self.expires_at and self.expires_at <= datetime.now(timezone.utc):
            return False
            
        return True
        
    @property
    def days_left(self) -> Optional[int]:
        """Возвращает количество дней до истечения подписки"""
        if not self.expires_at:
            return None
            
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, delta.days)
    
    @property
    def is_expiring_soon(self) -> bool:
        """Проверяет, истекает ли подписка в ближайшие 7 дней"""
        if not self.expires_at:
            return False
            
        days_left = self.days_left
        return days_left is not None and days_left <= 7
    
    def get_tier_display(self) -> str:
        """Возвращает красивое отображение тарифа с лимитом"""
        tier_name = self.tier.get_russian_name()
        return f"{tier_name} (до {self.max_addresses} адресов)"
    
    def get_status_display(self) -> str:
        """Возвращает красивое отображение статуса"""
        status_name = self.status.get_russian_name()
        
        if self.status == SubscriptionStatus.ACTIVE and self.expires_at:
            days_left = self.days_left
            if days_left is not None:
                if days_left == 0:
                    return f"{status_name} (истекает сегодня)"
                elif days_left <= 3:
                    return f"{status_name} (осталось {days_left} дн.)"
                else:
                    return f"{status_name} (до {self.expires_at.strftime('%d.%m.%Y')})"
        
        return status_name
