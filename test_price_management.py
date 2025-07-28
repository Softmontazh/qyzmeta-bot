# -*- coding: utf-8 -*-
# test_price_management.py
"""
Тестовый скрипт для проверки системы управления ценами
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

from database.engine import session_maker
from services.price_management_service import PriceManagementService
from database.enums.subscription_enums import SubscriptionTier


async def test_price_management():
    """Тестирование системы управления ценами"""
    
    async with session_maker() as session:
        print("🧪 Тестирование системы управления ценами\n")
        
        # 1. Получаем текущие цены
        print("1️⃣ Текущие цены:")
        current_prices = await PriceManagementService.get_current_prices(session)
        for tier_value, price_data in current_prices.items():
            print(f"   {price_data['tier_display']}: {price_data['formatted_price']}")
        
        # 2. Получаем сводку управления
        print("\n2️⃣ Сводка управления:")
        summary = await PriceManagementService.get_management_summary(session)
        stats = summary["statistics"]
        print(f"   Всего тарифов: {stats['total_tiers']}")
        print(f"   Настроено цен: {stats['configured_tiers']}")
        print(f"   Общий потенциал: {stats['revenue_potential']:,} ₸/мес")
        print(f"   Изменений всего: {stats['total_changes']}")
        
        # 3. Получаем историю изменений
        print("\n3️⃣ История изменений (последние 5):")
        history = await PriceManagementService.get_price_history(session, limit=5)
        if history:
            for i, record in enumerate(history, 1):
                date_str = record["created_at"].strftime("%d.%m.%Y %H:%M")
                tier_name = record["tier_display"]
                price_text = f"{record['price']:,} ₸" if record['price'] > 0 else "Отключен"
                print(f"   {i}. {tier_name} → {price_text} ({date_str})")
        else:
            print("   История пуста")
        
        # 4. Тестируем валидацию цен
        print("\n4️⃣ Тестирование валидации:")
        test_cases = ["2990", "5000", "-100", "abc", "150000", "0"]
        for test_price in test_cases:
            is_valid, price, error = PriceManagementService.validate_price_input(test_price)
            status = "✅" if is_valid else "❌"
            result = f"{price:,} ₸" if is_valid else error
            print(f"   {status} '{test_price}' → {result}")
        
        # 5. Проверяем получение цены конкретного тарифа
        print("\n5️⃣ Цены по тарифам:")
        for tier in SubscriptionTier:
            price = await PriceManagementService.get_tier_price(session, tier)
            print(f"   {tier.get_russian_name()}: {price:,} ₸")
        
        print("\n✅ Тестирование завершено!")


if __name__ == "__main__":
    asyncio.run(test_price_management())
