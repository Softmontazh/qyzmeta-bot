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
    from database.models.orm_user import orm_update_user_role
    from database.enums.user_enums import UserRole
    
    # Создаем поставщика услуг
    service_provider = JKServiceProvider(**service_data)
    session.add(service_provider)
    await session.flush()
    
    # Автоматически обновляем роль ответственного пользователя на SERVICE_PROVIDER
    if 'responsible_user_id' in service_data and service_data['responsible_user_id']:
        try:
            from database.models.orm_user import orm_get_user_by_id
            import os
            
            # Проверяем, не является ли пользователь создателем по CREATOR_ID из env
            creator_ids = os.getenv("CREATOR_ID")
            is_creator_by_env = creator_ids and str(service_data['responsible_user_id']) in creator_ids.split(",")
            
            # Если это создатель по env - НЕ меняем роль
            if is_creator_by_env:
                print(f"Пользователь {service_data['responsible_user_id']} является создателем (CREATOR_ID) - роль не изменена")
                return service_provider
            
            # Получаем текущего пользователя
            user = await orm_get_user_by_id(session, service_data['responsible_user_id'])
            
            if user:
                # Список административных ролей, которые НЕ нужно менять
                admin_roles = {
                    UserRole.CREATOR,
                    UserRole.ADMIN, 
                    UserRole.SUPERADMIN,
                    UserRole.MODERATOR,
                    UserRole.MANAGER
                }
                
                # Меняем роль только если это не админ и не уже поставщик услуг
                if user.role not in admin_roles and user.role != UserRole.SERVICE_PROVIDER:
                    await orm_update_user_role(
                        session, 
                        service_data['responsible_user_id'], 
                        UserRole.SERVICE_PROVIDER
                    )
                    print(f"Роль пользователя {service_data['responsible_user_id']} изменена на SERVICE_PROVIDER")
                else:
                    print(f"Роль пользователя {service_data['responsible_user_id']} ({user.role}) не изменена - административная роль")
                    
        except ValueError as e:
            # Если пользователь не найден, логируем ошибку, но не прерываем процесс
            print(f"Предупреждение: не удалось обновить роль пользователя {service_data['responsible_user_id']}: {e}")
    
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
            .where(JKServiceProvider.receives_notifications == True)
            .order_by(JKServiceProvider.priority)  # 1 - наивысший приоритет
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


async def orm_get_service_providers_by_category_and_jk(
    session: AsyncSession, 
    jk_id: int, 
    category: OfferCategory,
    active_only: bool = True
) -> List[JKServiceProvider]:
    """Получить всех поставщиков услуг для конкретной категории в ЖК (с учетом приоритета)"""
    stmt = (select(JKServiceProvider)
            .where(JKServiceProvider.jk_id == jk_id)
            .where(JKServiceProvider.category == category))
    
    if active_only:
        stmt = stmt.where(JKServiceProvider.is_active == True)
        stmt = stmt.where(JKServiceProvider.receives_notifications == True)
    
    # Сортируем по приоритету (1 - наивысший)
    stmt = stmt.order_by(JKServiceProvider.priority)
    
    result = await session.execute(stmt)
    return result.scalars().all()
