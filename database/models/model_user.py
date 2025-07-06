# -*- coding: utf-8 -*-
# database/models/model_user.py


from database.enums.user_enums import UserLanguage, UserRole
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Select,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.model_base import Base
from database.enums.user_enums import UserRole
from database.models.model_lot_limit import LotLimit


if TYPE_CHECKING:
    from database.models.model_lot import Lot  # Для избежания циклических импортов

# # Ограничения на количество лотов для разных ролей пользователей
# # Лист ролей и их лимиты
# LimitedLot = {
#     UserRole.CREATOR: 1000000,
#     UserRole.OWNER: 1000000,
#     UserRole.GUEST: 0,
#     UserRole.USER: 10,
#     UserRole.ADMIN: 100,
#     UserRole.SUPERADMIN: 100,
#     UserRole.MODERATOR: 100,
#     UserRole.SUPPORT: 100,
#     UserRole.MANAGER: 1000,
#     UserRole.PARTNER: 10000,
# }


class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, unique=True, index=True
    )

    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(50))
    username: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    user_language: Mapped[UserLanguage] = mapped_column(
        SqlEnum(UserLanguage), default=UserLanguage.RU, index=True
    )

    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_business: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole), default=UserRole.GUEST, index=True
    )
    phone: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    email: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), index=True)

    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_blocked_by_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_subscribed_to_channel: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True
    )
    is_subscribed_to_group: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True
    )
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    last_active: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    wants_notifications: Mapped[bool] = mapped_column(default=True)

    # Реферал
    invited_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), index=True
    )

    lots: Mapped[list["Lot"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan", lazy="selectin"
    )

    async def get_lot_limit(self, session: AsyncSession) -> int:
        """
        Возвращает лимит лотов на основе роли пользователя.
        Если лимит не найден в таблице LotLimit — возвращает 0.
        """

        result = await session.execute(
            Select(LotLimit.limit).where(LotLimit.role == self.role)
        )
        return result.scalar() or 0
