# -*- coding: utf-8 -*-
# database/models/model_offer.py

import uuid
from sqlalchemy import Integer, BigInteger, String, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from database.models.model_base import Base
from database.enums.offer_enums import OfferStatus

if TYPE_CHECKING:
    from database.models.model_user_jk import UserJK


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # UUID для API
    uuid: Mapped[str] = mapped_column(
        String(36), default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Категория заявки (по индексу для поиска)
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False)

    # Название заявки
    title: Mapped[str] = mapped_column(String(200), nullable=False)

    # Описание заявки
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # ID фото или видео в Telegram
    media_id: Mapped[str] = mapped_column(String(200), nullable=True)

    # ID пользователя, создавшего заявку
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # ID связи пользователя с ЖК
    user_jk_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user_jk.id"), nullable=False, index=True
    )

    # Статус заявки (nullable для совместимости со старыми данными)
    status: Mapped[OfferStatus] = mapped_column(
        Enum(OfferStatus), default=OfferStatus.ACTIVE, nullable=True, index=True
    )

    # Связи
    user_jk: Mapped["UserJK"] = relationship("UserJK", back_populates="offers")
