# -*- coding: utf-8 -*-
# database/models/orm_subscription_price.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict
from datetime import datetime, timezone

from database.models.model_subscription_price import SubscriptionPrice
from database.enums.subscription_enums import SubscriptionTier


async def orm_get_active_prices(session: AsyncSession) -> List[SubscriptionPrice]:
    """Получить все активные цены"""
    stmt = select(SubscriptionPrice).where(
        SubscriptionPrice.is_active == True
    ).order_by(SubscriptionPrice.tier)
    
    result = await session.execute(stmt)
    return result.scalars().all()


async def orm_get_price_by_tier(
    session: AsyncSession, 
    tier: SubscriptionTier
) -> Optional[SubscriptionPrice]:
    """Получить активную цену для конкретного тарифа"""
    stmt = select(SubscriptionPrice).where(
        and_(
            SubscriptionPrice.tier == tier.value,
            SubscriptionPrice.is_active == True
        )
    ).order_by(desc(SubscriptionPrice.created_at))
    
    result = await session.execute(stmt)
    return result.scalars().first()


async def orm_get_price_history(
    session: AsyncSession,
    tier: Optional[SubscriptionTier] = None,
    limit: int = 50
) -> List[SubscriptionPrice]:
    """Получить историю изменений цен"""
    stmt = select(SubscriptionPrice)
    
    if tier:
        stmt = stmt.where(SubscriptionPrice.tier == tier.value)
    
    stmt = stmt.order_by(desc(SubscriptionPrice.created_at)).limit(limit)
    
    result = await session.execute(stmt)
    return result.scalars().all()


async def orm_create_price(
    session: AsyncSession,
    tier: SubscriptionTier,
    price: int,
    created_by: int,
    notes: Optional[str] = None
) -> SubscriptionPrice:
    """Создать новую цену (деактивирует предыдущую)"""
    
    # Деактивируем все предыдущие цены для этого тарифа
    await session.execute(
        update(SubscriptionPrice)
        .where(
            and_(
                SubscriptionPrice.tier == tier.value,
                SubscriptionPrice.is_active == True
            )
        )
        .values(is_active=False)
    )
    
    # Создаем новую цену
    new_price = SubscriptionPrice(
        tier=tier.value,
        price=price,
        is_active=True,
        created_by=created_by,
        notes=notes
    )
    
    session.add(new_price)
    await session.commit()
    await session.refresh(new_price)
    
    return new_price


async def orm_update_price(
    session: AsyncSession,
    tier: SubscriptionTier,
    new_price: int,
    updated_by: int,
    notes: Optional[str] = None
) -> SubscriptionPrice:
    """Обновить цену тарифа"""
    
    # Получаем текущую активную цену
    current_price = await orm_get_price_by_tier(session, tier)
    
    if current_price and current_price.price == new_price:
        # Цена не изменилась
        return current_price
    
    # Создаем новую запись с обновленной ценой
    return await orm_create_price(
        session=session,
        tier=tier,
        price=new_price,
        created_by=updated_by,
        notes=notes or f"Обновление цены с {current_price.price if current_price else 'не установлено'} до {new_price}"
    )


async def orm_get_prices_summary(session: AsyncSession) -> Dict:
    """Получить сводку по ценам"""
    active_prices = await orm_get_active_prices(session)
    
    # Получаем статистику по истории
    stmt = select(SubscriptionPrice).order_by(desc(SubscriptionPrice.created_at))
    result = await session.execute(stmt)
    all_prices = result.scalars().all()
    
    return {
        "active_prices": {price.tier: price.to_dict() for price in active_prices},
        "total_changes": len(all_prices),
        "last_update": all_prices[0].created_at if all_prices else None,
        "tiers_configured": len(active_prices)
    }


async def orm_initialize_default_prices(session: AsyncSession, created_by: int = 0) -> List[SubscriptionPrice]:
    """Инициализировать цены по умолчанию из enum"""
    
    # Проверяем, есть ли уже активные цены
    existing = await orm_get_active_prices(session)
    if existing:
        return existing
    
    default_prices = [
        (SubscriptionTier.FREE, 0),
        (SubscriptionTier.BASIC, 2990),
        (SubscriptionTier.PREMIUM, 4990),
        (SubscriptionTier.VIP, 9990)
    ]
    
    created_prices = []
    for tier, price in default_prices:
        new_price = await orm_create_price(
            session=session,
            tier=tier,
            price=price,
            created_by=created_by,
            notes="Инициализация системы ценообразования"
        )
        created_prices.append(new_price)
    
    return created_prices


async def orm_deactivate_all_prices(session: AsyncSession) -> int:
    """Деактивировать все цены (для экстренных случаев)"""
    stmt = update(SubscriptionPrice).where(
        SubscriptionPrice.is_active == True
    ).values(is_active=False)
    
    result = await session.execute(stmt)
    await session.commit()
    
    return result.rowcount


async def orm_get_tier_price_changes_count(
    session: AsyncSession, 
    tier: SubscriptionTier
) -> int:
    """Получить количество изменений цены для тарифа"""
    stmt = select(SubscriptionPrice).where(SubscriptionPrice.tier == tier.value)
    result = await session.execute(stmt)
    return len(result.scalars().all())
