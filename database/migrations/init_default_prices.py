# -*- coding: utf-8 -*-
# database/migrations/init_default_prices.py

from sqlalchemy.ext.asyncio import AsyncSession
from database.models.orm_subscription_price import orm_initialize_default_prices
import logging

logger = logging.getLogger(__name__)


async def initialize_default_subscription_prices(session: AsyncSession, created_by: int = 0):
    """Инициализация цен подписок по умолчанию при первом запуске"""
    try:
        await orm_initialize_default_prices(session, created_by)
        await session.commit()
        logger.info("✅ Цены подписок по умолчанию успешно инициализированы")
        return True
    except Exception as e:
        await session.rollback()
        logger.error(f"❌ Ошибка при инициализации цен: {e}")
        return False
