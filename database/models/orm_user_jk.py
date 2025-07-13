# coding: utf-8
# database/models/orm_jk.py
"""Модуль для работы с жилыми комплексами (ЖК) в базе данных через ORM SQLAlchemy."""

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.model_jk import JK
from database.models.model_user import User
from database.models.model_user_jk import UserJK


async def orm_add_user_jk(
    session: AsyncSession, user_id: int, jk_id: int, appartment: str
) -> UserJK:
    """Добавление пользователя в ЖК с указанием квартиры."""
    existing = await session.execute(
        select(UserJK).where(
            UserJK.user_id == user_id,
            UserJK.jk_id == jk_id,
            UserJK.appartment == appartment,
        )
    )
    existing = existing.scalars().first()

    if existing:
        return existing
    obj = UserJK(user_id=user_id, jk_id=jk_id, appartment=appartment)

    session.add(obj)
    # Commit убран - middleware автоматически сделает commit
    await session.flush()  # Используем flush для получения ID
    await session.refresh(obj)
    return obj


async def orm_get_user_jk(
    session: AsyncSession, user_id: int, jk_id: int
) -> UserJK | None:
    """Получение привязки пользователя ЖК по user_id"""
    result = await session.execute(
        select(UserJK).where(UserJK.user_id == user_id, UserJK.jk_id == jk_id)
    )
    return result.scalar_one_or_none()


async def orm_delete_user_jk(session: AsyncSession, user_id: int, jk_id: int) -> bool:
    """Удаление привязки пользователя ЖК по user_id"""
    stmt = delete(UserJK).where(UserJK.user_id == user_id, UserJK.jk_id == jk_id)
    result = await session.execute(stmt)
    # Commit убран - middleware автоматически сделает commit
    return result.rowcount > 0  # Возвращает True, если удаление успешно


async def orm_get_jks_by_user_id(session: AsyncSession, user_id: int):
    """Получение списка ЖК, к которым привязан пользователь по user_id"""
    result = await session.execute(
        select(JK, UserJK)
        .join(UserJK, JK.id == UserJK.jk_id)
        .where(UserJK.user_id == user_id)
    )
    return result.all()  # список кортежей (JK, UserJK)


async def orm_get_users_by_jk_id(session: AsyncSession, jk_id: int) -> list[User]:
    """Получение списка пользователей, привязанных к ЖК по jk_id"""
    result = await session.execute(
        select(User).join(UserJK).where(UserJK.jk_id == jk_id)
    )
    return (
        result.scalars().all()
    )  # Возвращает список пользователей или пустой список, если не найдено


async def orm_update_user_jk(
    session: AsyncSession, user_id: int, jk_id: int, data: dict
) -> UserJK | None:
    """Обновление данных привязки пользователя к ЖК по user_id и jk_id"""
    stmt = (
        update(UserJK)
        .where(UserJK.user_id == user_id, UserJK.jk_id == jk_id)
        .values(**data)
    )
    result = await session.execute(stmt)
    # Commit убран - middleware автоматически сделает commit
    return await orm_get_user_jk(session, user_id, jk_id)


async def orm_get_admins_by_jk_id(session: AsyncSession, jk_id: int) -> list[User]:
    """Получение списка администраторов ЖК по jk_id"""
    result = await session.execute(
        select(User)
        .join(UserJK)
        .where(UserJK.jk_id == jk_id, UserJK.is_admin.is_(True))
    )
    return (
        result.scalars().all()
    )  # Возвращает список администраторов или пустой список, если не найдено


async def orm_get_uk_by_jk_id(session: AsyncSession, jk_id: int) -> User | None:
    """Получение УК, связанного с ЖК по jk_id"""
    result = await session.execute(
        select(User)
        .join(UserJK)
        .where(UserJK.jk_id == jk_id, UserJK.is_service.is_(True))
    )
    return result.scalar_one_or_none()  # Возвращает УК или None, если не найдено


async def orm_get_admins_jk_id(session: AsyncSession) -> list[int]:
    """Получение списка ID администраторов всех ЖК"""
    result = await session.execute(
        select(UserJK.jk_id).where(UserJK.is_admin.is_(True))
    )
    return [row[0] for row in result.fetchall()]  # Возвращает список ID администраторов


async def orm_get_jk_by_user_id_is_service(
    session: AsyncSession, user_id: int
) -> UserJK | None:
    """Получение привязки пользователя к ЖК, где пользователь является Службой ЖК"""
    result = await session.execute(
        select(UserJK).where(UserJK.user_id == user_id, UserJK.is_service.is_(True))
    )
    return result.scalar_one_or_none()  # Возвращает привязку или None, если не найдено


async def orm_get_jks_by_user_admin(session: AsyncSession, user_id: int) -> list[JK]:
    """Получение списка ЖК, где пользователь является администратором"""
    result = await session.execute(
        select(JK)
        .join(UserJK)
        .where(UserJK.user_id == user_id, UserJK.is_admin.is_(True))
    )
    return result.scalars().all()


async def orm_check_user_is_jk_admin(session: AsyncSession, user_id: int, jk_id: int) -> bool:
    """Проверка, является ли пользователь администратором конкретного ЖК"""
    result = await session.execute(
        select(UserJK).where(
            UserJK.user_id == user_id,
            UserJK.jk_id == jk_id,
            UserJK.is_admin.is_(True)
        )
    )
    return result.scalar_one_or_none() is not None


async def orm_set_user_jk_admin(session: AsyncSession, user_id: int, jk_id: int, is_admin: bool = True) -> UserJK | None:
    """Назначение/снятие пользователя администратором ЖК"""
    result = await session.execute(
        select(UserJK).where(
            UserJK.user_id == user_id,
            UserJK.jk_id == jk_id
        )
    )
    user_jk = result.scalar_one_or_none()
    
    if user_jk:
        user_jk.is_admin = is_admin
        await session.flush()
        return user_jk
    return None


async def orm_get_user_jk_with_jk_by_id(session: AsyncSession, user_jk_id: int):
    """Получение UserJK с данными JK по user_jk_id"""
    result = await session.execute(
        select(UserJK, JK)
        .join(JK, UserJK.jk_id == JK.id)
        .where(UserJK.id == user_jk_id)
    )
    return result.first()  # Возвращает (UserJK, JK) или None
