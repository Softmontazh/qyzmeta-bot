# -*- coding: utf-8 -*-
# keyboards/service_provider_keyboards.py
"""
Клавиатуры для управления поставщиками услуг.
"""

from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.enums.offer_category_enum import OfferCategory


def get_category_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора категории услуг."""
    buttons = []
    
    # Добавляем кнопки для каждой категории
    for category in OfferCategory:
        buttons.append([
            InlineKeyboardButton(
                text=f"{category.emoji} {category.display_name}",
                callback_data=f"select_category:{category.value}"
            )
        ])
    
    # Добавляем кнопку "Назад"
    buttons.append([
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_jk_selection"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_providers_keyboard(providers: List, jk_id: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком поставщиков услуг для ЖК.
    
    Args:
        providers: Список поставщиков услуг
        jk_id: ID жилого комплекса
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с поставщиками
    """
    buttons = []
    
    # Кнопки с поставщиками
    for provider in providers:
        category_emoji = provider.category.emoji
        status_emoji = "✅" if provider.is_active else "❌"
        notification_emoji = "🔔" if provider.receives_notifications else "🔕"
        
        button_text = f"{category_emoji} {provider.organization_name} {status_emoji}{notification_emoji}"
        buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"provider_details:{provider.id}"
            )
        ])
    
    # Кнопка добавления нового поставщика
    buttons.append([
        InlineKeyboardButton(
            text="➕ Добавить поставщика",
            callback_data=f"add_provider:{jk_id}"
        )
    ])
    
    # Кнопки навигации
    buttons.extend([
        [
            InlineKeyboardButton(
                text="🔙 Назад к выбору ЖК",
                callback_data="back_to_jk_selection"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="to_main_menu"
            )
        ]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_jk_selection_keyboard(jks: List) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора ЖК.
    
    Args:
        jks: Список жилых комплексов
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с ЖК
    """
    buttons = []
    
    for jk in jks:
        button_text = f"🏢 {jk.name} ({jk.city})"
        buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"select_jk:{jk.id}"
            )
        ])
    
    # Кнопка "Главное меню"
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="to_main_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_phone_input_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для ввода телефона с возможностью пропуска."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⏭️ Пропустить",
                callback_data="skip_phone"
            )
        ]
    ])


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру подтверждения создания поставщика."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Создать",
                callback_data="confirm_create_provider"
            ),
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data="cancel_add_provider"
            )
        ]
    ])


def get_provider_management_keyboard(provider_id: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для управления конкретным поставщиком.
    
    Args:
        provider_id: ID поставщика услуг
    
    Returns:
        InlineKeyboardMarkup: Клавиатура управления
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✏️ Редактировать",
                callback_data=f"edit_provider:{provider_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔔 Уведомления",
                callback_data=f"toggle_notifications:{provider_id}"
            ),
            InlineKeyboardButton(
                text="🔄 Статус",
                callback_data=f"toggle_status:{provider_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Удалить",
                callback_data=f"delete_provider:{provider_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_providers_list"
            )
        ]
    ])
