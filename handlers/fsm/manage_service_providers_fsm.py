# -*- coding: utf-8 -*-
# handlers/fsm/manage_service_providers_fsm.py
"""
FSM РґР»СЏ СѓРїСЂР°РІР»РµРЅРёСЏ РїРѕСЃС‚Р°РІС‰РёРєР°РјРё СѓСЃР»СѓРі РІ Р–Рљ.
РўРѕР»СЊРєРѕ Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂС‹ РјРѕРіСѓС‚ РїСЂРёРІСЏР·С‹РІР°С‚СЊ РѕСЂРіР°РЅРёР·Р°С†РёРё Рє Р–Рљ.
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
    """РЎРѕСЃС‚РѕСЏРЅРёСЏ РґР»СЏ СѓРїСЂР°РІР»РµРЅРёСЏ РїРѕСЃС‚Р°РІС‰РёРєР°РјРё СѓСЃР»СѓРі."""
    select_jk = State()          # Р’С‹Р±РѕСЂ Р–Рљ
    view_providers = State()     # РџСЂРѕСЃРјРѕС‚СЂ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ Р–Рљ
    add_provider = State()       # Р”РѕР±Р°РІР»РµРЅРёРµ РїРѕСЃС‚Р°РІС‰РёРєР°
    select_category = State()    # Р’С‹Р±РѕСЂ РєР°С‚РµРіРѕСЂРёРё СѓСЃР»СѓРі
    input_user_id = State()      # Р’РІРѕРґ user_id РѕС‚РІРµС‚СЃС‚РІРµРЅРЅРѕРіРѕ
    input_org_info = State()     # Р’РІРѕРґ РёРЅС„РѕСЂРјР°С†РёРё РѕР± РѕСЂРіР°РЅРёР·Р°С†РёРё
    input_phone = State()        # Р’РІРѕРґ РєРѕРЅС‚Р°РєС‚РЅРѕРіРѕ С‚РµР»РµС„РѕРЅР°
    input_work_schedule = State() # Р’РІРѕРґ СЂР°Р±РѕС‡РµРіРѕ РІСЂРµРјРµРЅРё
    confirm_provider = State()   # РџРѕРґС‚РІРµСЂР¶РґРµРЅРёРµ СЃРѕР·РґР°РЅРёСЏ


@manage_service_providers_router.message(Command("manage_services"))
async def cmd_manage_services(message: Message, state: FSMContext, session: AsyncSession):
    """РљРѕРјР°РЅРґР° РґР»СЏ СѓРїСЂР°РІР»РµРЅРёСЏ РїРѕСЃС‚Р°РІС‰РёРєР°РјРё СѓСЃР»СѓРі."""
    await state.clear()
    user_id = message.from_user.id
    
    # РџСЂРѕРІРµСЂСЏРµРј РїСЂР°РІР° РґРѕСЃС‚СѓРїР°
    has_access, error_msg = await check_service_management_access(user_id, session)
    if not has_access:
        await message.answer(error_msg, reply_markup=get_keyboard(MAIN_KB))
        return
    
    # РџРѕР»СѓС‡Р°РµРј РґРѕСЃС‚СѓРїРЅС‹Рµ Р–Рљ РґР»СЏ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ
    user = await orm_get_user_by_id(session, user_id)
    
    if user.role == UserRole.ADMIN:
        # РЎСѓРїРµСЂР°РґРјРёРЅ РІРёРґРёС‚ РІСЃРµ Р–Рљ
        available_jks = await orm_get_all_jks(session)
    else:
        # РђРґРјРёРЅ Р–Рљ РІРёРґРёС‚ С‚РѕР»СЊРєРѕ СЃРІРѕРё Р–Рљ
        available_jks = await orm_get_jks_by_user_admin(session, user_id)
    
    if not available_jks:
        await message.answer(
            "вќЊ РќРµС‚ РґРѕСЃС‚СѓРїРЅС‹С… Р–Рљ РґР»СЏ СѓРїСЂР°РІР»РµРЅРёСЏ РїРѕСЃС‚Р°РІС‰РёРєР°РјРё СѓСЃР»СѓРі.",
            reply_markup=get_keyboard(MAIN_KB)
        )
        return
    
    if len(available_jks) == 1:
        # Р•СЃР»Рё Р–Рљ С‚РѕР»СЊРєРѕ РѕРґРёРЅ, СЃСЂР°Р·Сѓ РїРµСЂРµС…РѕРґРёРј Рє РїСЂРѕСЃРјРѕС‚СЂСѓ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ
        jk = available_jks[0]
        await state.update_data(selected_jk_id=jk.id)
        await state.set_state(ManageServiceProviderStates.view_providers)
        
        providers = await orm_get_service_providers_by_jk(session, jk.id)
        
        providers_text = f"рџЏў <b>Р–Рљ: {jk.name}</b>\n\n"
        if providers:
            providers_text += "рџ“‹ <b>РџРѕСЃС‚Р°РІС‰РёРєРё СѓСЃР»СѓРі:</b>\n\n"
            for i, provider in enumerate(providers, 1):
                category_emoji = OfferCategory.get_emoji_by_value(provider.category)
                status = "вњ… РђРєС‚РёРІРµРЅ" if provider.is_active else "вќЊ РќРµР°РєС‚РёРІРµРЅ"
                notifications = "рџ”” Р’РєР»" if provider.receives_notifications else "рџ”• Р’С‹РєР»"
                
                providers_text += (
                    f"{i}. {category_emoji} <b>{provider.organization_name}</b>\n"
                    f"   РЎС‚Р°С‚СѓСЃ: {status} | РЈРІРµРґРѕРјР»РµРЅРёСЏ: {notifications}\n\n"
                )
        else:
            providers_text += "вќЊ РџРѕСЃС‚Р°РІС‰РёРєРё СѓСЃР»СѓРі РЅРµ РґРѕР±Р°РІР»РµРЅС‹."
        
        await message.answer(
            providers_text,
            parse_mode="HTML",
            reply_markup=get_providers_keyboard(providers, jk.id)
        )
    else:
        # Р•СЃР»Рё Р–Рљ РЅРµСЃРєРѕР»СЊРєРѕ, РїРѕРєР°Р·С‹РІР°РµРј СЃРїРёСЃРѕРє РґР»СЏ РІС‹Р±РѕСЂР°
        await state.set_state(ManageServiceProviderStates.select_jk)
        await message.answer(
            "рџЏў <b>Р’С‹Р±РµСЂРёС‚Рµ Р–Рљ РґР»СЏ СѓРїСЂР°РІР»РµРЅРёСЏ РїРѕСЃС‚Р°РІС‰РёРєР°РјРё СѓСЃР»СѓРі:</b>",
            parse_mode="HTML",
            reply_markup=get_jk_selection_keyboard(available_jks)
        )


@manage_service_providers_router.callback_query(F.data.startswith("select_jk:"))
async def handle_jk_selection(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """РћР±СЂР°Р±РѕС‚РєР° РІС‹Р±РѕСЂР° Р–Рљ."""
    jk_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    # РџСЂРѕРІРµСЂСЏРµРј РїСЂР°РІР° РґРѕСЃС‚СѓРїР° Рє РІС‹Р±СЂР°РЅРЅРѕРјСѓ Р–Рљ
    has_access, error_msg = await check_service_management_access(user_id, session, jk_id)
    if not has_access:
        await callback.answer(error_msg, show_alert=True)
        return
    
    await state.update_data(selected_jk_id=jk_id)
    await state.set_state(ManageServiceProviderStates.view_providers)
    
    # РџРѕР»СѓС‡Р°РµРј РёРЅС„РѕСЂРјР°С†РёСЋ Рѕ Р–Рљ Рё РїРѕСЃС‚Р°РІС‰РёРєР°С…
    jk = await orm_get_jk_by_id(session, jk_id)
    providers = await orm_get_service_providers_by_jk(session, jk_id)
    
    providers_text = f"рџЏў <b>Р–Рљ: {jk.name}</b>\n\n"
    if providers:
        providers_text += "рџ“‹ <b>РџРѕСЃС‚Р°РІС‰РёРєРё СѓСЃР»СѓРі:</b>\n\n"
        for i, provider in enumerate(providers, 1):
            category_emoji = OfferCategory.get_emoji_by_value(provider.category)
            status = "вњ… РђРєС‚РёРІРµРЅ" if provider.is_active else "вќЊ РќРµР°РєС‚РёРІРµРЅ"
            notifications = "рџ”” Р’РєР»" if provider.receives_notifications else "рџ”• Р’С‹РєР»"
            
            providers_text += (
                f"{i}. {category_emoji} <b>{provider.organization_name}</b>\n"
                f"   РЎС‚Р°С‚СѓСЃ: {status} | РЈРІРµРґРѕРјР»РµРЅРёСЏ: {notifications}\n\n"
            )
    else:
        providers_text += "вќЊ РџРѕСЃС‚Р°РІС‰РёРєРё СѓСЃР»СѓРі РЅРµ РґРѕР±Р°РІР»РµРЅС‹."
    
    await callback.message.edit_text(
        providers_text,
        parse_mode="HTML",
        reply_markup=get_providers_keyboard(providers, jk_id)
    )
    await callback.answer()


@manage_service_providers_router.callback_query(F.data.startswith("add_provider:"))
async def start_add_provider(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """РќР°С‡Р°Р»Рѕ РїСЂРѕС†РµСЃСЃР° РґРѕР±Р°РІР»РµРЅРёСЏ РїРѕСЃС‚Р°РІС‰РёРєР° СѓСЃР»СѓРі."""
    jk_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    # РџСЂРѕРІРµСЂСЏРµРј РїСЂР°РІР° РґРѕСЃС‚СѓРїР°
    has_access, error_msg = await check_service_management_access(user_id, session, jk_id)
    if not has_access:
        await callback.answer(error_msg, show_alert=True)
        return
    
    await state.update_data(selected_jk_id=jk_id)
    await state.set_state(ManageServiceProviderStates.select_category)
    
    jk = await orm_get_jk_by_id(session, jk_id)
    
    await callback.message.edit_text(
        f"рџЏў <b>Р–Рљ: {jk.name}</b>\n\n"
        "рџ“ќ <b>Р”РѕР±Р°РІР»РµРЅРёРµ РїРѕСЃС‚Р°РІС‰РёРєР° СѓСЃР»СѓРі</b>\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РєР°С‚РµРіРѕСЂРёСЋ СѓСЃР»СѓРі:",
        parse_mode="HTML",
        reply_markup=get_category_keyboard()
    )
    await callback.answer()


@manage_service_providers_router.callback_query(F.data.startswith("select_category:"))
async def handle_category_selection(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """РћР±СЂР°Р±РѕС‚РєР° РІС‹Р±РѕСЂР° РєР°С‚РµРіРѕСЂРёРё СѓСЃР»СѓРі."""
    category_value = callback.data.split(":")[1]
    
    try:
        category = OfferCategory(category_value)
    except ValueError:
        await callback.answer("вќЊ РќРµРёР·РІРµСЃС‚РЅР°СЏ РєР°С‚РµРіРѕСЂРёСЏ", show_alert=True)
        return
    
    # РџСЂРѕРІРµСЂСЏРµРј, РЅРµС‚ Р»Рё СѓР¶Рµ РїРѕСЃС‚Р°РІС‰РёРєР° РґР»СЏ СЌС‚РѕР№ РєР°С‚РµРіРѕСЂРёРё РІ Р–Рљ
    data = await state.get_data()
    jk_id = data.get("selected_jk_id")
    
    existing_provider = await orm_get_service_provider_by_category(session, jk_id, category)
    if existing_provider:
        await callback.answer(
            f"вќЊ РџРѕСЃС‚Р°РІС‰РёРє РґР»СЏ РєР°С‚РµРіРѕСЂРёРё '{category.get_display_name()}' СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚",
            show_alert=True
        )
        return
    
    await state.update_data(category=category_value)
    await state.set_state(ManageServiceProviderStates.input_user_id)
    
    await callback.message.edit_text(
        f"вњ… Р’С‹Р±СЂР°РЅР° РєР°С‚РµРіРѕСЂРёСЏ: <b>{category.get_display_name()}</b> {category.get_emoji()}\n\n"
        "рџ‘¤ <b>Р’РІРµРґРёС‚Рµ User ID РѕС‚РІРµС‚СЃС‚РІРµРЅРЅРѕРіРѕ Р»РёС†Р°</b>\n\n"
        "Р­С‚Рѕ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ РїРѕР»СЊР·РѕРІР°С‚РµР»СЊ, Р·Р°СЂРµРіРёСЃС‚СЂРёСЂРѕРІР°РЅРЅС‹Р№ РІ Р±РѕС‚Рµ, РєРѕС‚РѕСЂС‹Р№ Р±СѓРґРµС‚ РїРѕР»СѓС‡Р°С‚СЊ СѓРІРµРґРѕРјР»РµРЅРёСЏ Рѕ РЅРѕРІС‹С… Р·Р°СЏРІРєР°С….\n\n"
        "рџ’Ў <i>User ID РјРѕР¶РЅРѕ СѓР·РЅР°С‚СЊ РІ РїСЂРѕС„РёР»Рµ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РёР»Рё РїРѕРїСЂРѕСЃРёС‚СЊ РµРіРѕ РѕС‚РїСЂР°РІРёС‚СЊ РєРѕРјР°РЅРґСѓ /my_id</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@manage_service_providers_router.message(ManageServiceProviderStates.input_user_id)
async def handle_user_id_input(message: Message, state: FSMContext, session: AsyncSession):
    """РћР±СЂР°Р±РѕС‚РєР° РІРІРѕРґР° User ID РѕС‚РІРµС‚СЃС‚РІРµРЅРЅРѕРіРѕ Р»РёС†Р°."""
    try:
        responsible_user_id = int(message.text.strip())
    except ValueError:
        await message.answer("вќЊ User ID РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ С‡РёСЃР»РѕРј. РџРѕРїСЂРѕР±СѓР№С‚Рµ РµС‰Рµ СЂР°Р·:")
        return
    
    # Р’Р°Р»РёРґРёСЂСѓРµРј РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ
    is_valid, error_msg, user_info = await validate_responsible_user(responsible_user_id, session)
    if not is_valid:
        await message.answer(f"{error_msg}\n\nРџРѕРїСЂРѕР±СѓР№С‚Рµ РµС‰Рµ СЂР°Р·:")
        return
    
    await state.update_data(responsible_user_id=responsible_user_id, user_info=user_info)
    await state.set_state(ManageServiceProviderStates.input_org_info)
    
    user_name = user_info['first_name'] or 'РќРµРёР·РІРµСЃС‚РЅРѕ'
    if user_info['last_name']:
        user_name += f" {user_info['last_name']}"
    if user_info['username']:
        user_name += f" (@{user_info['username']})"
    
    await message.answer(
        f"вњ… <b>РћС‚РІРµС‚СЃС‚РІРµРЅРЅРѕРµ Р»РёС†Рѕ:</b> {user_name}\n\n"
        "рџЏў <b>Р’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ РѕСЂРіР°РЅРёР·Р°С†РёРё:</b>\n"
        "РќР°РїСЂРёРјРµСЂ: РћРћРћ 'Р”РѕРјРѕС„РѕРЅ-РЎРµСЂРІРёСЃ'",
        parse_mode="HTML"
    )


@manage_service_providers_router.message(ManageServiceProviderStates.input_org_info)
async def handle_org_info_input(message: Message, state: FSMContext, session: AsyncSession):
    """РћР±СЂР°Р±РѕС‚РєР° РІРІРѕРґР° РёРЅС„РѕСЂРјР°С†РёРё РѕР± РѕСЂРіР°РЅРёР·Р°С†РёРё."""
    organization_name = message.text.strip()
    
    # Р’Р°Р»РёРґРёСЂСѓРµРј РЅР°Р·РІР°РЅРёРµ РѕСЂРіР°РЅРёР·Р°С†РёРё
    is_valid, error_msg = validate_organization_name(organization_name)
    if not is_valid:
        await message.answer(f"{error_msg}\n\nРџРѕРїСЂРѕР±СѓР№С‚Рµ РµС‰Рµ СЂР°Р·:")
        return
    
    await state.update_data(organization_name=organization_name)
    await state.set_state(ManageServiceProviderStates.input_phone)
    
    await message.answer(
        f"вњ… <b>РћСЂРіР°РЅРёР·Р°С†РёСЏ:</b> {organization_name}\n\n"
        "рџ“ћ <b>Р’РІРµРґРёС‚Рµ РєРѕРЅС‚Р°РєС‚РЅС‹Р№ С‚РµР»РµС„РѕРЅ РѕСЂРіР°РЅРёР·Р°С†РёРё:</b>\n"
        "Р¤РѕСЂРјР°С‚: +7XXXXXXXXXX РёР»Рё РјРѕР¶РµС‚Рµ РїСЂРѕРїСѓСЃС‚РёС‚СЊ СЌС‚РѕС‚ С€Р°Рі",
        parse_mode="HTML",
        reply_markup=get_phone_input_keyboard()
    )


@manage_service_providers_router.message(ManageServiceProviderStates.input_phone)
async def handle_phone_input(message: Message, state: FSMContext, session: AsyncSession):
    """РћР±СЂР°Р±РѕС‚РєР° РІРІРѕРґР° РєРѕРЅС‚Р°РєС‚РЅРѕРіРѕ С‚РµР»РµС„РѕРЅР°."""
    phone = message.text.strip()
    
    # Р’Р°Р»РёРґРёСЂСѓРµРј С‚РµР»РµС„РѕРЅ
    validator = PhoneValidator()
    if not validator.validate(phone):
        await message.answer(
            "вќЊ РќРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚ С‚РµР»РµС„РѕРЅР°.\n"
            "РСЃРїРѕР»СЊР·СѓР№С‚Рµ С„РѕСЂРјР°С‚: +7XXXXXXXXXX\n\n"
            "РџРѕРїСЂРѕР±СѓР№С‚Рµ РµС‰Рµ СЂР°Р· РёР»Рё РЅР°Р¶РјРёС‚Рµ 'РџСЂРѕРїСѓСЃС‚РёС‚СЊ':",
            reply_markup=get_phone_input_keyboard()
        )
        return
    
    # РќРѕСЂРјР°Р»РёР·СѓРµРј С‚РµР»РµС„РѕРЅ
    normalized_phone = validator.normalize(phone)
    await state.update_data(contact_phone=normalized_phone)
    await state.set_state(ManageServiceProviderStates.input_work_schedule)
    
    await message.answer(
        f"вњ… <b>РўРµР»РµС„РѕРЅ:</b> {normalized_phone}\n\n"
        "рџ•’ <b>Р’РІРµРґРёС‚Рµ СЂР°Р±РѕС‡РµРµ РІСЂРµРјСЏ:</b>\n"
        "РќР°РїСЂРёРјРµСЂ: 'РџРЅ-РџС‚ 9:00-18:00' РёР»Рё 'РљСЂСѓРіР»РѕСЃСѓС‚РѕС‡РЅРѕ'",
        parse_mode="HTML"
    )


@manage_service_providers_router.callback_query(F.data == "skip_phone")
async def handle_skip_phone(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """РџСЂРѕРїСѓСЃРє РІРІРѕРґР° С‚РµР»РµС„РѕРЅР°."""
    await state.set_state(ManageServiceProviderStates.input_work_schedule)
    
    await callback.message.edit_text(
        "вЏ­пёЏ <b>РўРµР»РµС„РѕРЅ РїСЂРѕРїСѓС‰РµРЅ</b>\n\n"
        "рџ•’ <b>Р’РІРµРґРёС‚Рµ СЂР°Р±РѕС‡РµРµ РІСЂРµРјСЏ:</b>\n"
        "РќР°РїСЂРёРјРµСЂ: 'РџРЅ-РџС‚ 9:00-18:00' РёР»Рё 'РљСЂСѓРіР»РѕСЃСѓС‚РѕС‡РЅРѕ'",
        parse_mode="HTML"
    )
    await callback.answer()


@manage_service_providers_router.message(ManageServiceProviderStates.input_work_schedule)
async def handle_work_schedule_input(message: Message, state: FSMContext, session: AsyncSession):
    """РћР±СЂР°Р±РѕС‚РєР° РІРІРѕРґР° СЂР°Р±РѕС‡РµРіРѕ РІСЂРµРјРµРЅРё."""
    work_schedule = message.text.strip()
    
    # Р’Р°Р»РёРґРёСЂСѓРµРј СЂР°Р±РѕС‡РµРµ РІСЂРµРјСЏ
    is_valid, error_msg = validate_work_schedule(work_schedule)
    if not is_valid:
        await message.answer(f"{error_msg}\n\nРџРѕРїСЂРѕР±СѓР№С‚Рµ РµС‰Рµ СЂР°Р·:")
        return
    
    await state.update_data(work_schedule=work_schedule)
    await show_provider_confirmation(message, state, session)


async def show_provider_confirmation(message: Message, state: FSMContext, session: AsyncSession):
    """РџРѕРєР°Р·С‹РІР°РµС‚ РїРѕРґС‚РІРµСЂР¶РґРµРЅРёРµ СЃРѕР·РґР°РЅРёСЏ РїРѕСЃС‚Р°РІС‰РёРєР° СѓСЃР»СѓРі."""
    data = await state.get_data()
    
    # РџРѕР»СѓС‡Р°РµРј РёРЅС„РѕСЂРјР°С†РёСЋ Рѕ Р–Рљ
    jk = await orm_get_jk_by_id(session, data['selected_jk_id'])
    category = OfferCategory(data['category'])
    user_info = data['user_info']
    
    user_name = user_info['first_name'] or 'РќРµРёР·РІРµСЃС‚РЅРѕ'
    if user_info['last_name']:
        user_name += f" {user_info['last_name']}"
    if user_info['username']:
        user_name += f" (@{user_info['username']})"
    
    phone_text = data.get('contact_phone', 'РЅРµ СѓРєР°Р·Р°РЅ')
    
    confirmation_text = (
        "вњ… <b>РџРѕРґС‚РІРµСЂР¶РґРµРЅРёРµ СЃРѕР·РґР°РЅРёСЏ РїРѕСЃС‚Р°РІС‰РёРєР° СѓСЃР»СѓРі</b>\n\n"
        f"рџЏў <b>Р–Рљ:</b> {jk.name}\n"
        f"рџ“ќ <b>РљР°С‚РµРіРѕСЂРёСЏ:</b> {category.get_display_name()} {category.get_emoji()}\n"
        f"рџЏ›пёЏ <b>РћСЂРіР°РЅРёР·Р°С†РёСЏ:</b> {data['organization_name']}\n"
        f"рџ‘¤ <b>РћС‚РІРµС‚СЃС‚РІРµРЅРЅРѕРµ Р»РёС†Рѕ:</b> {user_name}\n"
        f"рџ“ћ <b>РўРµР»РµС„РѕРЅ:</b> {phone_text}\n"
        f"рџ•’ <b>Р Р°Р±РѕС‡РµРµ РІСЂРµРјСЏ:</b> {data['work_schedule']}\n\n"
        "РЎРѕР·РґР°С‚СЊ РїРѕСЃС‚Р°РІС‰РёРєР° СѓСЃР»СѓРі?"
    )
    
    await state.set_state(ManageServiceProviderStates.confirm_provider)
    await message.answer(
        confirmation_text,
        parse_mode="HTML",
        reply_markup=get_confirmation_keyboard()
    )


@manage_service_providers_router.callback_query(F.data == "confirm_create_provider")
async def confirm_create_provider(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """РџРѕРґС‚РІРµСЂР¶РґРµРЅРёРµ СЃРѕР·РґР°РЅРёСЏ РїРѕСЃС‚Р°РІС‰РёРєР° СѓСЃР»СѓРі."""
    data = await state.get_data()
    
    # РЎРѕР·РґР°РµРј РїРѕСЃС‚Р°РІС‰РёРєР° СѓСЃР»СѓРі
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
        
        # РџРѕР»СѓС‡Р°РµРј РёРЅС„РѕСЂРјР°С†РёСЋ Рѕ Р–Рљ РґР»СЏ С„РёРЅР°Р»СЊРЅРѕРіРѕ СЃРѕРѕР±С‰РµРЅРёСЏ
        jk = await orm_get_jk_by_id(session, data['selected_jk_id'])
        category = OfferCategory(data['category'])
        
        await callback.message.edit_text(
            f"вњ… <b>РџРѕСЃС‚Р°РІС‰РёРє СѓСЃР»СѓРі СѓСЃРїРµС€РЅРѕ СЃРѕР·РґР°РЅ!</b>\n\n"
            f"рџЏў <b>Р–Рљ:</b> {jk.name}\n"
            f"рџ“ќ <b>РљР°С‚РµРіРѕСЂРёСЏ:</b> {category.get_display_name()} {category.get_emoji()}\n"
            f"рџЏ›пёЏ <b>РћСЂРіР°РЅРёР·Р°С†РёСЏ:</b> {data['organization_name']}\n\n"
            "РџРѕСЃС‚Р°РІС‰РёРє РїРѕР»СѓС‡Р°РµС‚ СѓРІРµРґРѕРјР»РµРЅРёСЏ Рѕ РЅРѕРІС‹С… Р·Р°СЏРІРєР°С… РїРѕ СЌС‚РѕР№ РєР°С‚РµРіРѕСЂРёРё.",
            parse_mode="HTML",
            reply_markup=get_keyboard(MAIN_KB)
        )
        
        await state.clear()
        await callback.answer("РџРѕСЃС‚Р°РІС‰РёРє СЃРѕР·РґР°РЅ!")
        
    except Exception as e:
        await callback.message.edit_text(
            f"вќЊ РћС€РёР±РєР° РїСЂРё СЃРѕР·РґР°РЅРёРё РїРѕСЃС‚Р°РІС‰РёРєР° СѓСЃР»СѓРі:\n{str(e)}",
            reply_markup=get_keyboard(MAIN_KB)
        )
        await callback.answer("РћС€РёР±РєР° СЃРѕР·РґР°РЅРёСЏ")


@manage_service_providers_router.callback_query(F.data == "cancel_add_provider")
async def cancel_add_provider(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """РћС‚РјРµРЅР° СЃРѕР·РґР°РЅРёСЏ РїРѕСЃС‚Р°РІС‰РёРєР° СѓСЃР»СѓРі."""
    await callback.message.edit_text(
        "вќЊ <b>РЎРѕР·РґР°РЅРёРµ РїРѕСЃС‚Р°РІС‰РёРєР° СѓСЃР»СѓРі РѕС‚РјРµРЅРµРЅРѕ</b>",
        parse_mode="HTML",
        reply_markup=get_keyboard(MAIN_KB)
    )
    await state.clear()
    await callback.answer("РћС‚РјРµРЅРµРЅРѕ")


@manage_service_providers_router.callback_query(F.data == "back_to_jk_selection")
async def back_to_jk_selection(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Р’РѕР·РІСЂР°С‚ Рє РІС‹Р±РѕСЂСѓ Р–Рљ."""
    user_id = callback.from_user.id
    
    # РџРѕР»СѓС‡Р°РµРј РґРѕСЃС‚СѓРїРЅС‹Рµ Р–Рљ
    user = await orm_get_user_by_id(session, user_id)
    if user.role == UserRole.ADMIN:
        available_jks = await orm_get_all_jks(session)
    else:
        available_jks = await orm_get_jks_by_user_admin(session, user_id)
    
    await state.set_state(ManageServiceProviderStates.select_jk)
    await callback.message.edit_text(
        "рџЏў <b>Р’С‹Р±РµСЂРёС‚Рµ Р–Рљ РґР»СЏ СѓРїСЂР°РІР»РµРЅРёСЏ РїРѕСЃС‚Р°РІС‰РёРєР°РјРё СѓСЃР»СѓРі:</b>",
        parse_mode="HTML",
        reply_markup=get_jk_selection_keyboard(available_jks)
    )
    await callback.answer()


@manage_service_providers_router.callback_query(F.data == "to_main_menu")
async def to_main_menu(callback: CallbackQuery, state: FSMContext):
    """РџРµСЂРµС…РѕРґ РІ РіР»Р°РІРЅРѕРµ РјРµРЅСЋ."""
    await callback.message.edit_text(
        "рџЏ  <b>Р“Р»Р°РІРЅРѕРµ РјРµРЅСЋ</b>",
        parse_mode="HTML",
        reply_markup=get_keyboard(MAIN_KB)
    )
    await state.clear()
    await callback.answer()


# РћР±СЂР°Р±РѕС‚С‡РёРє РґР»СЏ РЅРµРєРѕСЂСЂРµРєС‚РЅРѕРіРѕ РІРІРѕРґР° РІ СЃРѕСЃС‚РѕСЏРЅРёРё input_user_id
@manage_service_providers_router.message(ManageServiceProviderStates.input_user_id)
async def invalid_user_id_input(message: Message):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РЅРµРєРѕСЂСЂРµРєС‚РЅРѕРіРѕ РІРІРѕРґР° User ID."""
    await message.answer(
        "вќЊ РџРѕР¶Р°Р»СѓР№СЃС‚Р°, РІРІРµРґРёС‚Рµ РєРѕСЂСЂРµРєС‚РЅС‹Р№ User ID (С‡РёСЃР»Рѕ).\n"
        "РџРѕРїСЂРѕР±СѓР№С‚Рµ РµС‰Рµ СЂР°Р·:"
    )
