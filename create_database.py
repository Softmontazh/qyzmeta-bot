# -*- coding: utf-8 -*-
# create_database.py
"""
Скрипт для создания всех таблиц базы данных.
"""

import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные окружения ПЕРЕД импортом database
load_dotenv()

from database.engine import create_db


async def main():
    """Создание всех таблиц."""
    print("🚀 Создание таблиц базы данных...")
    
    try:
        await create_db()
        print("✅ Все таблицы успешно созданы!")
        
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")


if __name__ == "__main__":
    asyncio.run(main())
