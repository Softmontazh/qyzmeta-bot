# coding: utf-8
# database/models/orm_lot.py

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.model_lot import Lot
from database.enums.lot_enums import LotOfferType, LotStatus, LotVisibility


async def orm_add_lot(session: AsyncSession, data: dict):
    """Добавление нового лота в базу данных."""
    obj = Lot(
        offer_type=LotOfferType(data["offer_type"]),
        type_lot=data["type_lot"],
        name=data["name_lot"],
        description=data["description_lot"],
        price=float(data["price_lot"]),
        city=data["city_lot"],
        phone=data["phone_lot"],
        image_id=data["image_lot"],
        owner_id=data["user_id"],  # Добавляем ID владельца лота
    )
    session.add(obj)
    # Commit убран - middleware автоматически сделает commit
    await session.flush()  # Используем flush для получения ID


async def orm_get_lots(session: AsyncSession):
    """Получение всех лотов из базы данных."""
    query = select(Lot)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_lots_by_user(session: AsyncSession, user_id: int):
    """Получение всех лотов пользователя по его ID."""
    query = select(Lot).where(Lot.owner_id == user_id)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_lots_by_status(session: AsyncSession, status: LotStatus):
    """Получение всех лотов по статусу."""
    query = select(Lot).where(Lot.status == status)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_lots_by_visibility(session: AsyncSession, visibility: LotVisibility):
    """Получение всех лотов по видимости."""
    query = select(Lot).where(Lot.visibility == visibility)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_lots_by_offer_type(session: AsyncSession, offer_type: LotOfferType):
    """Получение всех лотов по типу предложения."""
    query = select(Lot).where(Lot.offer_type == offer_type)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_lots_by_city(session: AsyncSession, city: str):
    """Получение всех лотов по городу."""
    query = select(Lot).where(Lot.city == city)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_lot(session: AsyncSession, lot_id: int):
    """Получение лота по его ID."""
    query = select(Lot).where(Lot.id == lot_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_lot(session: AsyncSession, lot_id: int, data):
    """Обновление лота по его ID."""
    # Получаем текущее значение expires_at, если не передано новое
    lot = await orm_get_lot(session, lot_id)
    expires_at = data.get("expires_at", getattr(lot, "expires_at", None))
    if expires_at is not None:
        from datetime import datetime, timezone

        if isinstance(expires_at, str):
            expires_at = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

    query = (
        update(Lot)
        .where(Lot.id == lot_id)
        .values(
            offer_type=LotOfferType(data["offer_type"]),
            type_lot=data["type_lot"],
            name=data["name_lot"],
            description=data["description_lot"],
            price=float(data["price_lot"]),
            city=data["city_lot"],
            phone=data["phone_lot"],
            image_id=data["image_lot"],
            owner_id=data["user_id"],  # Обновляем ID владельца лота
            status=LotStatus(data.get("status", LotStatus.ACTIVE)),
            visibility=LotVisibility(data.get("visibility", LotVisibility.PUBLIC)),
            expires_at=(
                expires_at if expires_at else lot.expires_at
            ),  # Используем текущее значение, если не передано новое
        )
    )
    await session.execute(query)
    # Commit убран - middleware автоматически сделает commit


async def orm_delete_lot(session: AsyncSession, lot_id: int):
    """Удаление лота по его ID."""
    query = delete(Lot).where(Lot.id == lot_id)
    await session.execute(query)
    # Commit убран - middleware автоматически сделает commit
