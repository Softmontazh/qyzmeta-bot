# -*- coding: utf-8 -*-
# handlers/fsm/add_jk_fsm.py
"""
Обработчики команд для создания и редактирования жилого комплекса (ЖК) с использованием FSM.
Упрощенная версия: вместо кнопок "Пропустить" используется точка "." для пропуска полей.
"""

import os
from aiogram.types import Message, CallbackQuery
from aiogram import F, Router
from aiogram.filters import Command, or_f, StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.orm_jk import orm_add_jk, orm_update_jk, orm_get_jk_by_id
from keyboards.reply import MAIN_KB, get_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.bus_service import bus_service

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
    "Список ЖК 📋",
    "Главное меню 🏠",
    placeholder="Меню управления ЖК",
    sizes=(2, 1),
)

add_jk_router = Router()


class JKCreationState(StatesGroup):
    """Состояния для создания жилого комплекса (ЖК)."""
    menu = State()  # Состояние меню выбора действий
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
    StateFilter(JKCreationState),
)
async def main_menu(message: Message, state: FSMContext):
    """Переход в главное меню из любого состояния FSM"""
    await state.clear()
    await message.answer("🏠 Главное меню", reply_markup=MAIN_KB)


@add_jk_router.message(
    or_f(Command("add_jk")),
    ~StateFilter(JKCreationState),
)
async def create_jk_menu(message: Message, state: FSMContext):
    """Показать меню управления ЖК"""
    await state.clear()
    creator_ids = os.getenv("CREATOR_ID")
    if not creator_ids or str(message.from_user.id) not in creator_ids.split(","):
        await message.answer("⛔ У вас нет прав ⛔")
        return
    await state.set_state(JKCreationState.menu)
    await message.answer("🏢 Выберите действие:", reply_markup=ADD_JK_MAIN)


@add_jk_router.message(
    F.text.lower() == "добавить жк",
    StateFilter(JKCreationState.menu),
)
async def start_create_jk(message: Message, state: FSMContext):
    """Начать создание нового ЖК"""
    await state.set_state(JKCreationState.name)
    await message.answer(
        "🏢 Введите название ЖК:\n\n"
        "💡 <i>Подсказка: введите точку (.) чтобы пропустить поле</i>",
        parse_mode="HTML"
    )


@add_jk_router.message(
    F.text.lower() == "список жк 📋",
    StateFilter(JKCreationState.menu),
)
async def show_jk_list_from_menu(message: Message, state: FSMContext, session: AsyncSession):
    """Показать список ЖК из меню создания"""
    await state.clear()
    
    # Используем внутреннюю функцию, которая не проверяет права повторно
    from handlers.fsm.manage_jk_fsm import show_jk_list_internal
    await show_jk_list_internal(message, state, session)


# Обработчик ввода названия ЖК
@add_jk_router.message(JKCreationState.name, F.text)
async def set_jk_name(message: Message, state: FSMContext):
    """Обработка ввода названия ЖК"""
    jk_name = message.text.strip()
    
    # Проверяем, не пропускает ли пользователь поле
    if jk_name == ".":
        # При редактировании сохраняем старое значение
        data = await state.get_data()
        if "editing_jk_id" in data:
            jk_name = data.get("current_name", "")
        else:
            jk_name = None
    elif len(jk_name) < 2:
        await message.answer(
            "❌ Название должно содержать минимум 2 символа.\n"
            "Введите название ЖК или точку (.) для пропуска:"
        )
        return
    
    await state.update_data(name=jk_name)
    await state.set_state(JKCreationState.block)
    
    # Показываем текущее значение при редактировании
    data = await state.get_data()
    current_block = data.get("current_block", "не указан")
    
    if "editing_jk_id" in data:
        await message.answer(
            f"🏗️ Введите блок ЖК:\n\n"
            f"📝 <b>Текущее значение:</b> {current_block}\n\n"
            "💡 <i>Введите новое значение или точку (.) чтобы сохранить текущее</i>",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "🏗️ Введите блок ЖК:\n\n"
            "💡 <i>Введите блок или точку (.) чтобы пропустить поле</i>",
            parse_mode="HTML"
        )


# Обработчик ввода блока ЖК
@add_jk_router.message(JKCreationState.block, F.text)
async def set_jk_block(message: Message, state: FSMContext):
    """Обработка ввода блока ЖК"""
    jk_block = message.text.strip()
    
    # Проверяем, не пропускает ли пользователь поле
    if jk_block == ".":
        # При редактировании сохраняем старое значение
        data = await state.get_data()
        if "editing_jk_id" in data:
            jk_block = data.get("current_block", None)
        else:
            jk_block = None
    
    await state.update_data(block=jk_block)
    await state.set_state(JKCreationState.city)
    
    # Показываем текущее значение при редактировании
    data = await state.get_data()
    current_city = data.get("current_city", "не указан")
    
    if "editing_jk_id" in data:
        await message.answer(
            f"🏙️ Введите город ЖК:\n\n"
            f"📝 <b>Текущее значение:</b> {current_city}\n\n"
            "💡 <i>Введите новое значение или точку (.) чтобы сохранить текущее</i>",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "🏙️ Введите город ЖК:\n\n"
            "💡 <i>Введите город или точку (.) чтобы пропустить поле</i>",
            parse_mode="HTML"
        )


# Обработчик ввода города ЖК
@add_jk_router.message(JKCreationState.city, F.text)
async def set_jk_city(message: Message, state: FSMContext):
    """Обработка ввода города ЖК"""
    jk_city = message.text.strip()
    
    # Проверяем, не пропускает ли пользователь поле
    if jk_city == ".":
        # При редактировании сохраняем старое значение
        data = await state.get_data()
        if "editing_jk_id" in data:
            jk_city = data.get("current_city", "")
        else:
            jk_city = ""
    
    await state.update_data(city=jk_city)
    await state.set_state(JKCreationState.street)
    
    # Показываем текущее значение при редактировании
    data = await state.get_data()
    current_street = data.get("current_street", "не указана")
    
    if "editing_jk_id" in data:
        await message.answer(
            f"🛣️ Введите улицу ЖК:\n\n"
            f"📝 <b>Текущее значение:</b> {current_street}\n\n"
            "💡 <i>Введите новое значение или точку (.) чтобы сохранить текущее</i>",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "🛣️ Введите улицу ЖК:\n\n"
            "💡 <i>Введите улицу или точку (.) чтобы пропустить поле</i>",
            parse_mode="HTML"
        )


# Обработчик ввода улицы ЖК
@add_jk_router.message(JKCreationState.street, F.text)
async def set_jk_street(message: Message, state: FSMContext):
    """Обработка ввода улицы ЖК"""
    jk_street = message.text.strip()
    
    # Проверяем, не пропускает ли пользователь поле
    if jk_street == ".":
        # При редактировании сохраняем старое значение
        data = await state.get_data()
        if "editing_jk_id" in data:
            jk_street = data.get("current_street", "")
        else:
            jk_street = ""
    
    await state.update_data(street=jk_street)
    await state.set_state(JKCreationState.house)
    
    # Показываем текущее значение при редактировании
    data = await state.get_data()
    current_house = data.get("current_house", "не указан")
    
    if "editing_jk_id" in data:
        await message.answer(
            f"🏠 Введите номер дома ЖК:\n\n"
            f"📝 <b>Текущее значение:</b> {current_house}\n\n"
            "💡 <i>Введите новое значение или точку (.) чтобы сохранить текущее</i>",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "🏠 Введите номер дома ЖК:\n\n"
            "💡 <i>Введите номер дома или точку (.) чтобы пропустить поле</i>",
            parse_mode="HTML"
        )


# Обработчик ввода номера дома ЖК
@add_jk_router.message(JKCreationState.house, F.text)
async def set_jk_house(message: Message, state: FSMContext):
    """Обработка ввода номера дома ЖК"""
    jk_house = message.text.strip()
    
    # Проверяем, не пропускает ли пользователь поле
    if jk_house == ".":
        # При редактировании сохраняем старое значение
        data = await state.get_data()
        if "editing_jk_id" in data:
            jk_house = data.get("current_house", "")
        else:
            jk_house = ""
    
    await state.update_data(house=jk_house)
    await state.set_state(JKCreationState.image_id)
    
    # Показываем текущее изображение при редактировании
    data = await state.get_data()
    current_image = data.get("current_image_id")
    
    if "editing_jk_id" in data:
        if current_image:
            await message.answer(
                "📸 Текущее изображение ЖК:",
                parse_mode="HTML"
            )
            await message.answer_photo(
                photo=current_image,
                caption="📸 Загрузите новое изображение ЖК или введите точку (.) чтобы сохранить текущее"
            )
        else:
            await message.answer(
                "📸 Загрузите изображение ЖК:\n\n"
                "📝 Текущее изображение: отсутствует\n\n"
                "💡 Загрузите новое изображение или введите точку (.) чтобы пропустить",
                parse_mode="HTML"
            )
    else:
        await message.answer(
            "📸 Загрузите изображение ЖК:\n\n"
            "💡 Загрузите изображение или введите точку (.) чтобы пропустить",
            parse_mode="HTML"
        )


# Обработчик загрузки изображения ЖК
@add_jk_router.message(JKCreationState.image_id, F.photo)
async def set_jk_image(message: Message, state: FSMContext):
    """Обработка загрузки изображения ЖК"""
    photo = message.photo[-1]
    
    # Сохраняем фото в общий канал для получения BUS_ID
    bus_id = await bus_service.save_image(photo.file_id)
    
    await state.update_data(image_id=photo.file_id, bus_image_id=bus_id)
    await show_confirmation(message, state)


# Обработчик пропуска изображения (точка)
@add_jk_router.message(JKCreationState.image_id, F.text == ".")
async def skip_jk_image(message: Message, state: FSMContext):
    """Пропуск загрузки изображения ЖК"""
    # При редактировании сохраняем старое изображение
    data = await state.get_data()
    if "editing_jk_id" in data:
        # Сохраняем текущие значения
        await state.update_data(
            image_id=data.get("current_image_id"),
            bus_image_id=data.get("current_bus_image_id")
        )
    else:
        # При создании нового ЖК - без изображения
        await state.update_data(image_id=None, bus_image_id=None)
    
    await show_confirmation(message, state)


# Обработчик некорректного ввода на этапе изображения
@add_jk_router.message(JKCreationState.image_id)
async def invalid_image_input(message: Message, state: FSMContext):
    """Обработка некорректного ввода на этапе загрузки изображения"""
    await message.answer(
        "❌ Пожалуйста, загрузите изображение или введите точку (.) для пропуска."
    )


async def show_confirmation(message: Message, state: FSMContext):
    """Показывает подтверждение создания/редактирования ЖК"""
    data = await state.get_data()
    
    editing_mode = "editing_jk_id" in data
    
    if editing_mode:
        text = "✏️ РЕДАКТИРОВАНИЕ ЖК\n\n"
    else:
        text = "🏢 СОЗДАНИЕ НОВОГО ЖК\n\n"
    
    text += f"📝 Название: {data.get('name', 'не указано')}\n"
    text += f"🏗️ Блок: {data.get('block', 'не указан')}\n"
    text += f"🏙️ Город: {data.get('city', 'не указан')}\n"
    text += f"🛣️ Улица: {data.get('street', 'не указана')}\n"
    text += f"🏠 Дом: {data.get('house', 'не указан')}\n"
    
    if data.get('image_id'):
        text += "📸 Изображение: загружено\n"
    else:
        text += "📸 Изображение: не загружено\n"
    
    if editing_mode:
        text += f"\n✅ Сохранить изменения?"
    else:
        text += f"\n✅ Создать ЖК?"
    
    await state.set_state(JKCreationState.confirm)
    await message.answer(text, reply_markup=CONFIRM_JK)


@add_jk_router.callback_query(F.data == "confirm_jk")
async def confirm_jk(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Подтверждение создания/редактирования ЖК"""
    data = await state.get_data()
    user_id = callback.from_user.id
    
    editing_mode = "editing_jk_id" in data
    
    if editing_mode:
        # Режим редактирования
        jk_id = data.get("editing_jk_id")
        
        jk_update_data = {
            "name": data.get("name"),
            "block": data.get("block"),
            "city": data.get("city"),
            "street": data.get("street"),
            "house": data.get("house"),
            "image_id": data.get("image_id"),
            "bus_image_id": data.get("bus_image_id")
        }
        
        updated_jk = await orm_update_jk(session, jk_id, jk_update_data)
        
        if updated_jk:
            text = f"✅ ЖК успешно обновлен!\n\n"
            text += f"🏢 {updated_jk.name}\n"
            text += f"📍 {updated_jk.city}, {updated_jk.street}, {updated_jk.house}\n"
            if updated_jk.block:
                text += f"🏗️ Блок: {updated_jk.block}\n"
            text += f"🆔 ID ЖК: {updated_jk.id}"
            
            if updated_jk.image_id:
                await callback.message.answer_photo(
                    photo=updated_jk.image_id,
                    caption=text
                )
            else:
                await callback.message.edit_text(text)
        else:
            await callback.message.edit_text("❌ Ошибка при обновлении ЖК")
    else:
        # Режим создания нового ЖК
        jk_data = {
            "name": data.get("name"),
            "block": data.get("block"),
            "city": data.get("city"),
            "street": data.get("street"),
            "house": data.get("house"),
            "image_id": data.get("image_id"),
            "bus_image_id": data.get("bus_image_id"),
            "creator_id": user_id,
        }
        
        jk = await orm_add_jk(session, jk_data)
        await session.commit()
        
        text = f"✅ ЖК успешно создан!\n\n"
        text += f"🏢 {jk.name}\n"
        text += f"📍 {jk.city}, {jk.street}, {jk.house}\n"
        if jk.block:
            text += f"🏗️ Блок: {jk.block}\n"
        text += f"🆔 ID ЖК: {jk.id}"
        
        if jk.image_id:
            await callback.message.answer_photo(
                photo=jk.image_id,
                caption=text
            )
        else:
            await callback.message.edit_text(text)
    
    await state.clear()
    
    # Возвращаем пользователя в меню управления ЖК
    await state.set_state(JKCreationState.menu)
    await callback.message.answer(
        "🏢 Выберите действие:",
        reply_markup=ADD_JK_MAIN
    )
    await callback.answer("Готово!")


@add_jk_router.callback_query(F.data == "cancel_jk")
async def cancel_jk(callback: CallbackQuery, state: FSMContext):
    """Отмена создания/редактирования ЖК"""
    data = await state.get_data()
    editing_mode = "editing_jk_id" in data
    
    if editing_mode:
        await callback.message.edit_text("❌ Редактирование ЖК отменено")
    else:
        await callback.message.edit_text("❌ Создание ЖК отменено")
    
    await state.clear()
    
    # Возвращаем пользователя в меню управления ЖК
    await state.set_state(JKCreationState.menu)
    await callback.message.answer(
        "🏢 Выберите действие:",
        reply_markup=ADD_JK_MAIN
    )
    await callback.answer("Отменено")
