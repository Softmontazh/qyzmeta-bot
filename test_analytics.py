#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки аналитики подписок
"""

import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

from database.engine import session_maker
from services.subscription_service import SubscriptionService
from database.models.orm_user import orm_get_total_users_count


async def test_subscription_analytics():
    """Тестирование аналитики подписок"""
    print("🔍 Тестирование аналитики подписок...")
    
    async with session_maker() as session:
        try:
            # Тест 1: Общее количество пользователей
            print("\n📊 Тест 1: Общее количество пользователей")
            total_users = await orm_get_total_users_count(session)
            print(f"Общее количество пользователей: {total_users}")
            
            # Тест 2: Полная аналитика
            print("\n📊 Тест 2: Полная аналитика подписок")
            analytics = await SubscriptionService.get_subscription_analytics(session)
            
            print(f"👥 Всего пользователей: {analytics['total_users']}")
            print(f"💳 Активных подписок: {analytics['active_subscriptions']}")
            print(f"🆓 Бесплатных пользователей: {analytics['free_users']}")
            print(f"💰 Общая выручка: {analytics['revenue']:,} ₸/мес")
            print(f"📈 Коэффициент конверсии: {analytics['conversion_rate']:.1f}%")
            
            print("\n📋 Разбивка по тарифам:")
            for tier_data in analytics['by_tier']:
                print(f"• {tier_data['tier_display']}: {tier_data['count']} ({tier_data['percentage']:.1f}%) - {tier_data['revenue']:,} ₸/мес")
            
            print("\n✅ Тест аналитики завершен успешно!")
            
        except Exception as e:
            print(f"❌ Ошибка при тестировании аналитики: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_subscription_analytics())
