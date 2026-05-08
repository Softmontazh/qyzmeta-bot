#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Миграция для исправления типа поля created_by в subscription_prices
INTEGER -> BIGINT для поддержки больших Telegram user_id
"""

import asyncio
import asyncpg
from database.engine import session_maker
from sqlalchemy import text


async def migrate_created_by_field():
    """Изменить тип поля created_by с INTEGER на BIGINT"""
    print("🔄 Начинаем миграцию поля created_by...")

    async with session_maker() as session:
        try:
            # Изменяем тип колонки на BIGINT
            await session.execute(
                text(
                    "ALTER TABLE subscription_prices ALTER COLUMN created_by TYPE BIGINT"
                )
            )

            await session.commit()
            print("✅ Миграция успешно завершена!")
            print("📊 Поле created_by теперь поддерживает большие Telegram user_id")

        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка при миграции: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate_created_by_field())
