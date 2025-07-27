# -*- coding: utf-8 -*-
# handlers/fsm/user_to_jk_fsm.py
"""
Обработчик команд для регистрации пользователя в жилом комплексе (ЖК) с использованием конечного автомата состояний (FSM).
"""

import os
from aiogram.types import Message, CallbackQuery
from aiogram import F, Bot, Router
from aiogram.filters import Command, StateFilter

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.reply import get_keyboard

from database.models.model_user_jk import UserJK
from database.models.model_jk import JK
from database.models.orm_user_jk import orm_add_user_jk
from database.models.orm_jk import orm_get_all_jks, orm_get_name_by_id
from services.subscription_service import SubscriptionService
from keyboards.subscription_keyboards import get_address_limit_exceeded_keyboard
from database.enums.subscription_enums import SubscriptionTier
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

user_to_jk_router = Router()


class UserToJK(StatesGroup):
    """Состояния для создания жилого комплекса (ЖК)."""

    set_jk_name = State()  # Состояние для ввода названия ЖК
    set_appartment = State()  # Состояние для ввода квартиры


""""Обработчики команд для регистрации пользователя в ЖК."""


@user_to_jk_router.message(F.text.lower().contains("добавить мою квартиру"))
@user_to_jk_router.message(Command("add_my_jk"))
async def add_my_jk(message: Message, state: FSMContext, session: AsyncSession):
    await state.set_state(UserToJK.set_jk_name)
    await message.answer("Пожалуйста, выберите ЖК:")
    all_jks = await orm_get_all_jks(session)
    if not all_jks:
        await message.answer("Нет доступных ЖК.")
        return

    for jk in all_jks:
        text = f"<b>{jk.name}</b>\nАдрес: {jk.full_address}\n"
        is_house_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👆 Я здесь живу! 👆", callback_data=f"is_hous:{jk.id}"
                    )
                ]
            ]
        )

        if getattr(jk, "image_id", None):
            await message.answer_photo(
                jk.image_id, caption=text, parse_mode="HTML", reply_markup=is_house_kb
            )
        else:
            await message.answer(text, parse_mode="HTML", reply_markup=is_house_kb)


"""Обработчик выбора ЖК пользователем."""


@user_to_jk_router.callback_query(F.data.startswith("is_hous:"))
async def is_hous_callback(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    jk_id = int(callback.data.split(":")[1])  # достаём ID из строки
    await state.update_data(jk_id=jk_id)  # сохраняем в FSM

    name_jk = await orm_get_name_by_id(session, jk_id)
    await callback.message.answer(
        f"Вы выбрали: <b>{name_jk}</b>\nВведите номер вашей квартиры:",
        parse_mode="HTML",
    )
    await state.set_state(UserToJK.set_appartment)
    await callback.answer()


"""Обработчик ввода квартиры пользователем."""


@user_to_jk_router.message(UserToJK.set_appartment)
async def set_appartment(message: Message, state: FSMContext, session: AsyncSession):
    """Установить номер квартиры и зарегистрировать пользователя в ЖК"""
    data = await state.get_data()
    jk_id = data.get("jk_id")
    appartment = message.text.strip()
    user_id = message.from_user.id

    # 🚀 ПРОВЕРКА ЛИМИТА АДРЕСОВ
    can_register, subscription_info = await SubscriptionService.check_can_register_address(
        session, user_id
    )
    
    if not can_register:
        # Превышен лимит адресов
        await state.clear()
        
        current_tier = subscription_info.get("tier", SubscriptionTier.FREE)
        
        limit_message = f"🚫 <b>Лимит адресов исчерпан</b>\n\n"
        limit_message += f"📊 <b>Ваш тариф:</b> {subscription_info['tier_name']}\n"
        limit_message += f"🏠 <b>Адреса:</b> {subscription_info['current_addresses']}/{subscription_info['max_addresses']}\n\n"
        limit_message += "💡 <b>Для регистрации по новому адресу необходимо обновить тариф</b>"
        
        # Клавиатура с предложением апгрейда
        keyboard = get_address_limit_exceeded_keyboard(user_id, current_tier)
        
        await message.answer(
            limit_message,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    # Сохраняем в БД (если лимит позволяет)
    await orm_add_user_jk(
        session, user_id=user_id, jk_id=jk_id, appartment=appartment
    )
    
    name_jk = await orm_get_name_by_id(session, jk_id)
    
    # Получаем обновленную информацию о подписке
    updated_subscription_info = await SubscriptionService.get_user_subscription_info(
        session, user_id
    )
    
    success_message = f"✅ <b>Успешно зарегистрированы!</b>\n\n"
    success_message += f"🏢 <b>ЖК:</b> {name_jk}\n"
    success_message += f"🏠 <b>Квартира:</b> {appartment}\n\n"
    success_message += f"📊 <b>Адреса:</b> {updated_subscription_info['current_addresses']}/{updated_subscription_info['max_addresses']}\n"
    
    # Если близко к лимиту, предлагаем апгрейд
    if (updated_subscription_info['max_addresses'] - updated_subscription_info['current_addresses'] <= 1 
        and updated_subscription_info['tier'] != SubscriptionTier.VIP):
        success_message += "\n💡 <i>Близко к лимиту! Рассмотрите возможность обновления тарифа</i>"
    
    await message.answer(success_message, parse_mode="HTML")
    await state.clear()
