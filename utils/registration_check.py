# -*- coding: utf-8 -*-
# utils/registration_check.py

from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database.enums.user_enums import UserRole
from database.models.orm_user import orm_get_user_by_id
from keyboards.reply import get_keyboard
from typing import Union


async def check_user_registration(event: Union[Message, CallbackQuery], session: AsyncSession) -> bool:
    """
    Проверяет, завершена ли регистрация пользователя.
    Возвращает True, если пользователь зарегистрирован, False - если нет.
    Работает как с Message, так и с CallbackQuery.
    """
    user_id = event.from_user.id
    user = await orm_get_user_by_id(session, user_id)
    
    # Если пользователь не найден, роль GUEST или нет телефона - регистрация не завершена
    if not user or user.role == UserRole.GUEST or not user.phone:
        if isinstance(event, Message):
            await event.answer(
                "🚫 Для доступа к этой функции необходимо завершить регистрацию.\n\n"
                "Пожалуйста, отправь свой номер телефона 📱",
                reply_markup=get_keyboard(
                    "Отправить номер 📞",
                    request_contact=0,
                    placeholder="нажми кнопку",
                    sizes=(1,),
                ),
            )
        else:  # CallbackQuery
            await event.answer(
                "🚫 Для доступа к этой функции необходимо завершить регистрацию.",
                show_alert=True
            )
        return False
    return True
