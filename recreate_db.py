# -*- coding: utf-8 -*-
"""
Скрипт для пересоздания базы данных с правильными enum значениями.
Удаляет все таблицы и создает их заново.
"""

import asyncio
from database.engine import drop_db, create_db
from database.engine import session_maker
from database.models.model_lot_limit import LotLimit
from database.enums.user_enums import UserRole


async def init_lot_limits(session):
    """Инициализация лимитов лотов для всех ролей"""
    lot_limits = [
        (UserRole.GUEST, 0),
        (UserRole.USER, 10),
        (UserRole.ADMIN, 100),
        (UserRole.CREATOR, 1000000),
        (UserRole.OWNER, 1000000),
        (UserRole.SUPERADMIN, 100),
        (UserRole.MODERATOR, 100),
        (UserRole.SUPPORT, 100),
        (UserRole.MANAGER, 1000),
        (UserRole.PARTNER, 10000),
        (UserRole.SERVICE_PROVIDER, 50),  # ✅ Добавляем лимит для поставщиков услуг
    ]
    
    for role, limit in lot_limits:
        lot_limit = LotLimit(role=role, limit=limit)
        session.add(lot_limit)
    
    await session.commit()
    print(f"✅ Добавлено {len(lot_limits)} лимитов лотов")


async def recreate_database():
    """Главная функция пересоздания базы данных"""
    print("🗑️ Удаляем все таблицы...")
    await drop_db()
    print("✅ Таблицы удалены")
    
    print("🏗️ Создаем таблицы заново...")
    await create_db()
    print("✅ Таблицы созданы")
    
    print("📝 Инициализируем базовые данные...")
    async with session_maker() as session:
        await init_lot_limits(session)
    
    print("🎉 База данных успешно пересоздана!")
    print("🔧 Теперь можно протестировать создание поставщика услуг")


if __name__ == "__main__":
    asyncio.run(recreate_database())
