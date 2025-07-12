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


# Проверка прав доступа
async def check_service_management_access(user_id: int, session: AsyncSession, jk_id: Optional[int] = None) -> tuple[bool, str]:
    """
    Проверка прав на управление поставщиками услуг.
    Возвращает (has_access, access_level)
    """
    # 1. Проверка глобальных админов (CREATOR)
    creator_ids = os.getenv("CREATOR_ID", "").split(",")
    if str(user_id) in creator_ids:
        return True, "CREATOR"
    
    # 2. Проверка роли в БД
    user = await orm_get_user_by_id(session, user_id)
    if user and user.role in [UserRole.CREATOR, UserRole.SUPERADMIN]:
        return True, "GLOBAL_ADMIN"
    
    # 3. Проверка администратора конкретного ЖК
    if jk_id:
        from database.models.orm_user_jk import orm_check_user_is_jk_admin
        is_jk_admin = await orm_check_user_is_jk_admin(session, user_id, jk_id)
        if is_jk_admin:
            return True, "JK_ADMIN"
    
    # 4. Проверка есть ли у пользователя хотя бы один ЖК в управлении
    admin_jks = await orm_get_jks_by_user_admin(session, user_id)
    if admin_jks:
        return True, "JK_ADMIN_LIMITED"
    
    return False, "NO_ACCESS"


def get_category_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с категориями услуг."""
    categories = [
        (OfferCategory.DOMOFON, "🔔 Домофон"),
        (OfferCategory.VIDEO, "📹 Видеонаблюдение"),
        (OfferCategory.ELEKTRIKA, "⚡ Электрика"),
        (OfferCategory.SANTEHNIKA, "🚿 Сантехника"),
        (OfferCategory.BLAGOUSTROYSTVO, "🌳 Благоустройство"),
        (OfferCategory.REPAIR, "🔧 Ремонт"),
        (OfferCategory.DRUGOE, "📝 Другое"),
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for category, display_name in categories:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=display_name,
                callback_data=f"select_category:{category.value}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_jk_selection")
    ])
    
    return keyboard


def get_providers_keyboard(providers: List, jk_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для управления поставщиками услуг."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    if providers:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="📋 Список поставщиков", callback_data="show_providers_list")
        ])
    
    keyboard.inline_keyboard.extend([
        [InlineKeyboardButton(text="➕ Добавить поставщика", callback_data=f"add_provider:{jk_id}")],
        [InlineKeyboardButton(text="🔙 Выбрать другой ЖК", callback_data="back_to_jk_selection")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main_menu")]
    ])
    
    return keyboard


# Команда для входа в управление поставщиками услуг
@manage_service_providers_router.message(Command("manage_services"))
@manage_service_providers_router.message(F.text.lower().contains("управление услугами"))
async def cmd_manage_services(message: Message, state: FSMContext, session: AsyncSession):
    """Начать управление поставщиками услуг."""
    user_id = message.from_user.id
    
    # Проверяем права доступа
    has_access, access_level = await check_service_management_access(user_id, session)
    
    if not has_access:
        await message.answer(
            "❌ У вас нет прав для управления поставщиками услуг.\n\n"
            "Права есть только у:\n"
            "• Создателей системы\n"
            "• Администраторов ЖК\n"
            "• Супер-администраторов",
            reply_markup=MAIN_KB
        )
        return
    
    # Получаем доступные ЖК в зависимости от уровня доступа
    if access_level in ["CREATOR", "GLOBAL_ADMIN"]:
        # Глобальные админы видят все ЖК
        jk_list = await orm_get_all_jks(session)
        access_info = "🌟 Глобальный доступ - все ЖК"
    else:
        # Администраторы ЖК видят только свои
        jk_list = await orm_get_jks_by_user_admin(session, user_id)
        access_info = "🏢 Доступ к вашим ЖК"
    
    if not jk_list:
        await message.answer(
            "📋 Нет доступных ЖК для управления поставщиками услуг.\n\n"
            "Обратитесь к администратору системы.",
            reply_markup=MAIN_KB
        )
        return
    
    # Сохраняем информацию о доступе
    await state.update_data(
        access_level=access_level,
        available_jks=[jk.id for jk in jk_list]
    )
    
    # Формируем список ЖК
    text = f"🔧 <b>УПРАВЛЕНИЕ ПОСТАВЩИКАМИ УСЛУГ</b>\n\n"
    text += f"{access_info}\n"
    text += f"Доступно ЖК: <b>{len(jk_list)}</b>\n\n"
    text += "Выберите жилой комплекс:"
    
    # Создаем клавиатуру с ЖК
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for jk in jk_list:
        button_text = f"🏢 {jk.name}"
        if hasattr(jk, 'house') and jk.house:
            button_text += f" (дом {jk.house})"
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"select_jk:{jk.id}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main_menu")
    ])
    
    await state.set_state(ManageServiceProviderStates.select_jk)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# Обработка выбора ЖК
@manage_service_providers_router.callback_query(
    F.data.startswith("select_jk:"),
    ManageServiceProviderStates.select_jk
)
async def handle_jk_selection(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Показать поставщиков услуг выбранного ЖК."""
    jk_id = int(callback.data.split(":")[1])
    
    # Проверяем доступ к этому ЖК
    data = await state.get_data()
    available_jks = data.get("available_jks", [])
    
    if jk_id not in available_jks:
        await callback.answer("❌ Нет доступа к этому ЖК", show_alert=True)
        return
    
    # Получаем информацию о ЖК
    jk = await orm_get_jk_by_id(session, jk_id)
    if not jk:
        await callback.answer("❌ ЖК не найден", show_alert=True)
        return
    
    # Получаем поставщиков услуг для этого ЖК
    providers = await orm_get_service_providers_by_jk(session, jk_id, active_only=False)
    
    # Сохраняем выбранный ЖК
    await state.update_data(selected_jk_id=jk_id)
    
    # Формируем текст с информацией
    text = f"🏢 <b>{jk.name}</b>\n"
    text += f"📍 {jk.city}, {jk.street}, {jk.house}\n\n"
    
    if providers:
        text += f"🔧 <b>Поставщики услуг ({len(providers)}):</b>\n\n"
        
        for provider in providers:
            status_icon = "✅" if provider.is_active else "❌"
            category_emoji = provider.category_emoji
            text += f"{status_icon} {category_emoji} <b>{provider.category_display_name}</b>\n"
            
            if provider.organization_name:
                text += f"   📊 {provider.organization_name}\n"
            
            if provider.contact_phone:
                text += f"   📞 {provider.contact_phone}\n"
            
            text += "\n"
    else:
        text += "📝 <b>Поставщики услуг не назначены</b>\n\n"
        text += "Добавьте первого поставщика услуг для автоматизации обработки заявок."
    
    # Переходим к состоянию просмотра поставщиков
    await state.set_state(ManageServiceProviderStates.view_providers)
    
    await callback.message.edit_text(
        text,
        reply_markup=get_providers_keyboard(providers, jk_id),
        parse_mode="HTML"
    )
    await callback.answer()


# Обработка добавления поставщика
@manage_service_providers_router.callback_query(
    F.data.startswith("add_provider:"),
    ManageServiceProviderStates.view_providers
)
async def start_add_provider(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Начать процесс добавления поставщика услуг."""
    jk_id = int(callback.data.split(":")[1])
    
    # Дополнительная проверка прав на этот ЖК
    user_id = callback.from_user.id
    has_access, _ = await check_service_management_access(user_id, session, jk_id)
    
    if not has_access:
        await callback.answer("❌ Нет прав для управления этим ЖК", show_alert=True)
        return
    
    # Получаем занятые категории для этого ЖК
    existing_providers = await orm_get_service_providers_by_jk(session, jk_id, active_only=True)
    occupied_categories = [p.category for p in existing_providers]
    
    if len(occupied_categories) >= len(OfferCategory):
        await callback.answer(
            "ℹ️ Все категории услуг уже назначены. Можете редактировать существующие.",
            show_alert=True
        )
        return
    
    text = "🎯 <b>Выбор категории услуг</b>\n\n"
    
    if occupied_categories:
        text += "❌ <b>Уже назначены:</b>\n"
        for category in occupied_categories:
            text += f"   {OfferCategory.get_emoji(category)} {OfferCategory.get_display_name(category)}\n"
        text += "\n"
    
    text += "➕ <b>Доступные категории:</b>\n"
    text += "Выберите категорию для нового поставщика услуг:"
    
    # Создаем клавиатуру только с доступными категориями
    available_categories = [cat for cat in OfferCategory if cat not in occupied_categories]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for category in available_categories:
        display_name = f"{OfferCategory.get_emoji(category)} {OfferCategory.get_display_name(category)}"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=display_name,
                callback_data=f"select_category:{category.value}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад к списку", callback_data=f"select_jk:{jk_id}")
    ])
    
    await state.set_state(ManageServiceProviderStates.select_category)
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# Обработка выбора категории
@manage_service_providers_router.callback_query(
    F.data.startswith("select_category:"),
    ManageServiceProviderStates.select_category
)
async def handle_category_selection(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка выбора категории услуг."""
    category_value = callback.data.split(":")[1]
    category = OfferCategory(category_value)
    
    # Сохраняем выбранную категорию
    await state.update_data(selected_category=category)
    
    text = f"👤 <b>Назначение ответственного</b>\n\n"
    text += f"Категория: {OfferCategory.get_emoji(category)} <b>{OfferCategory.get_display_name(category)}</b>\n\n"
    text += "📝 Введите Telegram user_id ответственного лица:\n\n"
    text += "💡 <b>Как узнать user_id:</b>\n"
    text += "• Попросите пользователя написать боту @userinfobot\n"
    text += "• Или использовать бот @getmyid_bot\n"
    text += "• ID выглядит как числовой код (например: 123456789)\n\n"
    text += "✏️ Введите user_id:"
    
    # Кнопка отмены
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_add_provider")]
    ])
    
    await state.set_state(ManageServiceProviderStates.input_user_id)
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# Обработка ввода user_id
@manage_service_providers_router.message(
    F.text.regexp(r'^\d+$'),
    ManageServiceProviderStates.input_user_id
)
async def handle_user_id_input(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ввода user_id ответственного."""
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Неверный формат user_id. Введите числовой код:\n"
            "Пример: 123456789"
        )
        return
    
    # Проверяем существование пользователя в базе
    user = await orm_get_user_by_id(session, user_id)
    
    if not user:
        await message.answer(
            f"⚠️ Пользователь с ID {user_id} не найден в системе.\n\n"
            f"Этот пользователь должен:\n"
            f"1. Запустить бота командой /start\n"
            f"2. Пройти регистрацию\n\n"
            f"Попробуйте ввести другой user_id или попросите пользователя зарегистрироваться:"
        )
        return
    
    # Сохраняем user_id ответственного
    await state.update_data(responsible_user_id=user_id)
    
    # Запрашиваем информацию об организации
    text = f"🏢 <b>Информация об организации</b>\n\n"
    text += f"Ответственный: {user.first_name or 'Не указано'}\n"
    text += f"User ID: {user_id}\n\n"
    text += "📝 Введите название организации/компании:\n\n"
    text += "💡 <i>Пример: ТОО 'ЭлектроСервис Алматы'</i>"
    
    # Кнопка отмены
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_add_provider")]
    ])
    
    await state.set_state(ManageServiceProviderStates.input_org_info)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# Обработка ввода информации об организации
@manage_service_providers_router.message(
    F.text,
    ManageServiceProviderStates.input_org_info
)
async def handle_org_info_input(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ввода информации об организации."""
    organization_name = message.text.strip()
    
    if len(organization_name) < 3:
        await message.answer(
            "❌ Название организации слишком короткое.\n"
            "Введите полное название (минимум 3 символа):"
        )
        return
    
    # Сохраняем название организации
    await state.update_data(organization_name=organization_name)
    
    # Запрашиваем контактный телефон
    examples = PhoneValidator.get_examples()
    examples_text = "\n".join([f"• {example}" for example in examples[:3]])
    
    text = f"📞 <b>Контактная информация</b>\n\n"
    text += f"Организация: {organization_name}\n\n"
    text += "Введите контактный телефон:\n\n"
    text += f"📋 <b>Примеры формата:</b>\n{examples_text}\n\n"
    text += "💡 <i>Или введите точку (.) чтобы пропустить</i>"
    
    # Кнопка отмены
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip_phone")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_add_provider")]
    ])
    
    await state.set_state(ManageServiceProviderStates.input_phone)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# Обработка ввода телефона
@manage_service_providers_router.message(
    F.text,
    ManageServiceProviderStates.input_phone
)
async def handle_phone_input(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ввода контактного телефона."""
    phone_text = message.text.strip()
    
    # Если пользователь хочет пропустить
    if phone_text == ".":
        await state.update_data(contact_phone=None)
        await show_provider_confirmation(message, state, session)
        return
    
    # Валидируем номер телефона
    is_valid, formatted_phone, error_message = validate_phone(phone_text)
    
    if not is_valid:
        # Показываем ошибку и примеры
        examples = PhoneValidator.get_examples()
        examples_text = "\n".join([f"• {example}" for example in examples[:3]])
        
        error_text = (
            f"❌ <b>Ошибка:</b> {error_message}\n\n"
            f"📋 <b>Примеры правильного формата:</b>\n{examples_text}\n\n"
            f"Попробуйте еще раз или введите <code>.</code> чтобы пропустить:"
        )
        
        await message.answer(error_text, parse_mode="HTML")
        return
    
    # Сохраняем отформатированный телефон
    await state.update_data(contact_phone=formatted_phone)
    
    # Показываем подтверждение с красиво отформатированным номером
    await message.answer(
        f"✅ <b>Телефон принят:</b> {formatted_phone}",
        parse_mode="HTML"
    )
    
    # Показываем итоговое подтверждение
    await show_provider_confirmation(message, state, session)


# Обработка пропуска телефона
@manage_service_providers_router.callback_query(
    F.data == "skip_phone",
    ManageServiceProviderStates.input_phone
)
async def handle_skip_phone(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Пропуск ввода телефона."""
    await state.update_data(contact_phone=None)
    await show_provider_confirmation(callback.message, state, session)
    await callback.answer()


async def show_provider_confirmation(message: Message, state: FSMContext, session: AsyncSession):
    """Показать подтверждение создания поставщика услуг."""
    data = await state.get_data()
    
    # Получаем информацию о ЖК
    jk = await orm_get_jk_by_id(session, data["selected_jk_id"])
    
    # Получаем информацию о пользователе
    user = await orm_get_user_by_id(session, data["responsible_user_id"])
    
    category = data["selected_category"]
    
    text = f"✅ <b>Подтверждение создания поставщика услуг</b>\n\n"
    text += f"🏢 <b>ЖК:</b> {jk.name}\n"
    text += f"📍 {jk.city}, {jk.street}, {jk.house}\n\n"
    text += f"🎯 <b>Категория:</b> {OfferCategory.get_emoji(category)} {OfferCategory.get_display_name(category)}\n\n"
    text += f"👤 <b>Ответственный:</b> {user.first_name or 'Не указано'}\n"
    text += f"🆔 <b>User ID:</b> {data['responsible_user_id']}\n\n"
    text += f"🏢 <b>Организация:</b> {data['organization_name']}\n"
    
    if data.get('contact_phone'):
        text += f"📞 <b>Телефон:</b> {data['contact_phone']}\n"
    
    text += f"\n⚙️ <b>Настройки по умолчанию:</b>\n"
    text += f"• Автоназначение заявок: ✅ Включено\n"
    text += f"• Уведомления: ✅ Включены\n"
    text += f"• Приоритет: 1 (высший)\n"
    text += f"• Рабочие дни: Пн-Пт\n"
    text += f"• Рабочее время: 09:00-18:00\n\n"
    text += f"Создать поставщика услуг?"
    
    # Кнопки подтверждения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Создать", callback_data="confirm_create_provider"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_add_provider")
        ]
    ])
    
    await state.set_state(ManageServiceProviderStates.confirm_provider)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# Подтверждение создания поставщика
@manage_service_providers_router.callback_query(
    F.data == "confirm_create_provider",
    ManageServiceProviderStates.confirm_provider
)
async def confirm_create_provider(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Создать поставщика услуг."""
    data = await state.get_data()
    
    # Подготавливаем данные для создания
    service_data = {
        "jk_id": data["selected_jk_id"],
        "category": data["selected_category"],
        "responsible_user_id": data["responsible_user_id"],
        "organization_name": data["organization_name"],
        "contact_phone": data.get("contact_phone"),
        "is_active": True,
        "receives_notifications": True,
        "auto_assign_offers": True,
        "priority": 1,
        "work_hours_start": "09:00",
        "work_hours_end": "18:00",
        "work_days": 31,  # Пн-Пт (1+2+4+8+16)
        "created_by_user_id": callback.from_user.id
    }
    
    try:
        # Создаем поставщика услуг
        provider = await orm_add_service_provider(session, service_data)
        
        text = f"🎉 <b>Поставщик услуг успешно создан!</b>\n\n"
        text += f"🆔 ID: {provider.id}\n"
        text += f"🎯 Категория: {provider.category_emoji} {provider.category_display_name}\n"
        text += f"🏢 Организация: {provider.organization_name}\n\n"
        text += f"✅ Теперь заявки категории '{provider.category_display_name}' будут автоматически назначаться на этого поставщика услуг."
        
        # Возвращаемся к просмотру ЖК
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Обратно к ЖК", callback_data=f"select_jk:{data['selected_jk_id']}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main_menu")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при создании поставщика услуг:\n{str(e)}\n\n"
            f"Попробуйте позже или обратитесь к администратору."
        )
    
    await state.clear()
    await callback.answer("Поставщик услуг создан!")


# Отмена добавления поставщика
@manage_service_providers_router.callback_query(
    F.data == "cancel_add_provider"
)
async def cancel_add_provider(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Отменить добавление поставщика услуг."""
    data = await state.get_data()
    jk_id = data.get("selected_jk_id")
    
    if jk_id:
        # Очищаем состояние, но сохраняем ключевые данные для возврата к ЖК
        await state.clear()
        await state.update_data(
            access_level=data.get("access_level"),
            available_jks=data.get("available_jks", []),
            selected_jk_id=jk_id
        )
        
        # Возвращаемся к просмотру ЖК
        await state.set_state(ManageServiceProviderStates.select_jk)
        
        # Эмулируем выбор ЖК для возврата к его просмотру
        callback.data = f"select_jk:{jk_id}"
        await handle_jk_selection(callback, state, session)
        return
    else:
        await callback.message.edit_text("❌ Операция отменена.")
        await state.clear()
    
    await callback.answer("Отменено")


# Возврат к выбору ЖК
@manage_service_providers_router.callback_query(F.data == "back_to_jk_selection")
async def back_to_jk_selection(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Вернуться к выбору ЖК."""
    await state.set_state(ManageServiceProviderStates.select_jk)
    await callback.answer("Возврат к выбору ЖК")
    
    # Перезапускаем команду manage_services
    await cmd_manage_services(callback.message, state, session)


# Переход в главное меню
@manage_service_providers_router.callback_query(F.data == "to_main_menu")
async def to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Перейти в главное меню."""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=MAIN_KB
    )
    await callback.answer()


# Обработка некорректного ввода user_id
@manage_service_providers_router.message(ManageServiceProviderStates.input_user_id)
async def invalid_user_id_input(message: Message):
    """Обработка некорректного ввода user_id."""
    await message.answer(
        "❌ Неверный формат user_id.\n\n"
        "User ID должен состоять только из цифр.\n"
        "Пример: 123456789\n\n"
        "Попробуйте еще раз:"
    )
