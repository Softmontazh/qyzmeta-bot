# -*- coding: utf-8 -*-
# database/models/orm_jk_service_provider.py

from typing import Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from database.models.model_jk_service_provider import JKServiceProvider
from database.enums.offer_category_enum import OfferCategory


async def orm_add_service_provider(session: AsyncSession, service_data: dict) -> JKServiceProvider:
    """Добавить нового поставщика услуг для ЖК"""
    service_provider = JKServiceProvider(**service_data)
    session.add(service_provider)
    await session.flush()
    return service_provider


async def orm_get_service_provider_by_id(session: AsyncSession, provider_id: int) -> Optional[JKServiceProvider]:
    """Получить поставщика услуг по ID"""
    stmt = select(JKServiceProvider).where(JKServiceProvider.id == provider_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def orm_get_service_provider_by_uuid(session: AsyncSession, uuid: str) -> Optional[JKServiceProvider]:
    """Получить поставщика услуг по UUID"""
    stmt = select(JKServiceProvider).where(JKServiceProvider.uuid == uuid)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def orm_get_service_providers_by_jk(session: AsyncSession, jk_id: int, 
                                        active_only: bool = True) -> List[JKServiceProvider]:
    """Получить всех поставщиков услуг для ЖК"""
    stmt = select(JKServiceProvider).where(JKServiceProvider.jk_id == jk_id)
    
    if active_only:
        stmt = stmt.where(JKServiceProvider.is_active == True)
    
    stmt = stmt.order_by(JKServiceProvider.category, JKServiceProvider.priority)
    result = await session.execute(stmt)
    return result.scalars().all()


async def orm_get_service_provider_by_category(session: AsyncSession, jk_id: int, 
                                             category: OfferCategory) -> Optional[JKServiceProvider]:
    """Получить поставщика услуг для конкретной категории в ЖК (с наивысшим приоритетом)"""
    stmt = (select(JKServiceProvider)
            .where(JKServiceProvider.jk_id == jk_id)
            .where(JKServiceProvider.category == category)
            .where(JKServiceProvider.is_active == True)
            .order_by(JKServiceProvider.priority)
            .limit(1))
    
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def orm_get_service_providers_by_user(session: AsyncSession, user_id: int) -> List[JKServiceProvider]:
    """Получить всех поставщиков услуг, где пользователь является ответственным"""
    stmt = (select(JKServiceProvider)
            .where(JKServiceProvider.responsible_user_id == user_id)
            .where(JKServiceProvider.is_active == True)
            .options(selectinload(JKServiceProvider.jk))
            .order_by(JKServiceProvider.jk_id, JKServiceProvider.category))
    
    result = await session.execute(stmt)
    return result.scalars().all()


async def orm_update_service_provider(session: AsyncSession, provider_id: int, 
                                     update_data: dict) -> Optional[JKServiceProvider]:
    """Обновить данные поставщика услуг"""
    stmt = (update(JKServiceProvider)
            .where(JKServiceProvider.id == provider_id)
            .values(**update_data)
            .returning(JKServiceProvider))
    
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def orm_deactivate_service_provider(session: AsyncSession, provider_id: int) -> bool:
    """Деактивировать поставщика услуг (мягкое удаление)"""
    stmt = (update(JKServiceProvider)
            .where(JKServiceProvider.id == provider_id)
            .values(is_active=False))
    
    result = await session.execute(stmt)
    return result.rowcount > 0


async def orm_delete_service_provider(session: AsyncSession, provider_id: int) -> bool:
    """Полностью удалить поставщика услуг"""
    stmt = delete(JKServiceProvider).where(JKServiceProvider.id == provider_id)
    result = await session.execute(stmt)
    return result.rowcount > 0


async def orm_get_responsible_for_offer_category(session: AsyncSession, jk_id: int, 
                                               category: OfferCategory) -> Optional[int]:
    """Получить ID ответственного пользователя для категории заявки в ЖК"""
    provider = await orm_get_service_provider_by_category(session, jk_id, category)
    return provider.responsible_user_id if provider else None


async def orm_check_user_manages_category(session: AsyncSession, user_id: int, 
                                        jk_id: int, category: OfferCategory) -> bool:
    """Проверить, управляет ли пользователь определенной категорией в ЖК"""
    stmt = (select(JKServiceProvider.id)
            .where(JKServiceProvider.responsible_user_id == user_id)
            .where(JKServiceProvider.jk_id == jk_id)
            .where(JKServiceProvider.category == category)
            .where(JKServiceProvider.is_active == True))
    
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def orm_get_categories_managed_by_user(session: AsyncSession, user_id: int, 
                                           jk_id: int) -> List[OfferCategory]:
    """Получить список категорий, которыми управляет пользователь в ЖК"""
    stmt = (select(JKServiceProvider.category)
            .where(JKServiceProvider.responsible_user_id == user_id)
            .where(JKServiceProvider.jk_id == jk_id)
            .where(JKServiceProvider.is_active == True))
    
    result = await session.execute(stmt)
    return result.scalars().all()


async def orm_get_working_providers_now(session: AsyncSession, jk_id: int) -> List[JKServiceProvider]:
    """Получить поставщиков услуг, которые работают сейчас"""
    providers = await orm_get_service_providers_by_jk(session, jk_id, active_only=True)
    return [provider for provider in providers if provider.is_working_now()]
