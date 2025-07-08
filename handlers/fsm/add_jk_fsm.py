# -*- coding: utf-8 -*-
# handlers/fsm/add_jk_fsm.py
"""
Обработчики команд для создания жилого комплекса (ЖК) с использованием конечного автомата состояний (FSM).
"""
"""Доступно только владельцу бота"""
"""ID владельца бота хранится в переменной окружения CREATOR_ID"""

import os
from aiogram.types import Message, CallbackQuery
from aiogram import F, Router
from aiogram.filters import Command, or_f, StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.orm_jk import orm_add_jk
from keyboards.reply import MAIN_KB, get_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

CONFIRM_JK = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_jk"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_jk"),
        ]
    ]
)

ADD_JK_MAIN = get_keyboard(
    "Добавить ЖК",
    "Главное меню 🏠",
    placeholder="Меню создания ЖК",
    sizes=(2, 1),
)

add_jk_router = Router()


class JKCreationState(StatesGroup):
    """Состояния для создания жилого комплекса (ЖК)."""

    name = State()  # Состояние для ввода названия ЖК
    block = State()  # Состояние для ввода блока ЖК
    city = State()  # Состояние для ввода города ЖК
    street = State()  # Состояние для ввода улицы ЖК
    house = State()  # Состояние для ввода номера дома ЖК
    image_id = State()  # Состояние для загрузки изображения ЖК
    confirm = State()  # Состояние для подтверждения создания ЖК


# Обработчики команд, которые работают вне состояний FSM
@add_jk_router.message(
    or_f(Command("main_menu"), F.text.lower() == "главное меню 🏠"),
    ~StateFilter(JKCreationState),
)
async def main_menu(message: Message, state: FSMContext):
    """Переход в главное меню"""
    await state.clear()
    await message.answer("🏠 Главное меню", reply_markup=MAIN_KB)


@add_jk_router.message(
    or_f(Command("add_jk"), F.text.lower() == "добавить жк"),
    ~StateFilter(JKCreationState),
)
async def create_jk(message: Message, state: FSMContext):
    await state.clear()
    creator_ids = os.getenv("CREATOR_ID")
    if not creator_ids or str(message.from_user.id) not in creator_ids.split(","):
        await message.answer("⛔ У вас нет прав ⛔")
        return
    await state.set_state(JKCreationState.name)
    await message.answer("🏢 Введите название ЖК:", reply_markup=ADD_JK_MAIN)


# Остальные обработчики состояний остаются без изменений
@add_jk_router.callback_query(F.data == "skip_name")
async def skip_name_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик пропуска ввода названия ЖК"""
    await state.update_data(name=None)
    await state.set_state(JKCreationState.block)
    await callback.message.answer("🏙️ Введите Блок ЖК:")
    await callback.answer()


@add_jk_router.message(JKCreationState.name)
async def set_jk_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(JKCreationState.block)
    skip_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data="skip_block")]
        ]
    )
    await message.answer(
        "🏙️ Введите Блок ЖК или пропустите шаг:\nпример: Блок А, Блок 1.1",
        reply_markup=skip_keyboard,
    )


@add_jk_router.callback_query(F.data == "skip_block")
async def skip_block_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик пропуска ввода блока ЖК"""
    await state.update_data(block=None)
    await state.set_state(JKCreationState.city)
    await callback.message.answer("🏙️ Введите город ЖК:")
    await callback.answer()


@add_jk_router.message(JKCreationState.city)
async def set_jk_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(JKCreationState.street)
    await message.answer("🏙️ Введите улицу ЖК:")


@add_jk_router.message(JKCreationState.street)
async def set_jk_street(message: Message, state: FSMContext):
    await state.update_data(street=message.text)
    await state.set_state(JKCreationState.house)
    await message.answer("🏙️ Введите номер дома ЖК:")


@add_jk_router.message(JKCreationState.house)
async def set_jk_house(message: Message, state: FSMContext):
    await state.update_data(house=message.text)
    await state.set_state(JKCreationState.image_id)
    await message.answer(
        "🏙️ Загрузите фото ЖК или пропустите:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Пропустить", callback_data="skip_image")]
            ]
        ),
    )


@add_jk_router.callback_query(F.data == "skip_image")
async def skip_image_callback(callback: CallbackQuery, state: FSMContext):
    """Пропуск изображения"""
    await state.update_data(image_id=None)
    await state.set_state(JKCreationState.confirm)
    await callback.message.answer("🏙️ Подтвердите создание ЖК:", reply_markup=CONFIRM_JK)
    await callback.answer()


@add_jk_router.message(JKCreationState.image_id, F.photo)
async def set_jk_image(message: Message, state: FSMContext, session: AsyncSession):
    photo = message.photo[-1]
    # отправляем в BUS
    BUS_ID = os.getenv("BUS_ID")
    sent = await message.bot.send_photo(BUS_ID, photo.file_id)
    new_file_id = sent.photo[-1].file_id

    await state.update_data(image_id=new_file_id)

    await state.set_state(JKCreationState.confirm)
    await message.answer("🏙️ Подтвердите создание ЖК:", reply_markup=CONFIRM_JK)


@add_jk_router.callback_query(F.data == "cancel_jk")
async def cancel_jk_creation(callback: CallbackQuery, state: FSMContext):
    """Отмена создания ЖК"""
    await state.clear()
    await callback.message.answer("🏙️ Создание ЖК отменено.")
    await callback.answer()


@add_jk_router.callback_query(F.data == "confirm_jk")
async def confirm_jk_creation_callback(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    """Подтверждение создания ЖК через кнопку"""
    data = await state.get_data()
    await callback.message.answer("🏙️ Создание ЖК подтверждено!")
    new_file_id = data.get("image_id")
    await state.update_data(image_id=new_file_id)

    data = await state.get_data()
    """Сохраняем ID создателя ЖК"""
    data["creator_id"] = callback.from_user.id
    await state.update_data(**data)

    """Создаем новый ЖК в базе данных"""
    new_jk = await orm_add_jk(session, data)
    await state.clear()
    await callback.message.answer("🏙️ ЖК успешно добавлен в базу данных!")

    text = (
        f"🏢 <b>{new_jk.name}</b>\n"
        f"Город: {new_jk.city}\n"
        f"Улица: {new_jk.street}\n"
        f"Дом: {new_jk.house}\n"
        f"Блок: {new_jk.block or '—'}\n"
        f"ID ЖК: <code>{new_jk.id}</code>"
    )
    print(text)
    await callback.message.answer_photo(
        new_jk.image_id, caption=text, parse_mode="HTML"
    )
