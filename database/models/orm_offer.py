# -*- coding: utf-8 -*-
# database/models/orm_offer.py

from sqlalchemy import select, update, delete, desc, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from database.models.model_offer import Offer
from database.models.model_user_jk import UserJK
from database.models.model_jk import JK
from database.models.model_user import User
from database.models.model_jk_service_provider import JKServiceProvider
from database.enums.offer_enums import OfferStatus
from typing import Optional, List, Dict, Any
import datetime


async def orm_add_offer(session: AsyncSession, data: dict) -> Offer:
    """Добавляет новую заявку в базу данных."""
    offer_data = {
        "category": data.get("category"),
        "title": data.get("title"),
        "description": data.get("description"),
        "media_id": data.get("media_id"),
        "bus_media_id": data.get("bus_media_id"),
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
    
    if offer and offer.user_id:
        # Загружаем информацию о пользователе отдельно по user_id из заявки
        user_result = await session.execute(
            select(User).where(User.user_id == offer.user_id)
        )
        user = user_result.scalar_one_or_none()
        # Добавляем пользователя как атрибут для удобства
        offer.user = user
    
    return offer


async def orm_get_service_provider_statistics(session: AsyncSession, user_id: int) -> Dict[str, Any]:
    """
    Получает статистику для поставщика услуг.
    """
    # Получаем все JKServiceProvider для данного пользователя
    providers_result = await session.execute(
        select(JKServiceProvider)
        .where(JKServiceProvider.responsible_user_id == user_id)
        .where(JKServiceProvider.is_active == True)
        .options(selectinload(JKServiceProvider.jk))
    )
    providers = providers_result.scalars().all()
    
    if not providers:
        return {
            "total_offers": 0,
            "completed_offers": 0,
            "in_progress_offers": 0,
            "cancelled_offers": 0,
            "completion_rate": 0.0,
            "avg_response_time_hours": 0.0,
            "jk_list": []
        }
    
    # Получаем все ЖК где пользователь является поставщиком услуг
    jk_ids = [provider.jk_id for provider in providers]
    categories = [provider.category.value if hasattr(provider.category, 'value') else provider.category for provider in providers]
    
    # Статистика по заявкам в этих ЖК с учетом категорий
    stats_result = await session.execute(
        select(
            func.count().label("total_offers"),
            func.sum(case((Offer.status == OfferStatus.COMPLETED, 1), else_=0)).label("completed_offers"),
            func.sum(case((Offer.status == OfferStatus.IN_PROGRESS, 1), else_=0)).label("in_progress_offers"),
            func.sum(case((Offer.status == OfferStatus.CANCELLED, 1), else_=0)).label("cancelled_offers")
        )
        .select_from(Offer)
        .join(UserJK, Offer.user_jk_id == UserJK.id)
        .where(
            and_(
                UserJK.jk_id.in_(jk_ids),
                Offer.category.in_(categories)
            )
        )
    )
    
    stats = stats_result.first()
    
    # Расчет среднего времени отклика для завершенных заявок
    response_time_result = await session.execute(
        select(
            func.avg(
                func.extract('epoch', Offer.updated_at) - func.extract('epoch', Offer.created_at)
            ).label("avg_response_seconds")
        )
        .select_from(Offer)
        .join(UserJK, Offer.user_jk_id == UserJK.id)
        .where(
            and_(
                UserJK.jk_id.in_(jk_ids),
                Offer.category.in_(categories),
                Offer.status == OfferStatus.COMPLETED,
                Offer.updated_at.isnot(None)
            )
        )
    )
    
    avg_response_seconds = response_time_result.scalar() or 0
    avg_response_hours = round(avg_response_seconds / 3600, 2) if avg_response_seconds else 0
    
    # Расчет коэффициента завершения
    total_offers = stats.total_offers or 0
    completed_offers = stats.completed_offers or 0
    completion_rate = round((completed_offers / total_offers * 100), 2) if total_offers > 0 else 0
    
    # Список ЖК с названиями
    jk_names = [provider.jk.name for provider in providers if provider.jk]
    
    return {
        "total_offers": total_offers,
        "completed_offers": completed_offers,
        "in_progress_offers": stats.in_progress_offers or 0,
        "cancelled_offers": stats.cancelled_offers or 0,
        "completion_rate": completion_rate,
        "avg_response_time_hours": avg_response_hours,
        "jk_list": jk_names
    }


async def orm_get_offers_by_status_for_provider(
    session: AsyncSession, 
    user_id: int, 
    status: str, 
    page: int = 0, 
    limit: int = 10
) -> List[Offer]:
    """
    Получает заявки по статусу для конкретного поставщика услуг с пагинацией.
    
    Args:
        session: Сессия базы данных
        user_id: ID пользователя-поставщика услуг
        status: Статус заявок (ACTIVE, IN_PROGRESS, COMPLETED, CANCELLED)
        page: Номер страницы (начиная с 0)
        limit: Количество заявок на странице
        
    Returns:
        List[Offer]: Список заявок с загруженными связанными данными
    """
    try:
        # Сначала получаем все ЖК и категории, которые обслуживает данный поставщик
        provider_query = select(JKServiceProvider).where(
            JKServiceProvider.responsible_user_id == user_id
        )
        provider_result = await session.execute(provider_query)
        providers = provider_result.scalars().all()
        
        if not providers:
            return []
        
        # Получаем списки ЖК и категорий
        jk_ids = [p.jk_id for p in providers]
        categories = [p.category.value for p in providers]
        
        # Преобразуем строку статуса в enum
        if isinstance(status, str):
            # Сначала попробуем найти по значению (если передали "active", "in_progress", etc.)
            status_enum = None
            for offer_status in OfferStatus:
                if offer_status.value == status.lower():
                    status_enum = offer_status
                    break
            
            # Если не нашли, попробуем найти по имени enum (если передали "ACTIVE", "IN_PROGRESS", etc.)
            if status_enum is None:
                try:
                    status_enum = OfferStatus[status.upper()]
                except KeyError:
                    print(f"Unknown status: {status}")
                    return []
        else:
            status_enum = status
        
        # Формируем запрос для поиска заявок
        query = (
            select(Offer)
            .options(
                selectinload(Offer.user_jk).selectinload(UserJK.jk),
                selectinload(Offer.user_jk)
            )
            .join(UserJK, Offer.user_jk_id == UserJK.id)
            .where(
                and_(
                    UserJK.jk_id.in_(jk_ids),  # ЖК, которые обслуживает поставщик
                    Offer.category.in_(categories),  # Категории, которые обслуживает поставщик
                    Offer.status == status_enum  # Нужный статус
                )
            )
            .order_by(desc(Offer.created_at))
            .offset(page * limit)
            .limit(limit)
        )
        
        result = await session.execute(query)
        offers = result.scalars().all()
        
        # Загружаем пользователей отдельно для каждой заявки
        for offer in offers:
            if offer.user_id:
                user_query = select(User).where(User.user_id == offer.user_id)
                user_result = await session.execute(user_query)
                offer.user = user_result.scalar_one_or_none()
        
        return offers
        
    except Exception as e:
        print(f"Error in orm_get_offers_by_status_for_provider: {e}")
        return []
