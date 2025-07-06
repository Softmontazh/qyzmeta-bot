# -*- coding: utf-8 -*-
# database/models/model_user_jk.py

from sqlalchemy import Integer, BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from database.models.model_base import Base


class UserJK(Base):
    __tablename__ = "user_jk"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ID пользователя в Telegram (может быть фирма)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)

    # ID жилого комплекса (ЖК), к которому принадлежит пользователь
    jk_id: Mapped[int] = mapped_column(ForeignKey("jks.id"), index=True)

    # Номер квартиры пользователя в ЖК
    appartment: Mapped[str] = mapped_column(String(20), default="", nullable=False)

    # Флаг, указывающий, является ли пользователь резидентом ЖК
    is_resident: Mapped[bool] = mapped_column(default=True, nullable=True)

    # Флаг, указывающий, является ли пользователь администратором ЖК (ОСИ)
    is_admin: Mapped[bool] = mapped_column(default=False, nullable=True)

    # Флаг, указывающий, является ли пользователь представителем УК
    is_uk: Mapped[bool] = mapped_column(default=False, nullable=True)

    # Флаг, указывающий, является ли пользователь Службой ЖК
    is_service: Mapped[bool] = mapped_column(default=False, nullable=True)
