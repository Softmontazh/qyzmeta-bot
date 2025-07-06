# coding: utf-8
# database/models/model_lot.py

from datetime import datetime, timedelta, timezone
from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    Column,
    Enum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.model_base import Base
from database.models.model_user import User
from database.enums.lot_enums import LotOfferType, LotStatus, LotVisibility


class Lot(Base):

    __tablename__ = "lots"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, index=True)
    offer_type: Mapped[LotOfferType] = mapped_column(
        Enum(LotOfferType, name="offer_type_enum"), nullable=False, index=True
    )
    type_lot: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float(asdecimal=True), index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    image_id: Mapped[str] = mapped_column(String(150), nullable=True)

    # Идентификатор пользователя-владельца лота
    owner_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=False, index=True
    )
    # Связь с пользователем (владельцем лота)
    owner: Mapped["User"] = relationship(back_populates="lots")

    # Статус заявки
    status: Mapped[LotStatus] = mapped_column(
        Enum(LotStatus, name="offer_status_enum"),
        nullable=False,
        default=LotStatus.ACTIVE,
        index=True,
    )
    # Видимость заявки
    visibility: Mapped[LotVisibility] = mapped_column(
        Enum(LotVisibility, name="offer_visibility_enum"),
        default=LotVisibility.PUBLIC,
        nullable=False,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=30),
        index=True,
    )
