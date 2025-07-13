# -*- coding: utf-8 -*-
# database/models/orm_jk_service_provider.py

from typing import Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from database.models.model_jk_service_provider import JKServiceProvider
from database.enums.offer_category_enum import OfferCategory


async def orm_add_service_provider(session: AsyncSession, service_data: dict) -> JKServiceProvider:
    """Добавить нового поставщика услуг для ЖК БЕЗ изменения роли"""
    
    # ПРИНУДИТЕЛЬНО УСТАНАВЛИВАЕМ is_active=False
    service_data['is_active'] = False
    
    # Создаем поставщика услуг
    service_provider = JKServiceProvider(**service_data)
    
    session.add(service_provider)
    await session.flush()
    await session.refresh(service_provider)

    # УБИРАЕМ ВЕСЬ БЛОК АВТОМАТИЧЕСКОГО ИЗМЕНЕНИЯ РОЛИ
    # Роль будет изменена только при активации администратором
    
    return service_provider


async def orm_get_service_provider_by_id(session: AsyncSession, provider_id: int) -> Optional[JKServiceProvider]:
    """Получить поставщика услуг по ID"""
    stmt = select(JKServiceProvider).where(JKServiceProvider.id == provider_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def orm_get_service_provider_by_id_with_jk(session: AsyncSession, provider_id: int) -> Optional[JKServiceProvider]:
    """Получить поставщика услуг по ID с загруженным ЖК"""
    stmt = select(JKServiceProvider).where(
        JKServiceProvider.id == provider_id
    ).options(
        selectinload(JKServiceProvider.jk)
    )
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


async def orm_get_user_service_provider_requests(session: AsyncSession, user_id: int) -> List[JKServiceProvider]:
    """Получить все заявки пользователя на статус поставщика услуг"""
    stmt = select(JKServiceProvider).where(
        JKServiceProvider.responsible_user_id == user_id
    ).options(selectinload(JKServiceProvider.jk))
    
    result = await session.execute(stmt)
    return result.scalars().all()


async def orm_create_service_provider_request(
    session: AsyncSession,
    jk_id: int,
    category: str,
    responsible_user_id: int,
    organization_name: str,
    contact_phone: str,
    contact_email: Optional[str] = None,
    description: Optional[str] = None,
    is_active: bool = False
) -> int:
    """Создать заявку на статус поставщика услуг БЕЗ изменения роли пользователя"""
    
    service_provider = JKServiceProvider(
        jk_id=jk_id,
        category=OfferCategory.from_string(category),
        responsible_user_id=responsible_user_id,
        organization_name=organization_name,
        contact_phone=contact_phone,
        contact_email=contact_email,
        description=description,
        is_active=False,  # ПРИНУДИТЕЛЬНО FALSE
        receives_notifications=True,
        auto_assign_offers=True,
        priority=1,
        created_by_user_id=responsible_user_id
    )
    
    session.add(service_provider)
    await session.flush()
    await session.refresh(service_provider)

    # НЕ МЕНЯЕМ РОЛЬ - только создаем заявку
    # Роль будет изменена администратором при активации
    
    return service_provider.id


async def orm_activate_service_provider_request(
    session: AsyncSession, 
    provider_id: int, 
    activated_by_user_id: int
) -> bool:
    """Активировать заявку поставщика услуг и изменить роль пользователя"""
    from database.models.orm_user import orm_update_user_role, orm_get_user_by_id
    from database.enums.user_enums import UserRole
    from datetime import datetime
    import os
    
    # Получаем заявку
    provider = await orm_get_service_provider_by_id(session, provider_id)
    if not provider or provider.is_active:
        return False
    
    # Активируем заявку
    stmt = update(JKServiceProvider).where(
        JKServiceProvider.id == provider_id
    ).values(
        is_active=True,
        updated_at=datetime.utcnow()
    )
    
    result = await session.execute(stmt)
    if result.rowcount == 0:
        return False
    
    # МЕНЯЕМ РОЛЬ ПОЛЬЗОВАТЕЛЯ НА SERVICE_PROVIDER
    try:
        # Проверяем, не является ли пользователь создателем по CREATOR_ID
        creator_ids = os.getenv("CREATOR_ID")
        is_creator_by_env = creator_ids and str(provider.responsible_user_id) in creator_ids.split(",")
        
        if is_creator_by_env:
            print(f"Пользователь {provider.responsible_user_id} является создателем - роль не изменена")
            return True
        
        # Получаем пользователя
        user = await orm_get_user_by_id(session, provider.responsible_user_id)
        if not user:
            return False
        
        # Список ролей, которые НЕ нужно менять
        admin_roles = {
            UserRole.CREATOR,
            UserRole.ADMIN, 
            UserRole.SUPERADMIN,
            UserRole.MODERATOR,
            UserRole.MANAGER
        }
        
        # Меняем роль только если это USER
        if user.role not in admin_roles:
            await orm_update_user_role(
                session, 
                provider.responsible_user_id, 
                UserRole.SERVICE_PROVIDER
            )
            print(f"Роль пользователя {provider.responsible_user_id} изменена на SERVICE_PROVIDER")
        
        return True
        
    except Exception as e:
        print(f"Ошибка при изменении роли: {e}")
        return False


async def orm_reject_service_provider_request(
    session: AsyncSession, 
    provider_id: int, 
    rejected_by_user_id: int
) -> bool:
    """Отклонить заявку поставщика услуг"""
    
    # Удаляем заявку из базы
    stmt = delete(JKServiceProvider).where(JKServiceProvider.id == provider_id)
    result = await session.execute(stmt)
    
    return result.rowcount > 0


async def orm_get_pending_service_provider_requests(
    session: AsyncSession,
    jk_id: Optional[int] = None
) -> List[JKServiceProvider]:
    """Получить все заявки в ожидании одобрения (is_active = false)"""
    
    stmt = select(JKServiceProvider).where(
        JKServiceProvider.is_active == False
    ).options(
        selectinload(JKServiceProvider.jk)
    ).order_by(JKServiceProvider.created_at.desc())
    
    if jk_id:
        stmt = stmt.where(JKServiceProvider.jk_id == jk_id)
    
    result = await session.execute(stmt)
    pending_requests = result.scalars().all()
    
    return pending_requests
