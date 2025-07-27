# -*- coding: utf-8 -*-
# database/models/orm_user_subscription.py

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_, or_, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.model_user_subscription import UserSubscription
from database.models.model_user_jk import UserJK
from database.enums.subscription_enums import SubscriptionTier, SubscriptionStatus


async def orm_get_user_subscription(
    session: AsyncSession, 
    user_id: int
) -> Optional[UserSubscription]:
    """Получить текущую активную подписку пользователя"""
    stmt = select(UserSubscription).where(
        UserSubscription.user_id == user_id,
        UserSubscription.status == SubscriptionStatus.ACTIVE
    ).order_by(UserSubscription.created_at.desc())
    
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def orm_create_user_subscription(
    session: AsyncSession,
    user_id: int,
    tier: SubscriptionTier = SubscriptionTier.FREE,
    duration_days: Optional[int] = None,
    payment_info: Optional[str] = None,
    notes: Optional[str] = None
) -> UserSubscription:
    """Создать новую подписку для пользователя"""
    
    # Деактивируем старые подписки
    await orm_deactivate_user_subscriptions(session, user_id)
    
    # Расчет даты истечения
    expires_at = None
    if duration_days and tier != SubscriptionTier.FREE:
        expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)
    
    # Создаем новую подписку
    subscription = UserSubscription(
        user_id=user_id,
        tier=tier,
        status=SubscriptionStatus.ACTIVE,
        max_addresses=tier.get_address_limit(),
        expires_at=expires_at,
        payment_info=payment_info,
        notes=notes
    )
    
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)
    
    return subscription


async def orm_deactivate_user_subscriptions(
    session: AsyncSession, 
    user_id: int
) -> None:
    """Деактивировать все активные подписки пользователя"""
    stmt = update(UserSubscription).where(
        UserSubscription.user_id == user_id,
        UserSubscription.status == SubscriptionStatus.ACTIVE
    ).values(
        status=SubscriptionStatus.CANCELLED,
        updated_at=func.now()
    )
    
    await session.execute(stmt)
    await session.commit()


async def orm_check_address_limit(
    session: AsyncSession, 
    user_id: int
) -> Tuple[int, int]:
    """Проверить лимит адресов пользователя
    
    Returns:
        tuple: (current_count, max_allowed)
    """
    # Получаем текущее количество адресов
    current_count_stmt = select(func.count(UserJK.id)).where(
        UserJK.user_id == user_id
    )
    current_result = await session.execute(current_count_stmt)
    current_count = current_result.scalar() or 0
    
    # Получаем лимит из подписки
    subscription = await orm_get_user_subscription(session, user_id)
    
    if subscription and subscription.is_active:
        max_allowed = subscription.max_addresses
    else:
        # Если нет активной подписки - бесплатный тариф
        max_allowed = SubscriptionTier.FREE.get_address_limit()
    
    return current_count, max_allowed


async def orm_can_register_address(
    session: AsyncSession, 
    user_id: int
) -> bool:
    """Проверить, может ли пользователь зарегистрировать новый адрес"""
    current_count, max_allowed = await orm_check_address_limit(session, user_id)
    return current_count < max_allowed


async def orm_get_all_subscriptions(
    session: AsyncSession,
    status: Optional[SubscriptionStatus] = None,
    tier: Optional[SubscriptionTier] = None,
    limit: int = 100,
    offset: int = 0
) -> List[UserSubscription]:
    """Получить все подписки с фильтрацией (для админ панели)"""
    stmt = select(UserSubscription)
    
    # Фильтры
    if status:
        stmt = stmt.where(UserSubscription.status == status)
    if tier:
        stmt = stmt.where(UserSubscription.tier == tier)
    
    stmt = stmt.order_by(
        UserSubscription.created_at.desc()
    ).limit(limit).offset(offset)
    
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def orm_get_subscriptions_count(
    session: AsyncSession,
    status: Optional[SubscriptionStatus] = None,
    tier: Optional[SubscriptionTier] = None
) -> int:
    """Получить количество подписок с фильтрацией"""
    stmt = select(func.count(UserSubscription.id))
    
    if status:
        stmt = stmt.where(UserSubscription.status == status)
    if tier:
        stmt = stmt.where(UserSubscription.tier == tier)
    
    result = await session.execute(stmt)
    return result.scalar() or 0


async def orm_get_expiring_subscriptions(
    session: AsyncSession,
    days_before: int = 3
) -> List[UserSubscription]:
    """Получить подписки, которые истекают в ближайшие N дней"""
    expiry_date = datetime.now(timezone.utc) + timedelta(days=days_before)
    
    stmt = select(UserSubscription).where(
        and_(
            UserSubscription.status == SubscriptionStatus.ACTIVE,
            UserSubscription.expires_at.is_not(None),
            UserSubscription.expires_at <= expiry_date
        )
    )
    
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def orm_update_subscription_tier(
    session: AsyncSession,
    user_id: int,
    new_tier: SubscriptionTier,
    duration_days: Optional[int] = None,
    payment_info: Optional[str] = None,
    notes: Optional[str] = None
) -> UserSubscription:
    """Обновить тариф пользователя"""
    subscription = await orm_get_user_subscription(session, user_id)
    
    if not subscription:
        # Создаем новую подписку
        return await orm_create_user_subscription(
            session, user_id, new_tier, duration_days, payment_info, notes
        )
    
    # Обновляем существующую
    subscription.tier = new_tier
    subscription.max_addresses = new_tier.get_address_limit()
    
    if duration_days and new_tier != SubscriptionTier.FREE:
        subscription.expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)
    elif new_tier == SubscriptionTier.FREE:
        subscription.expires_at = None
    
    if payment_info:
        subscription.payment_info = payment_info
    if notes:
        subscription.notes = notes
    
    subscription.updated_at = func.now()
    
    await session.commit()
    await session.refresh(subscription)
    
    return subscription


async def orm_get_subscription_statistics(
    session: AsyncSession
) -> dict:
    """Получить статистику по подпискам"""
    
    # Статистика по тарифам
    tier_stats = {}
    for tier in SubscriptionTier:
        count = await orm_get_subscriptions_count(
            session, status=SubscriptionStatus.ACTIVE, tier=tier
        )
        tier_stats[tier.value] = {
            "count": count,
            "name": tier.get_russian_name(),
            "monthly_revenue": count * tier.get_monthly_price()
        }
    
    # Общая статистика
    total_active = await orm_get_subscriptions_count(
        session, status=SubscriptionStatus.ACTIVE
    )
    total_expired = await orm_get_subscriptions_count(
        session, status=SubscriptionStatus.EXPIRED
    )
    total_cancelled = await orm_get_subscriptions_count(
        session, status=SubscriptionStatus.CANCELLED
    )
    
    # Подписки, истекающие в ближайшие 7 дней
    expiring_soon = await orm_get_expiring_subscriptions(session, 7)
    
    # Месячный доход
    monthly_revenue = sum(
        stats["monthly_revenue"] for stats in tier_stats.values()
    )
    
    return {
        "tier_stats": tier_stats,
        "total_active": total_active,
        "total_expired": total_expired,
        "total_cancelled": total_cancelled,
        "expiring_soon": len(expiring_soon),
        "monthly_revenue": monthly_revenue
    }


async def orm_search_user_subscription(
    session: AsyncSession,
    search_query: str
) -> List[UserSubscription]:
    """Поиск подписки по user_id"""
    try:
        # Пытаемся найти по user_id
        user_id = int(search_query)
        subscription = await orm_get_user_subscription(session, user_id)
        return [subscription] if subscription else []
    except ValueError:
        # Если не число, возвращаем пустой список
        return []


async def orm_expire_overdue_subscriptions(session: AsyncSession) -> int:
    """Автоматически истечь просроченные подписки"""
    now = datetime.now(timezone.utc)
    
    stmt = update(UserSubscription).where(
        and_(
            UserSubscription.status == SubscriptionStatus.ACTIVE,
            UserSubscription.expires_at.is_not(None),
            UserSubscription.expires_at <= now
        )
    ).values(
        status=SubscriptionStatus.EXPIRED,
        updated_at=func.now()
    )
    
    result = await session.execute(stmt)
    await session.commit()
    
    return result.rowcount or 0
