import uuid
from sqlalchemy import BigInteger, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional

from database.models.model_base import Base

if TYPE_CHECKING:
    from database.models.model_user_jk import UserJK
    from database.models.model_jk_service_provider import JKServiceProvider


class JK(Base):
    __tablename__ = "jks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True, index=True, 
        default=lambda: str(uuid.uuid4())
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
    # BUS_ID для общего доступа к изображению между ботами платформы
    bus_image_id: Mapped[str] = mapped_column(String(100), nullable=True)

    creator_id: Mapped[int] = mapped_column(BigInteger, nullable=True)

    # Список админов ЖК для локальной системы ролей (хранится как JSON массив telegram_id)
    admins_list: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Связи
    user_jks: Mapped[list["UserJK"]] = relationship("UserJK", back_populates="jk")
    service_providers: Mapped[list["JKServiceProvider"]] = relationship(
        "JKServiceProvider", 
        back_populates="jk",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    @property
    def full_address(self) -> str:
        address = f"{self.city or ''}, {self.street or ''}, {self.house or ''}"
        if self.block:
            address += f", блок {self.block}"
        return address.strip(", ")
