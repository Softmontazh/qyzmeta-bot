# coding: utf-8
# services/lot_service.py

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.model_user import User
from database.models.model_lot import Lot
from database.models.model_lot_limit import LotLimit
from database.enums.lot_enums import LotVisibility

""" Сервис для работы с лотами """


# Функция для поиска лотов пользователя
async def check_user_lot_limit(
    user: User, session: AsyncSession
) -> tuple[bool, int, int]:
    # Получаем лимит по роли
    lot_limit_stmt = select(LotLimit.limit).where(LotLimit.role == user.role)
    lot_limit_result = await session.execute(lot_limit_stmt)
    limit = lot_limit_result.scalar() or 0

    # Считаем активные лоты пользователя
    user_lots_stmt = (
        select(func.count()).select_from(Lot).where(Lot.owner_id == user.user_id)
    )
    current_count_result = await session.execute(user_lots_stmt)
    current_count = current_count_result.scalar() or 0

    can_add = current_count < limit

    # Возвращаем возможность добавления лота, текущее количество и лимит
    if can_add:
        print(
            f"Пользователь {int(user.user_id)} может добавить больше лотов. Текущее: {current_count}, Лимит: {limit}"
        )
    else:
        print(
            f"Пользователь {int(user.user_id)} не может добавить больше лотов. Текущее: {current_count}, Лимит: {limit}"
        )

    return can_add, current_count, limit


# Функция для поиска лотов по фильтрам
async def search_lots(
    session: AsyncSession,  # Тип сессии для работы с БД
    filters: dict,  # Фильтры для поиска лотов
    limit: int = 10,  # Количество лотов на странице
    offset: int = 0,  # Смещение для пагинации
) -> list[Lot]:  # Вернет список найденных лотов
    """
    Функция для поиска лотов по заданным фильтрам.
    """
    # Начинаем с запроса к таблице Lot, выбирая только публичные лоты
    query = select(Lot).where(Lot.visibility == LotVisibility.PUBLIC)

    # Фильтр по запросу
    if name := filters.get("name"):
        # Выбираем лоты, где название содержит искомый текст
        query = query.where(Lot.name.ilike(f"%{name}%"))

    # Фильтр по городу
    if city := filters.get("city"):
        # Выбираем лоты, где город совпадает с искомым
        query = query.where(Lot.city.ilike(f"%{city}%"))

    # Фильтр по типу лота
    if type_lot := filters.get("type_lot"):
        # Выбираем лоты по типу
        query = query.where(Lot.type_lot == type_lot)

    # Фильтр по статусу лота
    if status := filters.get("status"):
        # Выбираем лоты по статусу
        query = query.where(Lot.status == status)

    # Фильтр по группе
    if group_id := filters.get("group_id"):
        # Выбираем лоты, принадлежащие определенной группе
        query = query.where(Lot.group_id == group_id)

    query = query.order_by(Lot.created_at.desc()).limit(limit).offset(offset)

    result = await session.execute(query)
    return result.scalars().all()
