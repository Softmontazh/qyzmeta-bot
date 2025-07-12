# -*- coding: utf-8 -*-
# debug_roles.py
"""
Скрипт для проверки ролей пользователей
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.abspath('.'))

from database.database import get_session
from database.models.orm_user import orm_get_user_by_id
from database.enums.user_enums import UserRole
from services.service_provider_service import check_service_management_access


async def debug_user_access(user_id: int):
    """Проверяет доступ пользователя"""
    async with get_session() as session:
        # Получаем пользователя
        user = await orm_get_user_by_id(session, user_id)
        if not user:
            print(f"❌ Пользователь {user_id} не найден")
            return
        
        print(f"👤 Пользователь: {user.first_name} {user.last_name}")
        print(f"🎭 Роль: {user.role}")
        print(f"🎭 Тип роли: {type(user.role)}")
        print(f"🔍 Роль в перечислении CREATOR: {UserRole.CREATOR}")
        print(f"🔍 Роль равна CREATOR: {user.role == UserRole.CREATOR}")
        print(f"🔍 Роль в списке [ADMIN, SUPERADMIN, CREATOR]: {user.role in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.CREATOR]}")
        
        # Проверяем доступ
        has_access, error_msg = await check_service_management_access(user_id, session)
        print(f"🚪 Доступ: {has_access}")
        if not has_access:
            print(f"❌ Ошибка: {error_msg}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
        asyncio.run(debug_user_access(user_id))
    else:
        print("Использование: python debug_roles.py <user_id>")
