# coding: utf-8
# database/models/orm_jk.py

import uuid
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.model_jk import JK


async def orm_add_jk(session: AsyncSession, data: dict):
    """Добавление нового ЖК в базу данных."""
    generated_uuid = data.get("uuid") or str(uuid.uuid4())

    obj = JK(
        uuid=generated_uuid,
        name=data["name"],
        city=data["city"],
        street=data["street"],
        house=data["house"],
        block=data["block"],
        channel_id=data.get("channel_id"),
        group_id=data.get("group_id"),
        id_uk=data.get("id_uk"),
        image_id=data.get("image_id"),
        bus_image_id=data.get("bus_image_id"),  # BUS_ID для общего доступа
        creator_id=data.get("creator_id"),  # ID создателя ЖК
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def orm_get_jk(session: AsyncSession, jk_id: int) -> JK | None:
    """Получение ЖК по ID."""
    result = await session.execute(select(JK).where(JK.id == jk_id))
    return result.scalar_one_or_none()


async def orm_update_jk(session: AsyncSession, jk_id: int, data: dict) -> JK | None:
    """Обновление данных ЖК по ID."""
    # Создаем словарь только с теми полями, которые нужно обновить
    # Исключаем uuid, так как он не должен изменяться
    update_data = {}
    
    if "name" in data and data["name"] is not None:
        update_data["name"] = data["name"]
    if "city" in data and data["city"] is not None:
        update_data["city"] = data["city"]
    if "street" in data and data["street"] is not None:
        update_data["street"] = data["street"]
    if "house" in data and data["house"] is not None:
        update_data["house"] = data["house"]
    if "block" in data:
        update_data["block"] = data["block"]
    if "channel_id" in data:
        update_data["channel_id"] = data["channel_id"]
    if "group_id" in data:
        update_data["group_id"] = data["group_id"]
    if "id_uk" in data:
        update_data["id_uk"] = data["id_uk"]
    if "image_id" in data:
        update_data["image_id"] = data["image_id"]
    if "bus_image_id" in data:
        update_data["bus_image_id"] = data["bus_image_id"]
    
    if not update_data:
        # Если нет данных для обновления, просто возвращаем существующий объект
        return await orm_get_jk_by_id(session, jk_id)
    
    stmt = (
        update(JK)
        .where(JK.id == jk_id)
        .values(**update_data)
    )
    
    await session.execute(stmt)
    await session.commit()
    
    # Получаем обновленный объект
    updated_jk = await orm_get_jk_by_id(session, jk_id)
    return updated_jk


async def orm_get_jk_by_uuid(session: AsyncSession, uuid: str) -> JK | None:
    """Получение ЖК по UUID."""
    result = await session.execute(select(JK).where(JK.uuid == uuid))
    return result.scalar_one_or_none()


async def orm_delete_jk(session: AsyncSession, jk_id: int) -> bool:
    """Удаление ЖК по ID."""
    stmt = delete(JK).where(JK.id == jk_id)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0


async def orm_get_all_jks(session: AsyncSession) -> list[JK]:
    """Получение всех ЖК."""
    result = await session.execute(select(JK))
    return result.scalars().all()


async def orm_get_name_by_id(session: AsyncSession, jk_id: int) -> str | None:
    """Получение имени ЖК по ID."""
    result = await session.execute(select(JK.name).where(JK.id == jk_id))
    return result.scalar_one_or_none()


async def orm_get_jk_by_channel_id(session: AsyncSession, channel_id: int) -> JK | None:
    """Получение ЖК по ID канала."""
    result = await session.execute(select(JK).where(JK.channel_id == channel_id))
    return result.scalar_one_or_none()


async def orm_get_jk_by_group_id(session: AsyncSession, group_id: int) -> JK | None:
    """Получение ЖК по ID группы."""
    result = await session.execute(select(JK).where(JK.group_id == group_id))
    return result.scalar_one_or_none()


async def orm_get_jk_by_id_uk(session: AsyncSession, id_uk: int) -> JK | None:
    """Получение ЖК по ID УК."""
    result = await session.execute(select(JK).where(JK.id_uk == id_uk))
    return result.scalar_one_or_none()


# Дополнительные функции для управления ЖК

async def orm_get_jk_by_id(session: AsyncSession, jk_id: int) -> JK | None:
    """Получение ЖК по ID (алиас для совместимости)."""
    return await orm_get_jk(session, jk_id)


async def orm_update_jk_field(session: AsyncSession, jk_id: int, **kwargs) -> bool:
    """Обновление отдельных полей ЖК."""
    # Фильтруем только допустимые поля
    allowed_fields = {'name', 'city', 'street', 'house', 'block', 'image_id', 'bus_image_id', 'channel_id', 'group_id', 'id_uk'}
    update_data = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
    
    if not update_data:
        return False
    
    stmt = update(JK).where(JK.id == jk_id).values(**update_data)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0
