# coding: utf-8
# database/models/model_lot_limit.py

from sqlalchemy import Integer, Enum as SqlEnum, String
from sqlalchemy.orm import Mapped, mapped_column
from database.models.model_base import Base
from database.enums.user_enums import UserRole


class LotLimit(Base):
    __tablename__ = "lot_limits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole), unique=True, index=True, nullable=False
    )

    limit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
