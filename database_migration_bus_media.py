# -*- coding: utf-8 -*-
# database_migration_bus_media.py
"""
Скрипт для добавления поля bus_media_id в таблицу offers.
"""

import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные окружения ПЕРЕД импортом database
load_dotenv()

from sqlalchemy import text
from database.engine import session_maker


async def add_bus_media_id_column():
    """Добавляет колонку bus_media_id в таблицу offers."""
    async with session_maker() as session:
        try:
            # Проверяем, существует ли уже колонка
            check_column_query = text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'offers' 
                AND column_name = 'bus_media_id'
            """)
            
            result = await session.execute(check_column_query)
            column_exists = result.scalar() > 0
            
            if column_exists:
                print("✅ Колонка bus_media_id уже существует в таблице offers")
                return
            
            # Добавляем колонку
            add_column_query = text("""
                ALTER TABLE offers 
                ADD COLUMN bus_media_id VARCHAR(20) NULL
            """)
            
            await session.execute(add_column_query)
            await session.commit()
            
            print("✅ Колонка bus_media_id успешно добавлена в таблицу offers")
            
            # Добавляем индекс для лучшей производительности
            add_index_query = text("""
                CREATE INDEX IF NOT EXISTS idx_offers_bus_media_id 
                ON offers(bus_media_id)
            """)
            
            await session.execute(add_index_query)
            await session.commit()
            
            print("✅ Индекс для bus_media_id успешно создан")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка при добавлении колонки: {e}")
            raise


async def main():
    """Главная функция миграции."""
    print("🚀 Запуск миграции для добавления поддержки BUS медиа...")
    
    try:
        await add_bus_media_id_column()
        print("✅ Миграция успешно завершена!")
        print("\n📋 Изменения:")
        print("• Добавлена колонка bus_media_id VARCHAR(20) в таблицу offers")
        print("• Создан индекс idx_offers_bus_media_id для оптимизации запросов")
        print("\n🔧 BUS система готова к использованию!")
        
    except Exception as e:
        print(f"❌ Миграция провалилась: {e}")


if __name__ == "__main__":
    asyncio.run(main())
