# -*- coding: utf-8 -*-
# handlers/fsm/manage_jk_fsm.py
"""
Упрощенный FSM для управления списком ЖК - только просмотр списка и кнопка "Изменить".
Редактирование делается через add_jk_fsm.py с возможностью пропуска полей.
"""

import os
from aiogram.types import Message, CallbackQuery
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.orm_jk import orm_get_all_jks, orm_get_jk_by_id
from database.enums.user_enums import UserRole
from database.models.orm_user import orm_get_user_by_id
from keyboards.reply import MAIN_KB, get_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models.orm_jk_service_provider import orm_get_service_providers_by_jk
from database.enums.offer_category_enum import OfferCategory

manage_jk_router = Router()


class ManageJKState(StatesGroup):
    """Состояния для управления ЖК."""
    viewing_list = State()  # Просмотр списка ЖК


# Проверка прав доступа
async def check_creator_access(user_id: int, session: AsyncSession) -> bool:
    """Проверяет, является ли пользователь создателем."""
    creator_ids = os.getenv("CREATOR_ID")
    if not creator_ids:
        return False
    
    # Проверяем, есть ли user_id в списке создателей
    if str(user_id) in creator_ids.split(","):
        return True
    
    # Дополнительная проверка роли в БД
    user = await orm_get_user_by_id(session, user_id)
    return user and user.role in [UserRole.CREATOR, UserRole.OWNER, UserRole.SUPERADMIN]


# Команда для входа в меню управления ЖК
@manage_jk_router.message(F.text.lower().contains("список жк"))
@manage_jk_router.message(Command("manage_jk"))
async def cmd_manage_jk(message: Message, state: FSMContext, session: AsyncSession):
    """Показать список ЖК для управления."""
    user_id = message.from_user.id
    
    if not await check_creator_access(user_id, session):
        await message.answer(
            "❌ У вас нет прав для управления жилыми комплексами.",
            reply_markup=MAIN_KB
        )
        return
    
    # Получаем список всех ЖК
    jk_list = await orm_get_all_jks(session)
    
    if not jk_list:
        await message.answer(
            "📋 Список жилых комплексов пуст.\n\n"
            "Используйте команду 'Добавить ЖК' для создания нового комплекса.",
            reply_markup=get_keyboard(
                "Добавить ЖК",
                "Главное меню 🏠",
                placeholder="Управление ЖК",
                sizes=(1, 1)
            )
        )
        return
    
    # Формируем текст со списком ЖК
    text = "🏢 <b>УПРАВЛЕНИЕ ЖИЛЫМИ КОМПЛЕКСАМИ</b>\n\n"
    text += f"Всего ЖК в системе: <b>{len(jk_list)}</b>\n\n"
    
    # Создаем инлайн-клавиатуру с ЖК
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for jk in jk_list:
        # Кнопка для каждого ЖК - показываем дом вместо города
        jk_button = InlineKeyboardButton(
            text=f"🏢 {jk.name} (дом {jk.house})",
            callback_data=f"manage_jk_{jk.id}"
        )
        keyboard.inline_keyboard.append([jk_button])
    
    await state.set_state(ManageJKState.viewing_list)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# Обработка выбора конкретного ЖК - показываем только кнопку "Изменить"
@manage_jk_router.callback_query(F.data.startswith("manage_jk_"))
async def handle_jk_selection(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Показать детали ЖК с кнопкой изменить."""
    jk_id = int(callback.data.split("_")[-1])
    
    jk = await orm_get_jk_by_id(session, jk_id)
    if not jk:
        await callback.answer("❌ ЖК не найден", show_alert=True)
        return
    
    # Формируем информацию о ЖК
    text = f"🏢 <b>{jk.name}</b>\n\n"
    text += f"📍 <b>Адрес:</b> {jk.city}, {jk.street}, {jk.house}\n"
    if jk.block:
        text += f"🏗️ <b>Блок:</b> {jk.block}\n"
    text += f"🆔 <b>ID:</b> {jk.id}\n"
    text += f"📅 <b>Создан:</b> {jk.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    # Клавиатура с кнопками управления
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Изменить", callback_data=f"edit_jk_{jk_id}"),
            InlineKeyboardButton(text="🔧 Услуги", callback_data=f"manage_services_jk_{jk_id}")
        ],
        [
            InlineKeyboardButton(text="⬅️ К списку ЖК", callback_data="back_to_jk_list")
        ]
    ])
    
    # Безопасное обновление сообщения
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Обработка кнопки "Изменить" - запускаем FSM редактирования из add_jk_fsm.py
@manage_jk_router.callback_query(F.data.startswith("edit_jk_"))
async def start_edit_jk(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Запустить процесс редактирования ЖК через add_jk_fsm."""
    jk_id = int(callback.data.split("_")[-1])
    
    jk = await orm_get_jk_by_id(session, jk_id)
    if not jk:
        await callback.answer("❌ ЖК не найден", show_alert=True)
        return
    
    # Импортируем состояния из add_jk_fsm
    from handlers.fsm.add_jk_fsm import JKCreationState
    
    # Сохраняем данные ЖК для редактирования
    await state.update_data(
        editing_jk_id=jk_id,
        current_name=jk.name,
        current_city=jk.city,
        current_street=jk.street,
        current_house=jk.house,
        current_block=jk.block,
        current_image_id=jk.image_id,
        current_bus_image_id=jk.bus_image_id
    )
    
    # Переходим в состояние редактирования названия
    await state.set_state(JKCreationState.name)
    
    await callback.message.delete()
    await callback.message.answer(
        f"✏️ <b>РЕДАКТИРОВАНИЕ ЖК: {jk.name}</b>\n\n"
        f"📝 <b>Текущее название:</b> {jk.name}\n\n"
        "Введите новое название ЖК или точку (.) для сохранения текущего:",
        parse_mode="HTML"
    )
    await callback.answer()


# Обработка кнопки "Назад к списку ЖК"
@manage_jk_router.callback_query(F.data == "back_to_jk_list")
async def back_to_jk_list(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Вернуться к списку ЖК."""
    await state.clear()
    
    # Получаем список всех ЖК
    jk_list = await orm_get_all_jks(session)
    
    if not jk_list:
        await callback.message.delete()
        await callback.message.answer(
            "📋 Список жилых комплексов пуст.\n\n"
            "Используйте команду 'Добавить ЖК' для создания нового комплекса."
        )
        await callback.answer()
        return
    
    # Формируем текст со списком ЖК
    text = "🏢 <b>УПРАВЛЕНИЕ ЖИЛЫМИ КОМПЛЕКСАМИ</b>\n\n"
    text += f"Всего ЖК в системе: <b>{len(jk_list)}</b>\n\n"
    
    # Создаем клавиатуру с ЖК
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for jk in jk_list:
        jk_button = InlineKeyboardButton(
            text=f"🏢 {jk.name} (дом {jk.house})",
            callback_data=f"manage_jk_{jk.id}"
        )
        keyboard.inline_keyboard.append([jk_button])
    
    await state.set_state(ManageJKState.viewing_list)
    
    # Безопасное обновление сообщения
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Функция для внутреннего использования (вызов из add_jk_fsm.py)
async def show_jk_list_internal(message: Message, state: FSMContext, session: AsyncSession):
    """Показать список ЖК без проверки прав (для внутреннего использования)."""
    # Получаем список всех ЖК
    jk_list = await orm_get_all_jks(session)
    
    if not jk_list:
        await message.answer(
            "📋 Список жилых комплексов пуст.\n\n"
            "Используйте команду 'Добавить ЖК' для создания нового комплекса.",
            reply_markup=get_keyboard(
                "Добавить ЖК",
                "Главное меню 🏠",
                placeholder="Управление ЖК",
                sizes=(1, 1)
            )
        )
        return
    
    # Формируем текст со списком ЖК
    text = "🏢 <b>УПРАВЛЕНИЕ ЖИЛЫМИ КОМПЛЕКСАМИ</b>\n\n"
    text += f"Всего ЖК в системе: <b>{len(jk_list)}</b>\n\n"
    
    # Создаем инлайн-клавиатуру с ЖК
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for jk in jk_list:
        # Формируем название кнопки - показываем дом вместо города
        button_text = f"🏢 {jk.name}"
        if jk.house:
            button_text += f" (дом {jk.house})"
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"manage_jk_{jk.id}"
            )
        ])
    
    # Добавляем кнопку возврата
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")
    ])
    
    await state.set_state(ManageJKState.viewing_list)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# Обработчик для возврата в меню добавления ЖК
@manage_jk_router.callback_query(F.data == "back_to_main")
async def back_to_add_jk_menu(callback: CallbackQuery, state: FSMContext):
    """Вернуться в меню добавления ЖК."""
    from handlers.fsm.add_jk_fsm import JKCreationState, ADD_JK_MAIN
    
    await state.set_state(JKCreationState.menu)
    await callback.message.edit_text(
        "🏢 Выберите действие:",
        reply_markup=ADD_JK_MAIN,
        parse_mode=None
    )
    await callback.answer()


# Обработка кнопки "Услуги" - показ сервисных компаний для ЖК
@manage_jk_router.callback_query(F.data.startswith("manage_services_jk_"))
async def show_jk_services(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Показать список сервисных компаний для конкретного ЖК."""
    jk_id = int(callback.data.split("_")[-1])
    
    # Получаем информацию о ЖК
    jk = await orm_get_jk_by_id(session, jk_id)
    if not jk:
        await callback.answer("❌ ЖК не найден", show_alert=True)
        return
    
    # Получаем список поставщиков услуг для данного ЖК
    providers = await orm_get_service_providers_by_jk(session, jk_id, active_only=True)
    
    if not providers:
        # Если поставщиков нет
        text = f"🔧 <b>СЕРВИСНЫЕ КОМПАНИИ</b>\n\n"
        text += f"🏢 <b>ЖК:</b> {jk.name}\n\n"
        text += "❌ Для данного ЖК не настроены сервисные компании"
        
        # Кнопка возврата
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"manage_jk_{jk_id}")]
        ])
    else:
        # Формируем текст со списком поставщиков
        text = f"🔧 <b>СЕРВИСНЫЕ КОМПАНИИ</b>\n\n"
        text += f"🏢 <b>ЖК:</b> {jk.name}\n\n"
        
        for provider in providers:
            # Безопасная обработка категории (provider.category уже объект OfferCategory)
            category = provider.category
            
            text += f"{category.emoji} <b>{category.display_name}:</b> {provider.organization_name or 'Не указано'}\n"
            
            # Обработка телефона (может быть None)
            phone = provider.contact_phone if provider.contact_phone else "не указан"
            text += f"📞 <b>Телефон:</b> {phone}\n"
            
            text += f"👤 <b>Ответственный:</b> {provider.responsible_user_id}\n\n"
        
        text += f"📊 <b>Всего компаний:</b> {len(providers)}"
        
        # Кнопка возврата
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"manage_jk_{jk_id}")]
        ])
    
    # Отправляем сообщение
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except:
        # Если не удалось отредактировать, отправляем новое сообщение
        await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    
    await callback.answer()
