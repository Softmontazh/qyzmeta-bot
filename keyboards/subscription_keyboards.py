# -*- coding: utf-8 -*-
# keyboards/subscription_keyboards.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict

from database.enums.subscription_enums import SubscriptionTier, SubscriptionStatus


def get_subscription_upgrade_keyboard(
    current_tier: SubscriptionTier,
    suggestions: List[Dict]
) -> InlineKeyboardMarkup:
    """Клавиатура для выбора тарифа апгрейда"""
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки с доступными тарифами
    for suggestion in suggestions:
        tier = suggestion["tier"]
        name = suggestion["name"]
        price = suggestion["monthly_price"]
        
        if price > 0:
            text = f"{name} - {price:,} ₸/мес"
        else:
            text = name
            
        callback_data = f"upgrade_tier:{tier.value}"
        builder.button(text=text, callback_data=callback_data)
    
    # Кнопка отмены
    builder.button(text="❌ Отмена", callback_data="cancel_upgrade")
    
    # Размещаем по одной кнопке в ряду
    builder.adjust(1)
    
    return builder.as_markup()


def get_subscription_management_keyboard(
    user_id: int,
    subscription_info: Dict
) -> InlineKeyboardMarkup:
    """Клавиатура управления подпиской пользователя"""
    builder = InlineKeyboardBuilder()
    
    # Информация о подписке
    builder.button(
        text="📊 Подробная информация", 
        callback_data=f"sub_info:{user_id}"
    )
    
    # Если можно апгрейдить
    if subscription_info["tier"] != SubscriptionTier.VIP:
        builder.button(
            text="⬆️ Улучшить тариф", 
            callback_data=f"sub_upgrade:{user_id}"
        )
    
    # Если подписка истекает
    if subscription_info.get("is_expiring_soon"):
        builder.button(
            text="🔄 Продлить подписку", 
            callback_data=f"sub_renew:{user_id}"
        )
    
    builder.adjust(1)
    return builder.as_markup()


def get_admin_subscription_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для админ панели подписок"""
    builder = InlineKeyboardBuilder()
    
    # Основные разделы
    builder.button(text="📊 Статистика", callback_data="admin_sub_stats")
    builder.button(text="🔍 Поиск пользователя", callback_data="admin_sub_search")
    builder.button(text="📋 Все подписки", callback_data="admin_sub_list")
    builder.button(text="⚠️ Истекающие", callback_data="admin_sub_expiring")
    
    # Управление
    builder.button(text="🔄 Обновить просроченные", callback_data="admin_sub_expire")
    builder.button(text="➕ Создать подписку", callback_data="admin_sub_create")
    
    # Назад
    builder.button(text="🔙 Назад", callback_data="admin_business_models")
    
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def get_admin_user_subscription_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для управления подпиской конкретного пользователя"""
    builder = InlineKeyboardBuilder()
    
    # Изменить тариф
    for tier in SubscriptionTier:
        if tier != SubscriptionTier.FREE:
            builder.button(
                text=f"→ {tier.get_russian_name()}", 
                callback_data=f"admin_set_tier:{user_id}:{tier.value}"
            )
    
    # Отменить подписку
    builder.button(
        text="❌ Отменить подписку", 
        callback_data=f"admin_cancel_sub:{user_id}"
    )
    
    # Назад
    builder.button(text="🔙 Назад", callback_data="admin_sub_search")
    
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()


def get_subscription_duration_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора длительности подписки"""
    builder = InlineKeyboardBuilder()
    
    durations = [
        ("1 месяц", 30),
        ("3 месяца", 90),
        ("6 месяцев", 180),
        ("1 год", 365)
    ]
    
    for text, days in durations:
        builder.button(
            text=text, 
            callback_data=f"sub_duration:{days}"
        )
    
    builder.button(text="❌ Отмена", callback_data="cancel_subscription")
    
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def get_address_limit_exceeded_keyboard(
    user_id: int,
    current_tier: SubscriptionTier
) -> InlineKeyboardMarkup:
    """Клавиатура когда достигнут лимит адресов"""
    builder = InlineKeyboardBuilder()
    
    # Показываем только следующий доступный тариф
    next_tier = None
    current_limit = current_tier.get_address_limit()
    
    for tier in SubscriptionTier:
        if tier.get_address_limit() > current_limit:
            next_tier = tier
            break
    
    if next_tier:
        price = next_tier.get_monthly_price()
        text = f"⬆️ {next_tier.get_russian_name()}"
        if price > 0:
            text += f" ({price:,} ₸/мес)"
            
        builder.button(
            text=text,
            callback_data=f"quick_upgrade:{next_tier.value}"
        )
    
    # Посмотреть все тарифы
    builder.button(
        text="📋 Все тарифы", 
        callback_data="view_all_tiers"
    )
    
    # Моя подписка
    builder.button(
        text="📊 Моя подписка", 
        callback_data=f"sub_info:{user_id}"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_payment_confirmation_keyboard(
    tier: SubscriptionTier,
    duration_days: int
) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения платежа"""
    builder = InlineKeyboardBuilder()
    
    total_price = tier.get_monthly_price() * (duration_days / 30)
    
    builder.button(
        text=f"💳 Оплатить {total_price:,.0f} ₸", 
        callback_data=f"pay_confirm:{tier.value}:{duration_days}"
    )
    
    builder.button(text="❌ Отмена", callback_data="cancel_payment")
    
    builder.adjust(1)
    return builder.as_markup()


def get_subscription_info_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура в сообщении с информацией о подписке"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="⬆️ Улучшить тариф", 
        callback_data=f"sub_upgrade:{user_id}"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_tier_comparison_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура сравнения тарифов"""
    builder = InlineKeyboardBuilder()
    
    # Кнопки выбора тарифа
    for tier in SubscriptionTier:
        if tier != SubscriptionTier.FREE:
            price = tier.get_monthly_price()
            text = f"{tier.get_russian_name()}"
            if price > 0:
                text += f" - {price:,} ₸"
                
            builder.button(
                text=text,
                callback_data=f"select_tier:{tier.value}"
            )
    
    builder.button(text="🔙 Назад", callback_data="back_to_subscription")
    
    builder.adjust(1)
    return builder.as_markup()
