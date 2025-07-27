#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для создания новых таблиц в базе данных
Включая таблицу user_subscriptions для системы подписок
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.engine import create_db


async def create_tables():
    """Создать все таблицы в базе данных"""
    print("🚀 Создание таблиц в базе данных...")
    
    try:
        await create_db()
        print("✅ Все таблицы успешно созданы!")
        print("📊 Включая новую таблицу user_subscriptions для системы подписок")
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        return False
    
    return True


async def main():
    """Главная функция"""
    print("🏗️  Создание структуры базы данных")
    print("=" * 50)
    
    success = await create_tables()
    
    if success:
        print("\n✨ Готово! База данных обновлена")
        print("💡 Теперь можно запустить скрипт инициализации подписок:")
        print("   python scripts/init_subscriptions.py")
    else:
        print("\n❌ Не удалось создать таблицы")
        print("💡 Проверьте подключение к базе данных и переменную DATABASE_URL")


if __name__ == "__main__":
    asyncio.run(main())
