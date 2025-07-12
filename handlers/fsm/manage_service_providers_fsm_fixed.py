# -*- coding: utf-8 -*-
# handlers/fsm/manage_service_providers_fsm.py
"""
FSM для управления поставщиками услуг в ЖК.
Только администраторы могут привязывать организации к ЖК.
"""

import os
from typing import List, Optional
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.orm_jk import orm_get_all_jks, orm_get_jk_by_id
from database.models.orm_user import orm_get_user_by_id
from database.models.orm_user_jk import orm_get_jks_by_user_admin
from database.models.orm_jk_service_provider import (
    orm_add_service_provider,
    orm_get_service_providers_by_jk,
    orm_get_service_provider_by_category,
    orm_update_service_provider,
    orm_deactivate_service_provider
)
from database.enums.user_enums import UserRole
from database.enums.offer_category_enum import OfferCategory
from keyboards.reply import MAIN_KB, get_keyboard
from keyboards.service_provider_keyboards import (
    get_category_keyboard,
    get_providers_keyboard,
    get_jk_selection_keyboard,
    get_phone_input_keyboard,
    get_confirmation_keyboard
)
from services.service_provider_service import (
    check_service_management_access,
    validate_responsible_user,
    validate_organization_name,
    validate_work_schedule
)
from utils.phone_validator import validate_phone, PhoneValidator

manage_service_providers_router = Router()


class ManageServiceProviderStates(StatesGroup):
    """Состояния для управления поставщиками услуг."""
    select_jk = State()          # Выбор ЖК
    view_providers = State()     # Просмотр поставщиков ЖК
    add_provider = State()       # Добавление поставщика
    select_category = State()    # Выбор категории услуг
    input_user_id = State()      # Ввод user_id ответственного
    input_org_info = State()     # Ввод информации об организации
    input_phone = State()        # Ввод контактного телефона
    input_work_schedule = State() # Ввод рабочего времени
    confirm_provider = State()   # Подтверждение создания


@manage_service_providers_router.message(Command("manage_services"))
async def cmd_manage_services(message: Message, state: FSMContext, session: AsyncSession):
    """Команда для управления поставщиками услуг."""
    await state.clear()
    user_id = message.from_user.id
    
    # Проверяем права доступа
    has_access, error_msg = await check_service_management_access(user_id, session)
    if not has_access:
        await message.answer(error_msg, reply_markup=MAIN_KB)
        return
    
    # Получаем доступные ЖК для пользователя
    user = await orm_get_user_by_id(session, user_id)
    
    if user.role == UserRole.ADMIN:
        # Суперадмин видит все ЖК
        available_jks = await orm_get_all_jks(session)
    else:
        # Админ ЖК видит только свои ЖК
        available_jks = await orm_get_jks_by_user_admin(session, user_id)
    
    if not available_jks:
        await message.answer(
            "❌ Нет доступных ЖК для управления поставщиками услуг.",
            reply_markup=MAIN_KB
        )
        return
    
    if len(available_jks) == 1:
        # Если ЖК только один, сразу переходим к просмотру поставщиков
        jk = available_jks[0]
        await state.update_data(selected_jk_id=jk.id)
        await state.set_state(ManageServiceProviderStates.view_providers)
        
        providers = await orm_get_service_providers_by_jk(session, jk.id)
        
        providers_text = f"🏢 <b>ЖК: {jk.name}</b>\n\n"
        if providers:
            providers_text += "📋 <b>Поставщики услуг:</b>\n\n"
            for i, provider in enumerate(providers, 1):
                category_emoji = OfferCategory.get_emoji_by_value(provider.category)
                status = "✅ Активен" if provider.is_active else "❌ Неактивен"
                notifications = "🔔 Вкл" if provider.receives_notifications else "🔕 Выкл"
                
                providers_text += (
                    f"{i}. {category_emoji} <b>{provider.organization_name}</b>\n"
                    f"   Статус: {status} | Уведомления: {notifications}\n\n"
                )
        else:
            providers_text += "❌ Поставщики услуг не добавлены."
        
        await message.answer(
            providers_text,
            parse_mode="HTML",
            reply_markup=get_providers_keyboard(providers, jk.id)
        )
    else:
        # Если ЖК несколько, показываем список для выбора
        await state.set_state(ManageServiceProviderStates.select_jk)
        await message.answer(
            "🏢 <b>Выберите ЖК для управления поставщиками услуг:</b>",
            parse_mode="HTML",
            reply_markup=get_jk_selection_keyboard(available_jks)
        )


@manage_service_providers_router.callback_query(F.data.startswith("select_jk:"))
async def handle_jk_selection(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка выбора ЖК."""
    jk_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    # Проверяем права доступа к выбранному ЖК
    has_access, error_msg = await check_service_management_access(user_id, session, jk_id)
    if not has_access:
        await callback.answer(error_msg, show_alert=True)
        return
    
    await state.update_data(selected_jk_id=jk_id)
    await state.set_state(ManageServiceProviderStates.view_providers)
    
    # Получаем информацию о ЖК и поставщиках
    jk = await orm_get_jk_by_id(session, jk_id)
    providers = await orm_get_service_providers_by_jk(session, jk_id)
    
    providers_text = f"🏢 <b>ЖК: {jk.name}</b>\n\n"
    if providers:
        providers_text += "📋 <b>Поставщики услуг:</b>\n\n"
        for i, provider in enumerate(providers, 1):
            category_emoji = OfferCategory.get_emoji_by_value(provider.category)
            status = "✅ Активен" if provider.is_active else "❌ Неактивен"
            notifications = "🔔 Вкл" if provider.receives_notifications else "🔕 Выкл"
            
            providers_text += (
                f"{i}. {category_emoji} <b>{provider.organization_name}</b>\n"
                f"   Статус: {status} | Уведомления: {notifications}\n\n"
            )
    else:
        providers_text += "❌ Поставщики услуг не добавлены."
    
    await callback.message.edit_text(
        providers_text,
        parse_mode="HTML",
        reply_markup=get_providers_keyboard(providers, jk_id)
    )
    await callback.answer()


@manage_service_providers_router.callback_query(F.data.startswith("add_provider:"))
async def start_add_provider(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Начало процесса добавления поставщика услуг."""
    jk_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    # Проверяем права доступа
    has_access, error_msg = await check_service_management_access(user_id, session, jk_id)
    if not has_access:
        await callback.answer(error_msg, show_alert=True)
        return
    
    await state.update_data(selected_jk_id=jk_id)
    await state.set_state(ManageServiceProviderStates.select_category)
    
    jk = await orm_get_jk_by_id(session, jk_id)
    
    await callback.message.edit_text(
        f"🏢 <b>ЖК: {jk.name}</b>\n\n"
        "📑 <b>Добавление поставщика услуг</b>\n\n"
        "Выберите категорию услуг:",
        parse_mode="HTML",
        reply_markup=get_category_keyboard()
    )
    await callback.answer()


@manage_service_providers_router.callback_query(F.data.startswith("select_category:"))
async def handle_category_selection(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка выбора категории услуг."""
    category_value = callback.data.split(":")[1]
    
    try:
        category = OfferCategory(category_value)
    except ValueError:
        await callback.answer("❌ Неизвестная категория", show_alert=True)
        return
    
    # Проверяем, нет ли уже поставщика для этой категории в ЖК
    data = await state.get_data()
    jk_id = data.get("selected_jk_id")
    
    existing_provider = await orm_get_service_provider_by_category(session, jk_id, category)
    if existing_provider:
        await callback.answer(
            f"❌ Поставщик для категории '{category.get_display_name()}' уже существует",
            show_alert=True
        )
        return
    
    await state.update_data(category=category_value)
    await state.set_state(ManageServiceProviderStates.input_user_id)
    
    await callback.message.edit_text(
        f"✅ Выбрана категория: <b>{category.get_display_name()}</b> {category.get_emoji()}\n\n"
        "👤 <b>Введите User ID ответственного лица</b>\n\n"
        "Это должен быть пользователь, зарегистрированный в боте, который будет получать уведомления о новых заявках.\n\n"
        "💡 <i>User ID можно узнать в профиле пользователя или попросить его отправить команду /my_id</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@manage_service_providers_router.message(ManageServiceProviderStates.input_user_id)
async def handle_user_id_input(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ввода User ID ответственного лица."""
    try:
        responsible_user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ User ID должен быть числом. Попробуйте еще раз:")
        return
    
    # Валидируем пользователя
    is_valid, error_msg, user_info = await validate_responsible_user(responsible_user_id, session)
    if not is_valid:
        await message.answer(f"{error_msg}\n\nПопробуйте еще раз:")
        return
    
    await state.update_data(responsible_user_id=responsible_user_id, user_info=user_info)
    await state.set_state(ManageServiceProviderStates.input_org_info)
    
    user_name = user_info['first_name'] or 'Неизвестно'
    if user_info['last_name']:
        user_name += f" {user_info['last_name']}"
    if user_info['username']:
        user_name += f" (@{user_info['username']})"
    
    await message.answer(
        f"✅ <b>Ответственное лицо:</b> {user_name}\n\n"
        "🏢 <b>Введите название организации:</b>\n"
        "Например: ООО 'Домофон-Сервис'",
        parse_mode="HTML"
    )


@manage_service_providers_router.message(ManageServiceProviderStates.input_org_info)
async def handle_org_info_input(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ввода информации об организации."""
    organization_name = message.text.strip()
    
    # Валидируем название организации
    is_valid, error_msg = validate_organization_name(organization_name)
    if not is_valid:
        await message.answer(f"{error_msg}\n\nПопробуйте еще раз:")
        return
    
    await state.update_data(organization_name=organization_name)
    await state.set_state(ManageServiceProviderStates.input_phone)
    
    await message.answer(
        f"✅ <b>Организация:</b> {organization_name}\n\n"
        "📞 <b>Введите контактный телефон организации:</b>\n"
        "Формат: +7XXXXXXXXXX или можете пропустить этот шаг",
        parse_mode="HTML",
        reply_markup=get_phone_input_keyboard()
    )


@manage_service_providers_router.message(ManageServiceProviderStates.input_phone)
async def handle_phone_input(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ввода контактного телефона."""
    phone = message.text.strip()
    
    # Валидируем телефон
    validator = PhoneValidator()
    if not validator.validate(phone):
        await message.answer(
            "❌ Неверный формат телефона.\n"
            "Используйте формат: +7XXXXXXXXXX\n\n"
            "Попробуйте еще раз или нажмите 'Пропустить':",
            reply_markup=get_phone_input_keyboard()
        )
        return
    
    # Нормализуем телефон
    normalized_phone = validator.normalize(phone)
    await state.update_data(contact_phone=normalized_phone)
    await state.set_state(ManageServiceProviderStates.input_work_schedule)
    
    await message.answer(
        f"✅ <b>Телефон:</b> {normalized_phone}\n\n"
        "🕒 <b>Введите рабочее время:</b>\n"
        "Например: 'Пн-Пт 9:00-18:00' или 'Круглосуточно'",
        parse_mode="HTML"
    )


@manage_service_providers_router.callback_query(F.data == "skip_phone")
async def handle_skip_phone(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Пропуск ввода телефона."""
    await state.set_state(ManageServiceProviderStates.input_work_schedule)
    
    await callback.message.edit_text(
        "⏭️ <b>Телефон пропущен</b>\n\n"
        "🕒 <b>Введите рабочее время:</b>\n"
        "Например: 'Пн-Пт 9:00-18:00' или 'Круглосуточно'",
        parse_mode="HTML"
    )
    await callback.answer()


@manage_service_providers_router.message(ManageServiceProviderStates.input_work_schedule)
async def handle_work_schedule_input(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ввода рабочего времени."""
    work_schedule = message.text.strip()
    
    # Валидируем рабочее время
    is_valid, error_msg = validate_work_schedule(work_schedule)
    if not is_valid:
        await message.answer(f"{error_msg}\n\nПопробуйте еще раз:")
        return
    
    await state.update_data(work_schedule=work_schedule)
    await show_provider_confirmation(message, state, session)


async def show_provider_confirmation(message: Message, state: FSMContext, session: AsyncSession):
    """Показывает подтверждение создания поставщика услуг."""
    data = await state.get_data()
    
    # Получаем информацию о ЖК
    jk = await orm_get_jk_by_id(session, data['selected_jk_id'])
    category = OfferCategory(data['category'])
    user_info = data['user_info']
    
    user_name = user_info['first_name'] or 'Неизвестно'
    if user_info['last_name']:
        user_name += f" {user_info['last_name']}"
    if user_info['username']:
        user_name += f" (@{user_info['username']})"
    
    phone_text = data.get('contact_phone', 'не указан')
    
    confirmation_text = (
        "✅ <b>Подтверждение создания поставщика услуг</b>\n\n"
        f"🏢 <b>ЖК:</b> {jk.name}\n"
        f"📑 <b>Категория:</b> {category.get_display_name()} {category.get_emoji()}\n"
        f"🏛️ <b>Организация:</b> {data['organization_name']}\n"
        f"👤 <b>Ответственное лицо:</b> {user_name}\n"
        f"📞 <b>Телефон:</b> {phone_text}\n"
        f"🕒 <b>Рабочее время:</b> {data['work_schedule']}\n\n"
        "Создать поставщика услуг?"
    )
    
    await state.set_state(ManageServiceProviderStates.confirm_provider)
    await message.answer(
        confirmation_text,
        parse_mode="HTML",
        reply_markup=get_confirmation_keyboard()
    )


@manage_service_providers_router.callback_query(F.data == "confirm_create_provider")
async def confirm_create_provider(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Подтверждение создания поставщика услуг."""
    data = await state.get_data()
    
    # Создаем поставщика услуг
    provider_data = {
        'jk_id': data['selected_jk_id'],
        'category': data['category'],
        'organization_name': data['organization_name'],
        'responsible_user_id': data['responsible_user_id'],
        'contact_phone': data.get('contact_phone'),
        'work_schedule': data['work_schedule'],
        'is_active': True,
        'receives_notifications': True
    }
    
    try:
        provider = await orm_add_service_provider(session, provider_data)
        await session.commit()
        
        # Получаем информацию о ЖК для финального сообщения
        jk = await orm_get_jk_by_id(session, data['selected_jk_id'])
        category = OfferCategory(data['category'])
        
        await callback.message.edit_text(
            f"✅ <b>Поставщик услуг успешно создан!</b>\n\n"
            f"🏢 <b>ЖК:</b> {jk.name}\n"
            f"📑 <b>Категория:</b> {category.get_display_name()} {category.get_emoji()}\n"
            f"🏛️ <b>Организация:</b> {data['organization_name']}\n\n"
            "Поставщик получает уведомления о новых заявках по этой категории.",
            parse_mode="HTML",
            reply_markup=MAIN_KB
        )
        
        await state.clear()
        await callback.answer("Поставщик создан!")
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при создании поставщика услуг:\n{str(e)}",
            reply_markup=MAIN_KB
        )
        await callback.answer("Ошибка создания")


@manage_service_providers_router.callback_query(F.data == "cancel_add_provider")
async def cancel_add_provider(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Отмена создания поставщика услуг."""
    await callback.message.edit_text(
        "❌ <b>Создание поставщика услуг отменено</b>",
        parse_mode="HTML",
        reply_markup=MAIN_KB
    )
    await state.clear()
    await callback.answer("Отменено")


@manage_service_providers_router.callback_query(F.data == "back_to_jk_selection")
async def back_to_jk_selection(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Возврат к выбору ЖК."""
    user_id = callback.from_user.id
    
    # Получаем доступные ЖК
    user = await orm_get_user_by_id(session, user_id)
    if user.role == UserRole.ADMIN:
        available_jks = await orm_get_all_jks(session)
    else:
        available_jks = await orm_get_jks_by_user_admin(session, user_id)
    
    await state.set_state(ManageServiceProviderStates.select_jk)
    await callback.message.edit_text(
        "🏢 <b>Выберите ЖК для управления поставщиками услуг:</b>",
        parse_mode="HTML",
        reply_markup=get_jk_selection_keyboard(available_jks)
    )
    await callback.answer()


@manage_service_providers_router.callback_query(F.data == "to_main_menu")
async def to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Переход в главное меню."""
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>",
        parse_mode="HTML",
        reply_markup=MAIN_KB
    )
    await state.clear()
    await callback.answer()


# Обработчик для некорректного ввода в состоянии input_user_id
@manage_service_providers_router.message(ManageServiceProviderStates.input_user_id)
async def invalid_user_id_input(message: Message):
    """Обработчик некорректного ввода User ID."""
    await message.answer(
        "❌ Пожалуйста, введите корректный User ID (число).\n"
        "Попробуйте еще раз:"
    )
