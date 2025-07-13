# -*- coding: utf-8 -*-
# handlers/fsm/manage_service_providers_fsm.py
"""
FSM для управления поставщиками услуг в ЖК.
Только администраторы могут привязывать организации к ЖК.
"""

import os
from typing import Optional
from aiogram.types import Message, CallbackQuery
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
from keyboards.reply import MAIN_KB, CONTROL_SERVICE_PROVIDER_KB, get_keyboard
from keyboards.service_provider_keyboards import (
    get_category_keyboard,
    get_simple_jk_selection_keyboard,
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
from filters.chat_types import IsAdmin

manage_service_providers_router = Router()


def is_creator_by_environment(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь создателем по переменной окружения CREATOR_ID.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        bool: True если пользователь является создателем
    """
    creator_ids = os.getenv("CREATOR_ID")
    return creator_ids and str(user_id) in creator_ids.split(",")


class ManageServiceProviderStates(StatesGroup):
    """Состояния для управления поставщиками услуг."""
    select_jk_for_add = State()  # Выбор ЖК для добавления (упрощенный)
    select_category = State()    # Выбор категории услуг
    input_user_id = State()      # Ввод user_id ответственного
    input_org_info = State()     # Ввод информации об организации
    input_phone = State()        # Ввод контактного телефона
    input_work_schedule = State() # Ввод рабочего времени
    confirm_provider = State()   # Подтверждение создания


@manage_service_providers_router.message(Command("manage_services"), IsAdmin())
async def cmd_manage_services(message: Message, state: FSMContext, session: AsyncSession):
    """Команда для управления поставщиками услуг."""
    await state.clear()
    user_id = message.from_user.id
    
    # Получаем доступные ЖК для пользователя
    user = await orm_get_user_by_id(session, user_id)
    if not user:
        await message.answer(
            "❌ Ошибка: пользователь не найден в базе данных.",
            reply_markup=MAIN_KB
        )
        return
    
    # Проверяем, является ли пользователь создателем по CREATOR_ID
    is_creator_by_env = is_creator_by_environment(user_id)
    
    if is_creator_by_env or user.role in [UserRole.ADMIN, UserRole.CREATOR]:
        # Суперадмин, создатель и пользователи из CREATOR_ID видят все ЖК
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
    
    # Показываем меню управления поставщиками услуг
    await message.answer(
        "🔧 <b>Управление поставщиками услуг</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=CONTROL_SERVICE_PROVIDER_KB
    )


@manage_service_providers_router.callback_query(F.data.startswith("select_jk_for_add:"))
async def handle_jk_selection_for_add(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка выбора ЖК для добавления поставщика."""
    jk_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    # Проверяем права доступа к выбранному ЖК
    has_access, error_msg = await check_service_management_access(user_id, session, jk_id)
    if not has_access:
        await callback.answer(error_msg, show_alert=True)
        return
    
    await state.update_data(selected_jk_id=jk_id)
    await state.set_state(ManageServiceProviderStates.select_category)
    
    # Получаем информацию о ЖК
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
        category = OfferCategory.from_string(category_value)
    except ValueError:
        await callback.answer("❌ Неизвестная категория", show_alert=True)
        return
    
    await state.update_data(category=category)
    await state.set_state(ManageServiceProviderStates.input_user_id)
    
    await callback.message.edit_text(
        f"✅ Выбрана категория: <b>{category.display_name}</b> {category.emoji}\n\n"
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
        
        # Проверяем валидность User ID
        if responsible_user_id <= 0:
            await message.answer("❌ User ID должен быть положительным числом. Попробуйте еще раз:")
            return
        
        if responsible_user_id > 9999999999:  # Telegram User ID не может быть больше 10 цифр
            await message.answer("❌ User ID слишком большой. Попробуйте еще раз:")
            return
            
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
    
    # ИСПРАВЛЕНО: Использовать правильный метод валидации
    is_valid, formatted_phone, error_msg = PhoneValidator.validate_and_format(phone)
    
    if not is_valid:
        await message.answer(
            f"❌ {error_msg}\n"
            "Используйте формат: +7XXXXXXXXXX\n\n"
            "Попробуйте еще раз или нажмите 'Пропустить':",
            reply_markup=get_phone_input_keyboard()
        )
        return
    
    # Сохраняем отформатированный телефон
    await state.update_data(contact_phone=formatted_phone)
    await state.set_state(ManageServiceProviderStates.input_work_schedule)
    
    await message.answer(
        f"✅ <b>Телефон:</b> {formatted_phone}\n\n"
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
    category = data['category']  # category уже объект OfferCategory
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
        f"📑 <b>Категория:</b> {category.display_name} {category.emoji}\n"
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
    print(f"DEBUG: confirm_create_provider вызвана, callback.data = {callback.data}")
    data = await state.get_data()
    
    # Создаем поставщика услуг
    provider_data = {
        'jk_id': data['selected_jk_id'],
        'category': data['category'],
        'organization_name': data['organization_name'],
        'responsible_user_id': data['responsible_user_id'],
        'contact_phone': data.get('contact_phone'),
        'description': f"Рабочее время: {data['work_schedule']}",  # Сохраняем рабочее время в описание
        'is_active': True,
        'receives_notifications': True,
        'auto_assign_offers': True,  # Автоматически назначать заявки
        'priority': 1,  # Высший приоритет
        'created_by_user_id': callback.from_user.id  # Кто создал запись
    }
    
    try:
        provider = await orm_add_service_provider(session, provider_data)
        await session.commit()
        
        # Получаем информацию о ЖК для финального сообщения
        jk = await orm_get_jk_by_id(session, data['selected_jk_id'])
        category = OfferCategory(data['category'])
        
        # ИСПРАВЛЕНО: Убираем reply_markup из edit_text
        await callback.message.edit_text(
            f"✅ <b>Поставщик услуг успешно создан!</b>\n\n"
            f"🏢 <b>ЖК:</b> {jk.name}\n"
            f"📑 <b>Категория:</b> {category.display_name} {category.emoji}\n"
            f"🏛️ <b>Организация:</b> {data['organization_name']}\n\n"
            "✅ <b>Пользователь получил роль 'Поставщик услуг'</b>\n\n"
            "Поставщик получает уведомления о новых заявках по этой категории.",
            parse_mode="HTML"
        )
        
        # ДОБАВЛЕНО: Отправляем отдельное сообщение с Reply клавиатурой
        await callback.message.answer(
            "🏠 Возвращайтесь в главное меню для продолжения работы:",
            reply_markup=MAIN_KB
        )
        
        await state.clear()
        await callback.answer("Поставщик создан!")
        
    except Exception as e:
        await session.rollback()  # Откатываем транзакцию в случае ошибки
        await callback.message.edit_text(
            f"❌ Ошибка при создании поставщика услуг:\n{str(e)}"
        )
        
        # ДОБАВЛЕНО: Отправляем отдельное сообщение с Reply клавиатурой
        await callback.message.answer(
            "🏠 Возвращайтесь в главное меню:",
            reply_markup=MAIN_KB
        )
        await callback.answer("Ошибка создания")


@manage_service_providers_router.callback_query(F.data == "cancel_add_provider")
async def cancel_add_provider(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Отмена создания поставщика услуг."""
    print(f"DEBUG: cancel_add_provider вызвана, callback.data = {callback.data}")
    
    await callback.message.edit_text(
        "❌ <b>Создание поставщика услуг отменено</b>",
        parse_mode="HTML"
    )
    
    # Отправляем отдельное сообщение с Reply клавиатурой
    await callback.message.answer(
        "🏠 Возвращайтесь в главное меню:",
        reply_markup=MAIN_KB
    )
    
    await state.clear()
    await callback.answer("Отменено")
