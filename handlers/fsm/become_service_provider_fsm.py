# -*- coding: utf-8 -*-
# handlers/fsm/become_service_provider_fsm.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.orm_user import orm_get_user_by_id
from database.models.orm_jk import orm_get_all_jks
from database.models.orm_jk_service_provider import orm_create_service_provider_request, orm_get_user_service_provider_requests
from database.models.model_jk import JK
from database.enums.offer_category_enum import OfferCategory
from keyboards.reply import MAIN_KB

become_service_provider_router = Router()


class BecomeServiceProviderStates(StatesGroup):
    select_jk = State()          # Выбор ЖК
    select_category = State()    # Выбор категории услуг
    input_organization = State() # Ввод названия организации
    input_phone = State()        # Ввод телефона
    input_email = State()        # Ввод email (опционально)
    input_description = State()  # Ввод описания услуг
    confirm_request = State()    # Подтверждение заявки


@become_service_provider_router.callback_query(F.data == "become_service_provider")
async def start_become_service_provider(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Начать процесс подачи заявки на статус поставщика услуг"""
    user_id = callback.from_user.id
    
    # Проверяем, нет ли уже активных заявок от этого пользователя
    existing_requests = await orm_get_user_service_provider_requests(session, user_id)
    
    if existing_requests:
        pending_count = len([r for r in existing_requests if not r.is_active])
        if pending_count > 0:
            await callback.message.edit_text(
                f"⏳ <b>У вас уже есть заявка на рассмотрении</b>\n\n"
                f"Заявок в ожидании: {pending_count}\n\n"
                f"Дождитесь решения администратора или обратитесь к нему напрямую.",
                parse_mode="HTML"
            )
            return
    
    # Получаем доступные ЖК
    jks = await orm_get_all_jks(session)
    
    if not jks:
        await callback.message.edit_text(
            "❌ В системе пока нет доступных ЖК.\n"
            "Обратитесь к администратору."
        )
        return
    
    # Создаем клавиатуру с ЖК
    keyboard_buttons = []
    for jk in jks:
        address = f"{jk.city}, {jk.street}, {jk.house}"
        if jk.block:
            address += f", {jk.block}"
        
        button_text = f"🏠 {jk.name}\n📍 {address}"
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"select_jk:{jk.id}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_request")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        "🏢 <b>Выбор ЖК для предоставления услуг</b>\n\n"
        "Выберите жилой комплекс, в котором вы хотите предоставлять услуги:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    await state.set_state(BecomeServiceProviderStates.select_jk)
    await callback.answer()


@become_service_provider_router.callback_query(F.data.startswith("select_jk:"))
async def process_jk_selection(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка выбора ЖК"""
    jk_id = int(callback.data.split(":")[1])
    
    # Сохраняем ID ЖК в состоянии
    await state.update_data(jk_id=jk_id)
    
    # Получаем информацию о ЖК для отображения
    jk = await session.get(JK, jk_id)
    
    # Создаем клавиатуру с категориями услуг
    keyboard_buttons = []
    for category in OfferCategory:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{category.emoji} {category.display_name}",
                callback_data=f"select_category:{category.value}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="become_service_provider"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_request")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        f"🔧 <b>Выбор категории услуг</b>\n\n"
        f"ЖК: <b>{jk.name}</b>\n"
        f"Адрес: {jk.city}, {jk.street}, {jk.house}\n\n"
        f"Выберите категорию услуг, которые вы предоставляете:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    await state.set_state(BecomeServiceProviderStates.select_category)
    await callback.answer()


@become_service_provider_router.callback_query(F.data.startswith("select_category:"))
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории"""
    category_value = callback.data.split(":")[1]
    category = OfferCategory.from_string(category_value)
    
    # Сохраняем категорию в состоянии
    await state.update_data(category=category_value)
    
    await callback.message.edit_text(
        f"🏢 <b>Введите название организации</b>\n\n"
        f"Услуга: {category.emoji} {category.display_name}\n\n"
        f"Введите полное название вашей организации или ИП:\n"
        f"<i>Например: ООО \"Сервис Плюс\" или ИП Иванов И.И.</i>",
        parse_mode="HTML"
    )
    
    await state.set_state(BecomeServiceProviderStates.input_organization)
    await callback.answer()


@become_service_provider_router.message(BecomeServiceProviderStates.input_organization)
async def process_organization_input(message: Message, state: FSMContext):
    """Обработка ввода названия организации"""
    organization_name = message.text.strip()
    
    if len(organization_name) < 3:
        await message.answer(
            "❌ Название организации слишком короткое.\n"
            "Введите корректное название (минимум 3 символа):"
        )
        return
    
    if len(organization_name) > 200:
        await message.answer(
            "❌ Название организации слишком длинное.\n"
            "Максимум 200 символов. Введите более короткое название:"
        )
        return
    
    # Сохраняем название организации
    await state.update_data(organization_name=organization_name)
    
    await message.answer(
        f"📞 <b>Введите контактный телефон</b>\n\n"
        f"Организация: <b>{organization_name}</b>\n\n"
        f"Введите ваш контактный телефон:\n"
        f"<i>Например: +7 (999) 123-45-67</i>",
        parse_mode="HTML"
    )
    
    await state.set_state(BecomeServiceProviderStates.input_phone)


@become_service_provider_router.message(BecomeServiceProviderStates.input_phone)
async def process_phone_input(message: Message, state: FSMContext):
    """Обработка ввода телефона"""
    phone = message.text.strip()
    
    # Простая валидация телефона
    import re
    phone_pattern = r'^[\+]?[1-9][\d\s\-\(\)]{8,15}$'
    
    if not re.match(phone_pattern, phone):
        await message.answer(
            "❌ Некорректный формат телефона.\n"
            "Введите телефон в формате: +7 (999) 123-45-67"
        )
        return
    
    # Сохраняем телефон
    await state.update_data(contact_phone=phone)
    
    await message.answer(
        f"📧 <b>Введите email (необязательно)</b>\n\n"
        f"Телефон: <b>{phone}</b>\n\n"
        f"Введите ваш email для связи или отправьте /skip для пропуска:\n"
        f"<i>Например: service@company.ru</i>",
        parse_mode="HTML"
    )
    
    await state.set_state(BecomeServiceProviderStates.input_email)


@become_service_provider_router.message(BecomeServiceProviderStates.input_email)
async def process_email_input(message: Message, state: FSMContext):
    """Обработка ввода email"""
    email = message.text.strip()
    
    if email.lower() == '/skip':
        email = None
    else:
        # Простая валидация email
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            await message.answer(
                "❌ Некорректный формат email.\n"
                "Введите корректный email или /skip для пропуска:"
            )
            return
    
    # Сохраняем email
    await state.update_data(contact_email=email)
    
    await message.answer(
        f"📝 <b>Описание услуг (необязательно)</b>\n\n"
        f"Опишите подробнее какие услуги вы предоставляете, ваш опыт работы, "
        f"особенности или отправьте /skip для пропуска:\n\n"
        f"<i>Например: Аварийный ремонт сантехники 24/7, опыт работы 10 лет, "
        f"собственный инструмент и запчасти.</i>",
        parse_mode="HTML"
    )
    
    await state.set_state(BecomeServiceProviderStates.input_description)


@become_service_provider_router.message(BecomeServiceProviderStates.input_description)
async def process_description_input(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ввода описания и показ итогового подтверждения"""
    description = message.text.strip()
    
    if description.lower() == '/skip':
        description = None
    elif len(description) > 500:
        await message.answer(
            "❌ Описание слишком длинное.\n"
            "Максимум 500 символов. Сократите описание:"
        )
        return
    
    # Сохраняем описание
    await state.update_data(description=description)
    
    # Получаем все данные из состояния
    data = await state.get_data()
    
    # Получаем информацию о ЖК для отображения
    jk = await session.get(JK, data['jk_id'])
    category = OfferCategory.from_string(data['category'])
    
    # Формируем сообщение для подтверждения
    confirmation_text = (
        f"✅ <b>Подтверждение заявки</b>\n\n"
        f"🏢 <b>ЖК:</b> {jk.name}\n"
        f"📍 <b>Адрес:</b> {jk.city}, {jk.street}, {jk.house}\n"
        f"🔧 <b>Услуга:</b> {category.emoji} {category.display_name}\n\n"
        f"🏛️ <b>Организация:</b> {data['organization_name']}\n"
        f"📞 <b>Телефон:</b> {data['contact_phone']}\n"
    )
    
    if data.get('contact_email'):
        confirmation_text += f"📧 <b>Email:</b> {data['contact_email']}\n"
    
    if data.get('description'):
        confirmation_text += f"\n📝 <b>Описание:</b>\n{data['description']}\n"
    
    confirmation_text += (
        f"\n━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ <b>Статус:</b> Ожидает проверки администратора\n\n"
        f"Подтвердите отправку заявки:"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить заявку", callback_data="confirm_service_request"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_request")
            ]
        ]
    )
    
    await message.answer(
        confirmation_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    await state.set_state(BecomeServiceProviderStates.confirm_request)


@become_service_provider_router.callback_query(F.data == "confirm_service_request")
async def confirm_service_request(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Подтверждение и создание заявки"""
    user_id = callback.from_user.id
    data = await state.get_data()
    
    try:
        # Создаем запись в БД с is_active = False
        service_provider_id = await orm_create_service_provider_request(
            session=session,
            jk_id=data['jk_id'],
            category=data['category'],
            responsible_user_id=user_id,
            organization_name=data['organization_name'],
            contact_phone=data['contact_phone'],
            contact_email=data.get('contact_email'),
            description=data.get('description'),
            is_active=False  # Ожидает активации
        )
        
        await session.commit()
        
        await callback.message.edit_text(
            f"🎉 <b>Заявка успешно отправлена!</b>\n\n"
            f"📋 <b>Номер заявки:</b> #{service_provider_id}\n\n"
            f"⏳ Ваша заявка передана администратору на рассмотрение.\n"
            f"Вы получите уведомление о принятом решении.\n\n"
            f"💬 Вопросы можете задать администратору ЖК.",
            parse_mode="HTML"
        )
        
        # Отправляем уведомление администраторам (если настроено)
        # await notify_admins_about_new_service_request(session, service_provider_id)
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ <b>Ошибка при создании заявки</b>\n\n"
            f"Произошла техническая ошибка. Попробуйте позже или обратитесь к администратору.\n\n"
            f"Код ошибки: {str(e)[:50]}...",
            parse_mode="HTML"
        )
    
    await state.clear()
    await callback.answer()


@become_service_provider_router.callback_query(F.data == "cancel_request")
async def cancel_request(callback: CallbackQuery, state: FSMContext):
    """Отмена подачи заявки"""
    await callback.message.edit_text(
        "❌ <b>Заявка отменена</b>\n\n"
        "Вы можете подать заявку на статус поставщика услуг позже, "
        "используя команду /is_service",
        parse_mode="HTML"
    )
    
    await state.clear()
    await callback.answer()
