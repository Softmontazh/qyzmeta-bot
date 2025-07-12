# -*- coding: utf-8 -*-
# database/models/model_jk_service_provider.py

import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Boolean,
    Enum as SqlEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.model_base import Base
from database.enums.offer_category_enum import OfferCategory

if TYPE_CHECKING:
    from database.models.model_jk import JK


class JKServiceProvider(Base):
    """
    Модель привязки ЖК к обслуживающим организациям по категориям.
    
    Каждая запись представляет ответственную организацию/лицо 
    за определенную категорию услуг в конкретном ЖК.
    """
    
    __tablename__ = "jk_service_providers"

    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    uuid: Mapped[str] = mapped_column(
        String(36), 
        nullable=False, 
        unique=True, 
        index=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Связь с ЖК
    jk_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("jks.id"), 
        nullable=False, 
        index=True
    )
    
    # Категория обслуживания
    category: Mapped[OfferCategory] = mapped_column(
        SqlEnum(OfferCategory), 
        nullable=False, 
        index=True
    )
    
    # Ответственное лицо/организация
    responsible_user_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey("users.user_id"), 
        nullable=False, 
        index=True
    )
    
    # Дополнительная информация
    organization_name: Mapped[Optional[str]] = mapped_column(
        String(200), 
        nullable=True,
        comment="Название организации/компании"
    )
    
    contact_phone: Mapped[Optional[str]] = mapped_column(
        String(50), 
        nullable=True,
        index=True,
        comment="Контактный телефон"
    )
    
    contact_email: Mapped[Optional[str]] = mapped_column(
        String(100), 
        nullable=True,
        comment="Контактный email"
    )
    
    # Статусы и настройки
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        index=True,
        comment="Активна ли привязка"
    )
    
    receives_notifications: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="Получает ли уведомления о заявках"
    )
    
    auto_assign_offers: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="Автоматически назначать заявки этой категории"
    )
    
    # Приоритет (для случаев с несколькими поставщиками услуг)
    priority: Mapped[int] = mapped_column(
        Integer, 
        default=1, 
        nullable=False,
        comment="Приоритет (1 - высший, чем больше число - тем ниже приоритет)"
    )
    
    # Рабочее время (опционально)
    work_hours_start: Mapped[Optional[str]] = mapped_column(
        String(5), 
        nullable=True,
        comment="Начало рабочего дня (HH:MM)"
    )
    
    work_hours_end: Mapped[Optional[str]] = mapped_column(
        String(5), 
        nullable=True,
        comment="Конец рабочего дня (HH:MM)"
    )
    
    # Дни работы (битовая маска: пн=1, вт=2, ср=4, чт=8, пт=16, сб=32, вс=64)
    work_days: Mapped[Optional[int]] = mapped_column(
        Integer, 
        default=31,  # пн-пт (1+2+4+8+16)
        nullable=True,
        comment="Рабочие дни недели (битовая маска)"
    )
    
    # Дополнительные поля
    description: Mapped[Optional[str]] = mapped_column(
        String(500), 
        nullable=True,
        comment="Описание услуг или специализации"
    )
    
    contract_number: Mapped[Optional[str]] = mapped_column(
        String(100), 
        nullable=True,
        comment="Номер договора обслуживания"
    )
    
    contract_start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        nullable=True,
        comment="Дата начала договора"
    )
    
    contract_end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        nullable=True,
        comment="Дата окончания договора"
    )
    
    # Служебные поля
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, 
        nullable=True,
        comment="Кто создал запись"
    )

    # Связи
    jk: Mapped["JK"] = relationship(
        "JK", 
        back_populates="service_providers"
    )

    # Ограничения уникальности
    __table_args__ = (
        # Одна категория - один основной поставщик на ЖК (по приоритету)
        # Но может быть несколько с разными приоритетами
    )

    def __repr__(self) -> str:
        return f"<JKServiceProvider(jk_id={self.jk_id}, category={self.category.value}, responsible={self.responsible_user_id})>"

    @property
    def category_display_name(self) -> str:
        """Возвращает отображаемое название категории"""
        return self.category.display_name

    @property
    def category_emoji(self) -> str:
        """Возвращает эмодзи категории"""
        return self.category.emoji

    @property
    def is_contract_active(self) -> bool:
        """Проверяет, активен ли договор на текущую дату"""
        if not self.contract_start_date or not self.contract_end_date:
            return True  # Если даты не указаны, считаем активным
        
        now = datetime.utcnow()
        return self.contract_start_date <= now <= self.contract_end_date

    def is_working_now(self) -> bool:
        """Проверяет, работает ли поставщик услуг сейчас"""
        if not self.is_active:
            return False
            
        now = datetime.utcnow()
        current_day = now.weekday()  # 0=понедельник, 6=воскресенье
        
        # Проверяем рабочие дни
        if self.work_days:
            day_bit = 1 << current_day
            if not (self.work_days & day_bit):
                return False
        
        # Проверяем рабочее время
        if self.work_hours_start and self.work_hours_end:
            current_time = now.strftime("%H:%M")
            return self.work_hours_start <= current_time <= self.work_hours_end
            
        return True
