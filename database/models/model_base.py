# -*- coding: utf-8 -*-
# .\database\models\model_base.py

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Базовая модель SQLAlchemy для наследования другими моделями.
    Атрибуты:
        created_at (DateTime): Дата и время создания записи. Устанавливается автоматически при создании.
        updated_at (DateTime): Дата и время последнего обновления записи. Обновляется автоматически при изменении.
    """

    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
