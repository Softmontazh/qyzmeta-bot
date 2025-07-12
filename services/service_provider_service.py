# -*- coding: utf-8 -*-
# services/service_provider_service.py
"""
Сервис для работы с поставщиками услуг.
"""

from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.orm_user import orm_get_user_by_id
from database.models.orm_user_jk import orm_get_jks_by_user_admin
from database.enums.user_enums import UserRole


async def check_service_management_access(user_id: int, session: AsyncSession, jk_id: Optional[int] = None) -> tuple[bool, str]:
    """
    Проверяет права пользователя на управление поставщиками услуг.
    
    Args:
        user_id: ID пользователя
        session: Сессия БД
        jk_id: ID ЖК (если нужна проверка для конкретного ЖК)
    
    Returns:
        Tuple[bool, str]: (имеет доступ, сообщение об ошибке)
    """
    # Получаем пользователя
    user = await orm_get_user_by_id(session, user_id)
    if not user:
        return False, "❌ Пользователь не найден"
    
    # Проверяем роль пользователя
    if user.role not in [UserRole.ADMIN, UserRole.ADMIN_JK]:
        return False, "❌ У вас недостаточно прав для управления поставщиками услуг"
    
    # Если пользователь - суперадмин, доступ ко всему
    if user.role == UserRole.ADMIN:
        return True, ""
    
    # Если администратор ЖК, проверяем доступ к конкретному ЖК
    if user.role == UserRole.ADMIN_JK:
        if jk_id is None:
            # Если ЖК не указан, получаем список доступных ЖК
            jks = await orm_get_jks_by_user_admin(session, user_id)
            if not jks:
                return False, "❌ У вас нет прав администратора ни в одном ЖК"
            return True, ""
        else:
            # Проверяем доступ к конкретному ЖК
            jks = await orm_get_jks_by_user_admin(session, user_id)
            accessible_jk_ids = [jk.id for jk in jks]
            if jk_id not in accessible_jk_ids:
                return False, "❌ У вас нет прав для управления этим ЖК"
            return True, ""
    
    return False, "❌ Неизвестная роль пользователя"


async def validate_responsible_user(user_id: int, session: AsyncSession) -> tuple[bool, str, Optional[dict]]:
    """
    Валидирует ответственного пользователя для поставщика услуг.
    
    Args:
        user_id: ID пользователя
        session: Сессия БД
    
    Returns:
        Tuple[bool, str, Optional[dict]]: (валиден, сообщение, данные пользователя)
    """
    # Проверяем, что пользователь существует
    user = await orm_get_user_by_id(session, user_id)
    if not user:
        return False, f"❌ Пользователь с ID {user_id} не найден в базе данных", None
    
    # Формируем информацию о пользователе
    user_info = {
        'user_id': user.user_id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username,
        'phone': user.phone,
        'role': user.role
    }
    
    return True, "", user_info


def validate_organization_name(org_name: str) -> tuple[bool, str]:
    """
    Валидирует название организации.
    
    Args:
        org_name: Название организации
    
    Returns:
        Tuple[bool, str]: (валидно, сообщение об ошибке)
    """
    if not org_name or not org_name.strip():
        return False, "❌ Название организации не может быть пустым"
    
    org_name = org_name.strip()
    
    if len(org_name) < 3:
        return False, "❌ Название организации должно содержать минимум 3 символа"
    
    if len(org_name) > 200:
        return False, "❌ Название организации слишком длинное (максимум 200 символов)"
    
    return True, ""


def validate_work_schedule(schedule: str) -> tuple[bool, str]:
    """
    Валидирует рабочее расписание.
    
    Args:
        schedule: Рабочее расписание
    
    Returns:
        Tuple[bool, str]: (валидно, сообщение об ошибке)
    """
    if not schedule or not schedule.strip():
        return False, "❌ Рабочее время не может быть пустым"
    
    schedule = schedule.strip()
    
    if len(schedule) < 5:
        return False, "❌ Рабочее время должно содержать минимум 5 символов"
    
    if len(schedule) > 100:
        return False, "❌ Рабочее время слишком длинное (максимум 100 символов)"
    
    return True, ""
