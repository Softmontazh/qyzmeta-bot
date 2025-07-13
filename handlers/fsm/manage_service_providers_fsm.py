# -*- coding: utf-8 -*-
# handlers/fsm/manage_service_providers_fsm.py
"""
FSM для управления поставщиками услуг в ЖК.

Система работает через заявки:
1. Администраторы создают заявки на поставку услуг через этот интерфейс
2. Все заявки создаются в неактивном состоянии (is_active=False)
3. Заявки требуют одобрения вышестоящим администратором
4. После одобрения пользователь получает роль SERVICE_PROVIDER и доступ к панели

Это обеспечивает контроль качества и предотвращает создание некачественных записей.
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
    orm_deactivate_service_provider,
    orm_get_service_provider_by_id,
    orm_activate_service_provider_request,
    orm_reject_service_provider_request,
    orm_get_pending_service_provider_requests
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
    
    # Создаем кнопку для быстрого ввода текущего User ID
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    current_user_id = callback.from_user.id
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📱 Мой ID: {current_user_id}",
                    callback_data=f"use_my_id:{current_user_id}"
                )
            ],
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_provider")
            ]
        ]
    )
    
    await callback.message.edit_text(
        f"✅ Выбрана категория: <b>{category.display_name}</b> {category.emoji}\n\n"
        "👤 <b>Введите User ID ответственного лица</b>\n\n"
        f"🆔 <b>Ваш User ID:</b> <code>{current_user_id}</code>\n\n"
        "Это должен быть пользователь, зарегистрированный в боте, который будет получать уведомления о новых заявках.\n\n"
        "💡 <i>Вы можете использовать свой ID или ввести другой User ID</i>",
        parse_mode="HTML",
        reply_markup=keyboard
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
    
    # Проверяем наличие required keys
    jk_id = data.get('selected_jk_id') or data.get('jk_id')
    if not jk_id:
        await message.answer(
            "❌ Ошибка: потеряна информация о выбранном ЖК.\n"
            "Попробуйте начать заново с команды /manage_service_providers"
        )
        await state.clear()
        return
    
    # Получаем информацию о ЖК
    jk = await orm_get_jk_by_id(session, jk_id)
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
    data = await state.get_data()
    
    # Проверяем наличие required keys
    jk_id = data.get('selected_jk_id') or data.get('jk_id')
    if not jk_id:
        await callback.message.edit_text(
            "❌ Ошибка: потеряна информация о выбранном ЖК.\n"
            "Попробуйте начать заново с команды /manage_service_providers"
        )
        await state.clear()
        await callback.answer()
        return
    
    # Создаем поставщика услуг
    provider_data = {
        'jk_id': jk_id,
        'category': data['category'],
        'organization_name': data['organization_name'],
        'responsible_user_id': data['responsible_user_id'],
        'contact_phone': data.get('contact_phone'),
        'description': f"Рабочее время: {data['work_schedule']}",
        'is_active': False,  # Заявка неактивна до одобрения администратором
        'receives_notifications': True,
        'auto_assign_offers': True,
        'priority': 1,
        'created_by_user_id': callback.from_user.id
    }
    
    try:
        provider = await orm_add_service_provider(session, provider_data)
        await session.commit()
        
        # Получаем информацию о ЖК для финального сообщения
        jk = await orm_get_jk_by_id(session, jk_id)
        category = OfferCategory(data['category'])
        
        await callback.message.edit_text(
            f"✅ <b>Заявка на поставку услуг создана!</b>\n\n"
            f"🏢 <b>ЖК:</b> {jk.name}\n"
            f"📑 <b>Категория:</b> {category.display_name} {category.emoji}\n"
            f"🏛️ <b>Организация:</b> {data['organization_name']}\n\n"
            "⏳ <b>Заявка передана на рассмотрение администратору</b>\n\n"
            "Пользователь получит уведомление о принятом решении после одобрения.",
            parse_mode="HTML"
        )
        
        await callback.message.answer(
            "🏠 Возвращайтесь в главное меню для продолжения работы:",
            reply_markup=MAIN_KB
        )
        
        await state.clear()
        await callback.answer("Поставщик создан!")
        
    except Exception as e:
        await session.rollback()
        await callback.message.edit_text(
            f"❌ Ошибка при создании поставщика услуг:\n{str(e)}"
        )
        
        await callback.message.answer(
            "🏠 Возвращайтесь в главное меню:",
            reply_markup=MAIN_KB
        )
        await callback.answer("Ошибка создания")


@manage_service_providers_router.callback_query(F.data == "cancel_add_provider")
async def cancel_add_provider(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Отмена создания поставщика услуг."""
    
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


@manage_service_providers_router.callback_query(F.data.startswith("use_my_id:"))
async def handle_use_my_id(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка нажатия кнопки 'Мой ID'"""
    user_id = int(callback.data.split(":")[1])
    
    # Валидируем пользователя
    is_valid, error_msg, user_info = await validate_responsible_user(user_id, session)
    if not is_valid:
        await callback.answer(f"❌ {error_msg}", show_alert=True)
        return
    
    # Получаем текущие данные состояния и добавляем к ним новые
    await state.update_data(responsible_user_id=user_id, user_info=user_info)
    await state.set_state(ManageServiceProviderStates.input_org_info)
    
    user_name = user_info['first_name'] or 'Неизвестно'
    if user_info['last_name']:
        user_name += f" {user_info['last_name']}"
    if user_info['username']:
        user_name += f" (@{user_info['username']})"
    
    await callback.message.edit_text(
        f"✅ <b>Ответственное лицо:</b> {user_name}\n\n"
        "🏢 <b>Введите название организации:</b>\n"
        "Например: ООО 'Домофон-Сервис'",
        parse_mode="HTML"
    )
    await callback.answer()


# ОБРАБОТЧИКИ ДЛЯ УПРАВЛЕНИЯ ЗАЯВКАМИ НА ПОСТАВКУ УСЛУГ

@manage_service_providers_router.message(F.text == "Заявки на поставку услуг", IsAdmin())
async def handle_pending_requests_button(message: Message, state: FSMContext, session: AsyncSession):
    """Показать заявки на поставку услуг в ожидании одобрения"""
    user_id = message.from_user.id
    
    # Получаем доступные ЖК для пользователя
    user = await orm_get_user_by_id(session, user_id)
    is_creator_by_env = is_creator_by_environment(user_id)
    
    if is_creator_by_env or user.role in [UserRole.ADMIN, UserRole.CREATOR]:
        # Суперадмин и создатель видят все заявки
        pending_requests = await orm_get_pending_service_provider_requests(session)
    else:
        # Админ ЖК видит только заявки по своим ЖК
        available_jks = await orm_get_jks_by_user_admin(session, user_id)
        jk_ids = [jk.id for jk in available_jks]
        
        pending_requests = []
        for jk_id in jk_ids:
            jk_requests = await orm_get_pending_service_provider_requests(session, jk_id)
            pending_requests.extend(jk_requests)
    
    if not pending_requests:
        await message.answer(
            "✅ <b>Нет заявок в ожидании</b>\n\n"
            "В данный момент нет заявок на поставку услуг, "
            "ожидающих вашего одобрения.",
            parse_mode="HTML"
        )
        return
    
    # Группируем заявки по ЖК
    requests_by_jk = {}
    for req in pending_requests:
        jk_name = req.jk.name
        if jk_name not in requests_by_jk:
            requests_by_jk[jk_name] = []
        requests_by_jk[jk_name].append(req)
    
    # Формируем сообщение
    message_text = f"📋 <b>Заявки на поставку услуг</b>\n\n"
    message_text += f"🔍 <b>Всего заявок:</b> {len(pending_requests)}\n\n"
    
    for jk_name, requests in requests_by_jk.items():
        message_text += f"🏢 <b>{jk_name}</b> ({len(requests)} заявок)\n"
        
        for req in requests:
            message_text += (
                f"  📝 #{req.id} - {req.category.emoji} {req.category.display_name}\n"
                f"  👤 {req.organization_name or 'Не указано'}\n"
                f"  📞 {req.contact_phone or 'Не указан'}\n"
                f"  📅 {req.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
    
    # Создаем inline клавиатуру с заявками
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard_buttons = []
    
    for req in pending_requests[:10]:  # Показываем первые 10 заявок
        button_text = f"#{req.id} {req.category.emoji} {req.jk.name[:15]}..."
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"review_request:{req.id}"
            )
        ])
    
    if len(pending_requests) > 10:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"📄 Показать ещё ({len(pending_requests) - 10})",
                callback_data="show_more_requests"
            )
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(
        message_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@manage_service_providers_router.callback_query(F.data.startswith("review_request:"))
async def review_service_request(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Просмотр детальной информации о заявке"""
    request_id = int(callback.data.split(":")[1])
    
    # Получаем заявку С ЗАГРУЖЕННЫМ ЖК
    from database.models.orm_jk_service_provider import orm_get_service_provider_by_id_with_jk
    request = await orm_get_service_provider_by_id_with_jk(session, request_id)
    if not request or request.is_active:
        await callback.answer("❌ Заявка не найдена или уже обработана", show_alert=True)
        return
    
    # Получаем информацию о пользователе
    user = await orm_get_user_by_id(session, request.responsible_user_id)
    user_info = f"{user.first_name}"
    if user.last_name:
        user_info += f" {user.last_name}"
    if user.username:
        user_info += f" (@{user.username})"
    
    # Формируем детальное сообщение
    details_text = (
        f"📋 <b>Заявка #{request.id}</b>\n\n"
        f"🏢 <b>ЖК:</b> {request.jk.name}\n"
        f"📍 <b>Адрес:</b> {request.jk.city}, {request.jk.street}, {request.jk.house}\n"
        f"🔧 <b>Услуга:</b> {request.category.emoji} {request.category.display_name}\n\n"
        f"👤 <b>Заявитель:</b> {user_info}\n"
        f"🆔 <b>User ID:</b> {request.responsible_user_id}\n"
        f"🏛️ <b>Организация:</b> {request.organization_name}\n"
        f"📞 <b>Телефон:</b> {request.contact_phone}\n"
    )
    
    if request.contact_email:
        details_text += f"📧 <b>Email:</b> {request.contact_email}\n"
    
    if request.description:
        details_text += f"\n📝 <b>Описание:</b>\n{request.description}\n"
    
    details_text += f"\n📅 <b>Подано:</b> {request.created_at.strftime('%d.%m.%Y в %H:%M')}"
    
    # Кнопки одобрения/отклонения
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить",
                    callback_data=f"approve_request:{request_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject_request:{request_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад к списку",
                    callback_data="back_to_requests_list"
                )
            ]
        ]
    )
    
    await callback.message.edit_text(
        details_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@manage_service_providers_router.callback_query(F.data.startswith("approve_request:"))
async def approve_service_request(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Одобрить заявку на поставку услуг"""
    request_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    # Активируем заявку и меняем роль пользователя
    success = await orm_activate_service_provider_request(session, request_id, user_id)
    
    if success:
        await session.commit()
        
        await callback.message.edit_text(
            f"✅ <b>Заявка #{request_id} одобрена!</b>\n\n"
            f"Пользователю назначена роль поставщика услуг.\n"
            f"Он получит доступ к панели управления.",
            parse_mode="HTML"
        )
        
        # Отправляем уведомление пользователю (опционально)
        # await notify_user_about_approved_request(request.responsible_user_id, request)
        
    else:
        await callback.message.edit_text(
            f"❌ <b>Ошибка при одобрении заявки #{request_id}</b>\n\n"
            f"Заявка не найдена или уже обработана.",
            parse_mode="HTML"
        )
    
    await callback.answer("Заявка обработана" if success else "Ошибка обработки")


@manage_service_providers_router.callback_query(F.data.startswith("reject_request:"))
async def reject_service_request(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Отклонить заявку на поставку услуг"""
    request_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    # Получаем информацию о заявке перед удалением
    request = await orm_get_service_provider_by_id(session, request_id)
    if not request:
        await callback.answer("❌ Заявка не найдена", show_alert=True)
        return
    
    # Отклоняем заявку (удаляем из базы)
    success = await orm_reject_service_provider_request(session, request_id, user_id)
    
    if success:
        await session.commit()
        
        await callback.message.edit_text(
            f"❌ <b>Заявка #{request_id} отклонена</b>\n\n"
            f"Заявка удалена из системы.\n"
            f"Пользователь остается в роли USER.",
            parse_mode="HTML"
        )
        
        # Отправляем уведомление пользователю (опционально)
        # await notify_user_about_rejected_request(request.responsible_user_id, request)
        
    else:
        await callback.message.edit_text(
            f"❌ <b>Ошибка при отклонении заявки #{request_id}</b>",
            parse_mode="HTML"
        )
    
    await callback.answer("Заявка отклонена" if success else "Ошибка обработки")


@manage_service_providers_router.callback_query(F.data == "back_to_requests_list")
async def back_to_requests_list(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Возврат к списку заявок"""
    # Просто перенаправляем к обработчику показа заявок
    await handle_pending_requests_button(callback.message, state, session)
    await callback.answer()
