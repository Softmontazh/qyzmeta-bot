#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для инициализации бесплатных подписок для существующих пользователей
После добавления системы подписок нужно создать FREE подписки для всех пользователей
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.engine import get_sessionmaker
from database.models.model_user import User
from database.models.orm_user_subscription import orm_create_user_subscription
from database.enums.subscription_enums import SubscriptionTier
from database.models.orm_user_jk import orm_check_address_limit


async def initialize_free_subscriptions():
    """Создать бесплатные подписки для всех существующих пользователей"""
    
    async for session in get_sessionmaker():
        # Получаем всех пользователей
        stmt = select(User)
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        print(f"🔍 Найдено пользователей: {len(users)}")
        
        created_count = 0
        
        for user in users:
            try:
                # Проверяем, есть ли уже подписка
                from database.models.orm_user_subscription import orm_get_user_subscription
                existing_subscription = await orm_get_user_subscription(session, user.user_id)
                
                if existing_subscription:
                    print(f"⏭️  Пользователь {user.user_id} уже имеет подписку, пропускаем")
                    continue
                
                # Создаем бесплатную подписку
                subscription = await orm_create_user_subscription(
                    session=session,
                    user_id=user.user_id,
                    tier=SubscriptionTier.FREE,
                    notes="Создано автоматически при инициализации системы подписок"
                )
                
                created_count += 1
                print(f"✅ Создана подписка для пользователя {user.user_id} ({user.first_name})")
                
            except Exception as e:
                print(f"❌ Ошибка для пользователя {user.user_id}: {e}")
                continue
        
        print(f"\n🎉 Инициализация завершена!")
        print(f"📊 Создано подписок: {created_count}")
        print(f"👥 Всего пользователей: {len(users)}")
        
        # Завершаем транзакцию
        break


async def check_address_limits():
    """Проверить соответствие лимитов адресов"""
    
    async for session in get_sessionmaker():
        # Получаем всех пользователей с подписками
        from database.models.orm_user_subscription import orm_get_all_subscriptions
        from database.enums.subscription_enums import SubscriptionStatus
        
        subscriptions = await orm_get_all_subscriptions(
            session, 
            status=SubscriptionStatus.ACTIVE,
            limit=1000
        )
        
        print(f"\n🔍 Проверка лимитов адресов для {len(subscriptions)} подписок...")
        
        violations = []
        
        for subscription in subscriptions:
            current_count, max_allowed = await orm_check_address_limit(
                session, subscription.user_id
            )
            
            if current_count > max_allowed:
                violations.append({
                    'user_id': subscription.user_id,
                    'tier': subscription.tier,
                    'current': current_count,
                    'max': max_allowed,
                    'excess': current_count - max_allowed
                })
                
                print(f"⚠️  Нарушение лимита: Пользователь {subscription.user_id}")
                print(f"    Тариф: {subscription.tier.get_russian_name()}")
                print(f"    Адресов: {current_count}/{max_allowed} (превышение: {current_count - max_allowed})")
        
        if not violations:
            print("✅ Все лимиты соблюдаются!")
        else:
            print(f"\n⚠️  Найдено нарушений: {len(violations)}")
            print("💡 Рекомендуется обновить тарифы для этих пользователей")
        
        # Завершаем транзакцию
        break


async def main():
    """Главная функция"""
    print("🚀 Инициализация системы подписок")
    print("=" * 50)
    
    # Инициализируем подписки
    await initialize_free_subscriptions()
    
    # Проверяем лимиты
    await check_address_limits()
    
    print("\n✨ Готово! Система подписок готова к работе")


if __name__ == "__main__":
    asyncio.run(main())
