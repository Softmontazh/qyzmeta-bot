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
    stmt = (
        update(JK)
        .where(JK.id == jk_id)
        .values(
            uuid=data.get("uuid"),
            name=data.get("name"),
            city=data.get("city"),
            street=data.get("street"),
            house=data.get("house"),
            block=data.get("block"),
            channel_id=data.get("channel_id"),
            group_id=data.get("group_id"),
            id_uk=data.get("id_uk"),
        )
    )
    result = await session.execute(stmt)
    await session.commit()
    await session.refresh(result)
    return result.scalar_one_or_none()


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
