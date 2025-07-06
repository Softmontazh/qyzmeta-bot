# coding: utf-8
# database/models/model_jk.py

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.models.model_base import Base


class JK(Base):
    __tablename__ = "jks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    city: Mapped[str] = mapped_column(String(50), nullable=True)
    street: Mapped[str] = mapped_column(String(100), nullable=True)
    house: Mapped[str] = mapped_column(String(20), nullable=True)
    block: Mapped[str] = mapped_column(String(20), nullable=True)
    # Уникальный идентификатор канала ЖК
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=True, index=True)
    # Уникальный идентификатор группы ЖК
    group_id: Mapped[int] = mapped_column(BigInteger, nullable=True, index=True)
    # Уникальный идентификатор управляющей компании
    id_uk: Mapped[int] = mapped_column(BigInteger, nullable=True, index=True)

    image_id: Mapped[str] = mapped_column(String(100), nullable=True)

    creator_id: Mapped[int] = mapped_column(BigInteger, nullable=True)

    @property
    def full_address(self) -> str:
        address = f"{self.city or ''}, {self.street or ''}, {self.house or ''}"
        if self.block:
            address += f", блок {self.block}"
        return address.strip(", ")
