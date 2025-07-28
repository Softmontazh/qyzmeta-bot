# -*- coding: utf-8 -*-
# database/models/model_subscription_price.py

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from datetime import datetime, timezone

from database.models.model_base import Base
from database.enums.subscription_enums import SubscriptionTier


class SubscriptionPrice(Base):
    """Модель для управления ценами подписок"""
    __tablename__ = "subscription_prices"

    id = Column(Integer, primary_key=True, index=True)
    tier = Column(String(20), nullable=False, index=True)  # FREE, BASIC, PREMIUM, VIP
    price = Column(Integer, nullable=False)  # Цена в тенге
    is_active = Column(Boolean, default=True, nullable=False)  # Активна ли цена
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(BigInteger, nullable=True)  # ID создателя (Telegram user_id может быть большим)
    notes = Column(Text, nullable=True)  # Заметки о изменении цены

    def __repr__(self):
        return f"<SubscriptionPrice(tier={self.tier}, price={self.price}, active={self.is_active})>"

    @property
    def tier_enum(self) -> SubscriptionTier:
        """Возвращает enum тарифа"""
        return SubscriptionTier(self.tier)

    @property
    def tier_display(self) -> str:
        """Возвращает отображаемое название тарифа"""
        return self.tier_enum.get_russian_name()

    @property
    def formatted_price(self) -> str:
        """Возвращает отформатированную цену"""
        if self.price == 0:
            return "Бесплатно"
        return f"{self.price:,} ₸/мес"

    @property
    def created_at_local(self) -> datetime:
        """Возвращает время создания в местном времени"""
        if self.created_at.tzinfo is None:
            return self.created_at.replace(tzinfo=timezone.utc)
        return self.created_at

    def to_dict(self) -> dict:
        """Преобразует объект в словарь"""
        return {
            "id": self.id,
            "tier": self.tier,
            "tier_display": self.tier_display,
            "price": self.price,
            "formatted_price": self.formatted_price,
            "is_active": self.is_active,
            "created_at": self.created_at_local,
            "created_by": self.created_by,
            "notes": self.notes
        }
