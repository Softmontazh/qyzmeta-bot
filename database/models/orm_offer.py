# -*- coding: utf-8 -*-
# database/models/orm_offer.py

from sqlalchemy import select, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.model_offer import Offer
from typing import Optional, List


async def orm_add_offer(session: AsyncSession, data: dict) -> Offer:
    """Добавляет новую заявку в базу данных."""
    offer = Offer(
        category=data.get("category"),
        title=data.get("title"),
        description=data.get("description"),
        media_id=data.get("media_id"),
        user_id=data.get("user_id"),
        user_jk_id=data.get("user_jk_id"),
    )
    session.add(offer)
    await session.flush()
    return offer


async def orm_get_offer_by_id(session: AsyncSession, offer_id: int) -> Optional[Offer]:
    """Получает заявку по ID."""
    result = await session.execute(select(Offer).where(Offer.id == offer_id))
    return result.scalar_one_or_none()


async def orm_get_offers_by_user_id(
    session: AsyncSession, user_id: int, limit: int = 50
) -> List[Offer]:
    """Получает все заявки пользователя."""
    result = await session.execute(
        select(Offer)
        .where(Offer.user_id == user_id)
        .order_by(desc(Offer.created_at))
        .limit(limit)
    )
    return result.scalars().all()


async def orm_get_offers_by_jk(
    session: AsyncSession, user_jk_id: int, limit: int = 50
) -> List[Offer]:
    """Получает все заявки по ЖК."""
    result = await session.execute(
        select(Offer)
        .where(Offer.user_jk_id == user_jk_id)
        .order_by(desc(Offer.created_at))
        .limit(limit)
    )
    return result.scalars().all()


async def orm_update_offer(
    session: AsyncSession, offer_id: int, data: dict
) -> Optional[Offer]:
    """Обновляет заявку."""
    await session.execute(
        update(Offer).where(Offer.id == offer_id).values(**data)
    )
    return await orm_get_offer_by_id(session, offer_id)


async def orm_delete_offer(session: AsyncSession, offer_id: int) -> bool:
    """Удаляет заявку."""
    result = await session.execute(delete(Offer).where(Offer.id == offer_id))
    return result.rowcount > 0


async def orm_get_offers_by_category(
    session: AsyncSession, category: str, user_jk_id: int = None, limit: int = 50
) -> List[Offer]:
    """Получает заявки по категории."""
    query = select(Offer).where(Offer.category == category)
    
    if user_jk_id:
        query = query.where(Offer.user_jk_id == user_jk_id)
    
    query = query.order_by(desc(Offer.created_at)).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
