# -*- coding: utf-8 -*-
# handlers/control_service_provider_kb.py
"""
Обработчики для клавиатуры управления поставщиками услуг.
"""

from aiogram.types import Message
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.orm_jk import orm_get_all_jks, orm_get_jk_by_id
from database.models.orm_user import orm_get_user_by_id
from database.models.orm_user_jk import orm_get_jks_by_user_admin
from database.models.orm_jk_service_provider import orm_get_service_providers_by_jk
from database.enums.user_enums import UserRole
from database.enums.offer_category_enum import OfferCategory
from keyboards.reply import MAIN_KB, CONTROL_SERVICE_PROVIDER_KB
from keyboards.service_provider_keyboards import (
    get_category_keyboard,
    get_simple_jk_selection_keyboard
)

from handlers.fsm.manage_service_providers_fsm import is_creator_by_environment
from handlers.fsm.manage_service_providers_fsm import ManageServiceProviderStates

# Создаем роутер для обработчиков клавиатуры
control_service_provider_router = Router()


@control_service_provider_router.message(F.text == "Список поставщиков услуг")
async def show_service_providers_list(message: Message, state: FSMContext, session: AsyncSession):
    """Показать список поставщиков услуг."""
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
    
    # Проверяем права доступа
    is_creator_by_env = is_creator_by_environment(user_id)
    
    if is_creator_by_env or user.role in [UserRole.ADMIN, UserRole.CREATOR]:
        available_jks = await orm_get_all_jks(session)
    else:
        available_jks = await orm_get_jks_by_user_admin(session, user_id)
    
    if not available_jks:
        await message.answer(
            "❌ Нет доступных ЖК для просмотра поставщиков услуг.",
            reply_markup=CONTROL_SERVICE_PROVIDER_KB
        )
        return
    
    # Формируем список поставщиков по всем ЖК
    providers_text = "📋 <b>Список поставщиков услуг:</b>\n\n"
    total_providers = 0
    
    for jk in available_jks:
        providers = await orm_get_service_providers_by_jk(session, jk.id, active_only=True)
        if providers:
            providers_text += f"🏢 <b>{jk.name}</b>\n"
            for provider in providers:
                # Безопасная обработка категории
                if isinstance(provider.category, OfferCategory):
                    category = provider.category
                elif isinstance(provider.category, str):
                    category = OfferCategory.from_string(provider.category)
                else:
                    # Пропускаем если неизвестный тип
                    continue
                    
                providers_text += f"  {category.emoji} {category.display_name}: {provider.organization_name}\n"
                total_providers += 1
            providers_text += "\n"
    
    if total_providers == 0:
        providers_text += "❌ Поставщики услуг не найдены."
    else:
        providers_text += f"📊 <b>Всего поставщиков:</b> {total_providers}"
    
    await message.answer(providers_text, parse_mode="HTML", reply_markup=CONTROL_SERVICE_PROVIDER_KB)


@control_service_provider_router.message(F.text == "Добавить поставщика услуг")
async def add_service_provider(message: Message, state: FSMContext, session: AsyncSession):
    """Начать процесс добавления поставщика услуг."""
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
    
    # Проверяем права доступа
    is_creator_by_env = is_creator_by_environment(user_id)
    
    if is_creator_by_env or user.role in [UserRole.ADMIN, UserRole.CREATOR]:
        available_jks = await orm_get_all_jks(session)
    else:
        available_jks = await orm_get_jks_by_user_admin(session, user_id)
    
    if not available_jks:
        await message.answer(
            "❌ Нет доступных ЖК для добавления поставщиков услуг.",
            reply_markup=CONTROL_SERVICE_PROVIDER_KB
        )
        return
    
    if len(available_jks) == 1:
        # Если ЖК только один, сразу переходим к выбору категории
        jk = available_jks[0]
        await state.update_data(selected_jk_id=jk.id)
        await state.set_state(ManageServiceProviderStates.select_category)
        
        await message.answer(
            f"🏢 <b>ЖК: {jk.name}</b>\n\n"
            "🔧 <b>Добавление поставщика услуг</b>\n\n"
            "Выберите категорию услуг:",
            parse_mode="HTML",
            reply_markup=get_category_keyboard()
        )
    else:
        # Если ЖК несколько, показываем список для выбора
        await state.set_state(ManageServiceProviderStates.select_jk_for_add)
        await message.answer(
            "🏢 <b>Выберите ЖК для добавления поставщика услуг:</b>",
            parse_mode="HTML",
            reply_markup=get_simple_jk_selection_keyboard(available_jks)
        )


@control_service_provider_router.message(F.text == "Управление ЖК", default_state)
async def control_jk(message: Message, state: FSMContext, session: AsyncSession):
    """Управление ЖК - переход к меню /add_jk."""
    await state.clear()
    user_id = message.from_user.id
    
    # Проверяем права доступа - только создатели и админы могут управлять ЖК
    user = await orm_get_user_by_id(session, user_id)
    is_creator_by_env = is_creator_by_environment(user_id)
    
    if not (is_creator_by_env or (user and user.role in [UserRole.ADMIN, UserRole.CREATOR])):
        await message.answer(
            "❌ У вас нет прав для управления ЖК.",
            reply_markup=CONTROL_SERVICE_PROVIDER_KB
        )
        return
    
    # ✅ Запускаем FSM для управления ЖК (то же самое что команда /add_jk)
    from handlers.fsm.add_jk_fsm import JKCreationState, ADD_JK_MAIN
    
    await state.set_state(JKCreationState.menu)
    await message.answer(
        "🏢 <b>Управление ЖК</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=ADD_JK_MAIN
    )


@control_service_provider_router.message(F.text == "Главное меню")
async def go_to_main_menu(message: Message, state: FSMContext):
    """Возврат в главное меню."""
    await state.clear()
    await message.answer(
        "🏠 <b>Главное меню</b>",
        parse_mode="HTML",
        reply_markup=MAIN_KB
    )
