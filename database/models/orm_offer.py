# -*- coding: utf-8 -*-
# database/models/orm_offer.py

from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from database.models.model_offer import Offer
from database.models.model_user_jk import UserJK
from database.models.model_jk import JK
from database.enums.offer_enums import OfferStatus
from typing import Optional, List


async def orm_add_offer(session: AsyncSession, data: dict) -> Offer:
    """Добавляет новую заявку в базу данных."""
    offer_data = {
        "category": data.get("category"),
        "title": data.get("title"),
        "description": data.get("description"),
        "media_id": data.get("media_id"),
        "user_id": data.get("user_id"),
        "user_jk_id": data.get("user_jk_id"),
        "status": data.get("status", OfferStatus.ACTIVE),  # Устанавливаем ACTIVE по умолчанию
    }
    
    offer = Offer(**offer_data)
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


async def orm_get_offers_by_user(
    session: AsyncSession, user_id: int, limit: int = 50
) -> List[Offer]:
    """Получает все заявки пользователя с полной информацией о ЖК."""
    result = await session.execute(
        select(Offer)
        .options(
            selectinload(Offer.user_jk).selectinload(UserJK.jk)
        )
        .where(Offer.user_id == user_id)
        .where((Offer.status != OfferStatus.ARCHIVED) | (Offer.status.is_(None)))
        .order_by(desc(Offer.created_at))
        .limit(limit)
    )
    return result.scalars().all()


async def orm_archive_offer(session: AsyncSession, offer_id: int) -> bool:
    """Архивирует заявку (меняет статус на ARCHIVED)."""
    result = await session.execute(
        update(Offer)
        .where(Offer.id == offer_id)
        .values(status=OfferStatus.ARCHIVED)
    )
    return result.rowcount > 0


async def orm_get_offer_by_uuid(session: AsyncSession, offer_uuid: str) -> Optional[Offer]:
    """Получает заявку по UUID."""
    result = await session.execute(select(Offer).where(Offer.uuid == offer_uuid))
    return result.scalar_one_or_none()


async def orm_archive_offer_by_uuid(session: AsyncSession, offer_uuid: str) -> bool:
    """Архивирует заявку по UUID (меняет статус на ARCHIVED)."""
    result = await session.execute(
        update(Offer)
        .where(Offer.uuid == offer_uuid)
        .values(status=OfferStatus.ARCHIVED)
    )
    return result.rowcount > 0


async def orm_get_active_offers_by_user(
    session: AsyncSession, user_id: int, limit: int = 50
) -> List[Offer]:
    """Получает только активные заявки пользователя."""
    result = await session.execute(
        select(Offer)
        .options(
            selectinload(Offer.user_jk).selectinload(UserJK.jk)
        )
        .where(Offer.user_id == user_id)
        .where((Offer.status != OfferStatus.ARCHIVED) | (Offer.status.is_(None)))
        .order_by(desc(Offer.created_at))
        .limit(limit)
    )
    return result.scalars().all()


async def orm_update_offer_status(session: AsyncSession, offer_id: int, new_status: OfferStatus) -> tuple[Offer, OfferStatus]:
    """
    Обновляет статус заявки и возвращает заявку и старый статус.
    Возвращает tuple(offer, old_status) для уведомлений.
    """
    # Получаем текущую заявку
    result = await session.execute(
        select(Offer).where(Offer.id == offer_id)
    )
    offer = result.scalar_one_or_none()
    
    if not offer:
        raise ValueError(f"Заявка с ID {offer_id} не найдена")
    
    old_status = offer.status
    
    # Обновляем статус
    await session.execute(
        update(Offer)
        .where(Offer.id == offer_id)
        .values(status=new_status, updated_at=func.now())
    )
    
    # Обновляем объект в памяти
    offer.status = new_status
    
    return offer, old_status


async def orm_get_offer_with_user_info(session: AsyncSession, offer_id: int) -> Offer:
    """
    Получает заявку с полной информацией о пользователе и ЖК для уведомлений.
    """
    from database.models.model_user import User
    
    result = await session.execute(
        select(Offer)
        .options(
            selectinload(Offer.user_jk).selectinload(UserJK.jk)
        )
        .where(Offer.id == offer_id)
    )
    offer = result.scalar_one_or_none()
    
    if offer and offer.user_jk:
        # Загружаем информацию о пользователе отдельно
        user_result = await session.execute(
            select(User).where(User.user_id == offer.user_jk.user_id)
        )
        user = user_result.scalar_one_or_none()
        # Добавляем пользователя как атрибут для удобства
        offer.user_jk.user = user
    
    return offer
