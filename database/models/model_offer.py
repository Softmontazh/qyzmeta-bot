# -*- coding: utf-8 -*-
# database/models/model_offer.py

import uuid
from datetime import datetime
from sqlalchemy import Integer, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from database.models.model_base import Base


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # UUID для API
    uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=False), default=lambda: str(uuid.uuid4()), nullable=False
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
