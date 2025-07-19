# -*- coding: utf-8 -*-
# test_bus_integration.py
"""
Тест интеграции BUS системы с заявками.
"""

import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

from database.engine import session_maker
from database.models.orm_offer import orm_add_offer
from services.bus_service import bus_service
from database.enums.offer_enums import OfferStatus


async def test_bus_integration():
    """Тестирует интеграцию BUS с заявками."""
    print("🧪 Тестирование BUS интеграции...")
    
    async with session_maker() as session:
        # Создаем тестовую заявку с BUS медиа
        test_offer_data = {
            "category": "elektrika",
            "title": "Тестовая заявка с BUS медиа",
            "description": "Проверка работы BUS системы для медиафайлов",
            "media_id": "test_original_file_id_12345",
            "bus_media_id": "BUS_ABC123DEF456789A",  # Тестовый BUS_ID
            "user_id": 123456789,
            "user_jk_id": 1,
            "status": OfferStatus.ACTIVE
        }
        
        try:
            offer = await orm_add_offer(session, test_offer_data)
            await session.commit()
            
            print(f"✅ Тестовая заявка создана:")
            print(f"   ID: {offer.id}")
            print(f"   Категория: {offer.category}")
            print(f"   Название: {offer.title}")
            print(f"   Original Media ID: {offer.media_id}")
            print(f"   BUS Media ID: {offer.bus_media_id}")
            print(f"   Статус: {offer.status}")
            
            # Тестируем валидацию BUS_ID
            is_valid = bus_service.validate_bus_id(offer.bus_media_id)
            print(f"   BUS_ID валиден: {'✅' if is_valid else '❌'}")
            
            # Тестируем создание корректного BUS_ID
            test_file_id = "BAADBAADzwADVhFzSaab1L0b4_aLAg"
            generated_bus_id = bus_service.generate_bus_id(test_file_id)
            print(f"   Сгенерированный BUS_ID: {generated_bus_id}")
            print(f"   Длина: {len(generated_bus_id)}")
            print(f"   Валиден: {'✅' if bus_service.validate_bus_id(generated_bus_id) else '❌'}")
            
            print("\n🎯 BUS интеграция готова к использованию!")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка при создании тестовой заявки: {e}")


async def cleanup_test_data():
    """Удаляет тестовые данные."""
    async with session_maker() as session:
        from sqlalchemy import text
        
        try:
            # Удаляем тестовые заявки
            cleanup_query = text("DELETE FROM offers WHERE title LIKE '%Тестовая заявка%'")
            result = await session.execute(cleanup_query)
            await session.commit()
            
            deleted_count = result.rowcount
            if deleted_count > 0:
                print(f"🧹 Удалено {deleted_count} тестовых заявок")
            else:
                print("🧹 Тестовые данные не найдены")
                
        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка при очистке тестовых данных: {e}")


async def main():
    """Главная функция теста."""
    print("🚀 Запуск теста BUS интеграции...")
    
    try:
        await test_bus_integration()
        
        # Опционально очищаем тестовые данные
        print("\n" + "="*50)
        cleanup = input("Очистить тестовые данные? (y/N): ").lower().strip()
        if cleanup in ['y', 'yes', 'да']:
            await cleanup_test_data()
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")


if __name__ == "__main__":
    asyncio.run(main())
