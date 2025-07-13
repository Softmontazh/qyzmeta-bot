# coding: utf-8
# database/models/orm_user.py

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.model_user import User


async def orm_add_user(session: AsyncSession, data: dict):
    """Добавление нового пользователя в базу данных."""
    obj = User(
        user_id=data["user_id"],
        first_name=data["first_name"],
        last_name=data.get("last_name", None),
        username=data.get("username", None),
        user_language=data.get("user_language", "RU"),
        is_bot=data.get("is_bot", False),
        is_premium=data.get("is_premium", False),
        is_business=data.get("is_business", False),
        role=data.get("role", "GUEST"),
        phone=data.get("phone", None),
        email=data.get("email", None),
        city=data.get("city", None),
        is_banned=data.get("is_banned", False),
        is_blocked=data.get("is_blocked", False),
        is_blocked_by_admin=data.get("is_blocked_by_admin", False),
        is_subscribed_to_channel=data.get("is_subscribed_to_channel", False),
        is_subscribed_to_group=data.get("is_subscribed_to_group", False),
        subscription_expires_at=data.get("subscription_expires_at", None),
        last_active=data.get("last_active", None),
        wants_notifications=data.get("wants_notifications", True),
        invited_by_id=data.get("invited_by_id", None),
        lots=data.get("lots", []),  # Список лотов пользователя
        # limited_lots=data.get(
        #     "limited_lots", 0
        # ),  # Количество лотов, доступных пользователю
    )
    session.add(obj)
    # Commit убран - middleware автоматически сделает commit
    await session.flush()  # Используем flush для получения ID


async def orm_get_user_by_id(session: AsyncSession, user_id: int):
    """Получение пользователя по его ID."""
    query = select(User)
    result = await session.execute(query.where(User.user_id == user_id))
    return (
        result.scalar_one_or_none()
    )  # Возвращает пользователя или None, если не найден


async def orm_update_user_role(session: AsyncSession, user_id: int, new_role):
    """Обновление роли пользователя."""
    from database.enums.user_enums import UserRole

    # Если передан строковый enum, преобразуем в объект
    if isinstance(new_role, str):
        new_role = UserRole(new_role)

    stmt = update(User).where(User.user_id == user_id).values(role=new_role)
    result = await session.execute(stmt)

    # Проверяем, был ли обновлен хотя бы один пользователь
    if result.rowcount == 0:
        raise ValueError(f"Пользователь с ID {user_id} не найден")

    return result.rowcount


async def orm_get_user_role(session: AsyncSession, user_id: int):
    """Получение роли пользователя по его ID."""
    query = select(User.role)
    result = await session.execute(query.where(User.user_id == user_id))
    return result.scalar_one_or_none()  # Возвращает роль или None, если не найден
