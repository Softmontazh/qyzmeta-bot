# -*- coding: utf-8 -*-
# handlers/business_models.py
"""
Обработчики для бизнес-моделей и монетизации.
Доступны только создателю платформы.
"""

from aiogram import F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.subscription_keyboards import get_admin_subscription_keyboard, get_admin_user_subscription_keyboard
from services.subscription_service import SubscriptionService
from database.enums.subscription_enums import SubscriptionTier
from database.models.orm_user import orm_get_user_by_id
import os

business_models_router = Router()


def is_creator_by_environment(user_id: int) -> bool:
    """Проверяет, является ли пользователь создателем через переменную окружения"""
    creator_ids = os.getenv("CREATOR_ID")
    if not creator_ids:
        return False
    
    creator_id_list = [id_str.strip() for id_str in creator_ids.split(",")]
    return str(user_id) in creator_id_list


class BusinessModelStates(StatesGroup):
    """Состояния для работы с бизнес-моделями"""
    searching_user = State()
    setting_tier = State()


# ==================== БИЗНЕС-МОДЕЛИ ====================

@business_models_router.message(F.text.lower().contains("бизнес-модели"))
async def business_models_menu(message: types.Message, session: AsyncSession, user_id: int = None):
    """Главное меню бизнес-моделей"""
    # Получаем user_id либо из параметра, либо из сообщения
    if user_id is None:
        user_id = message.from_user.id
    
    # Проверяем права создателя
    if not is_creator_by_environment(user_id):
        await message.answer("❌ У вас нет прав доступа к бизнес-моделям.")
        return
    
    stats = await SubscriptionService.get_admin_statistics(session)
    
    message_text = f"💰 <b>БИЗНЕС-МОДЕЛИ</b>\n\n"
    
    # Краткая сводка
    message_text += f"📊 <b>Общая статистика:</b>\n"
    message_text += f"• Активных: {stats['summary']['total_active']}\n"
    message_text += f"• Истекших: {stats['summary']['total_expired']}\n"
    message_text += f"• Отмененных: {stats['summary']['total_cancelled']}\n"
    message_text += f"• Истекают скоро: {stats['summary']['expiring_soon']}\n\n"
    
    # Детализация по тарифам
    message_text += f"🎯 <b>По тарифам:</b>\n"
    for tier_data in stats['tier_breakdown']:
        message_text += f"• {tier_data['name']}: {tier_data['count']} чел. "
        message_text += f"({tier_data['monthly_revenue']:,} ₸/мес)\n"
    
    message_text += f"\n💰 <b>Общий доход:</b> {stats['summary']['monthly_revenue']:,} ₸/мес"
    
    # Истекающие подписки (если есть)
    if stats['expiring_subscriptions']:
        message_text += f"\n\n⚠️ <b>Истекают в ближайшие 7 дней:</b>\n"
        for sub in stats['expiring_subscriptions'][:3]:  # Показываем первые 3
            message_text += f"• ID{sub['user_id']}: {sub['tier']} ({sub['days_left']} дн.)\n"
        
        if len(stats['expiring_subscriptions']) > 3:
            message_text += f"... и еще {len(stats['expiring_subscriptions']) - 3}"
    
    keyboard = get_admin_subscription_keyboard()
    
    await message.answer(
        message_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@business_models_router.callback_query(F.data == "admin_business_models")
async def admin_business_models_callback(callback: types.CallbackQuery, session: AsyncSession):
    """Callback для возврата в бизнес-модели"""
    if not is_creator_by_environment(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    # Получаем статистику для отображения
    stats = await SubscriptionService.get_admin_statistics(session)
    
    # Добавляем timestamp для гарантии уникальности
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    message_text = f"💰 <b>БИЗНЕС-МОДЕЛИ</b> <i>({timestamp})</i>\n\n"
    
    # Краткая сводка
    message_text += f"📊 <b>Общая статистика:</b>\n"
    message_text += f"• Активных: {stats['summary']['total_active']}\n"
    message_text += f"• Истекших: {stats['summary']['total_expired']}\n"
    message_text += f"• Отмененных: {stats['summary']['total_cancelled']}\n"
    message_text += f"• Истекают скоро: {stats['summary']['expiring_soon']}\n\n"
    
    # Детализация по тарифам
    message_text += f"🎯 <b>По тарифам:</b>\n"
    for tier_data in stats['tier_breakdown']:
        message_text += f"• {tier_data['name']}: {tier_data['count']} чел. "
        message_text += f"({tier_data['monthly_revenue']:,} ₸/мес)\n"
    
    message_text += f"\n💰 <b>Общий доход:</b> {stats['summary']['monthly_revenue']:,} ₸/мес"
    
    # Истекающие подписки (если есть)
    if stats['expiring_subscriptions']:
        message_text += f"\n\n⚠️ <b>Истекают в ближайшие 7 дней:</b>\n"
        for sub in stats['expiring_subscriptions'][:3]:  # Показываем первые 3
            message_text += f"• ID{sub['user_id']}: {sub['tier']} ({sub['days_left']} дн.)\n"
        
        if len(stats['expiring_subscriptions']) > 3:
            message_text += f"... и еще {len(stats['expiring_subscriptions']) - 3}"
    
    keyboard = get_admin_subscription_keyboard()
    
    # Проверяем, отличается ли новый контент от текущего
    current_text = callback.message.text or ""
    if current_text.strip() == message_text.strip():
        # Если контент одинаковый, просто отвечаем на callback без изменения сообщения
        await callback.answer("📊 Обновлено")
        return
    
    try:
        await callback.message.edit_text(
            message_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    except Exception as e:
        # Если не удалось отредактировать, просто отвечаем
        await callback.answer("📊 Актуальные данные")
    
    await callback.answer()


@business_models_router.callback_query(F.data == "admin_sub_list")
async def admin_subscription_list(callback: types.CallbackQuery, session: AsyncSession):
    """Список всех подписок"""
    if not is_creator_by_environment(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
        
    # Получаем список всех подписок
    all_subscriptions = await SubscriptionService.get_all_subscriptions(session)
    
    message_text = f"📋 <b>ВСЕ ПОДПИСКИ</b>\n\n"
    
    if not all_subscriptions:
        message_text += "❌ Подписок не найдено"
    else:
        message_text += f"👥 <b>Всего подписок:</b> {len(all_subscriptions)}\n\n"
        
        # Группируем по тарифам
        from collections import defaultdict
        by_tier = defaultdict(list)
        
        for sub in all_subscriptions:
            by_tier[sub.tier].append(sub)
        
        # Показываем по тарифам
        tier_names = {
            'FREE': '🆓 Бесплатный',
            'BASIC': '⭐ Базовый', 
            'PREMIUM': '🚀 Премиум',
            'VIP': '👑 VIP'
        }
        
        for tier, subs in by_tier.items():
            tier_name = tier_names.get(tier.value, tier.value)
            message_text += f"<b>{tier_name}:</b> {len(subs)} чел.\n"
            
            # Показываем первые 5 пользователей
            for i, sub in enumerate(subs[:5]):
                status_emoji = "✅" if sub.status.value == "ACTIVE" else "❌"
                message_text += f"  {status_emoji} ID {sub.user_id}"
                if sub.tier.value != 'FREE':
                    message_text += f" (до {sub.expires_at.strftime('%d.%m.%Y')})"
                message_text += "\n"
            
            if len(subs) > 5:
                message_text += f"  ... и еще {len(subs) - 5} чел.\n"
            message_text += "\n"
    
    # Кнопка назад к бизнес-моделям
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="⬅️ Назад к бизнес-моделям", 
            callback_data="admin_business_models"
        )]
    ])
    
    await callback.message.edit_text(
        message_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@business_models_router.callback_query(F.data == "admin_sub_search")
async def admin_search_user_start(callback: types.CallbackQuery, state: FSMContext):
    """Начать поиск пользователя"""
    if not is_creator_by_environment(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
        
    await state.set_state(BusinessModelStates.searching_user)
    
    await callback.message.edit_text(
        "🔍 <b>Поиск пользователя</b>\n\n"
        "Введите ID пользователя для просмотра и управления его подпиской:",
        parse_mode="HTML"
    )
    await callback.answer()


@business_models_router.message(StateFilter(BusinessModelStates.searching_user))
async def admin_search_user_process(message: types.Message, session: AsyncSession, state: FSMContext):
    """Обработка поиска пользователя"""
    if not is_creator_by_environment(message.from_user.id):
        await message.answer("❌ У вас нет прав доступа к бизнес-моделям.")
        await state.clear()
        return
        
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректный ID пользователя (число)")
        return
    
    # Проверяем существование пользователя
    user = await orm_get_user_by_id(session, user_id)
    if not user:
        await message.answer(f"❌ Пользователь с ID {user_id} не найден")
        return
    
    # Получаем информацию о подписке
    subscription_info = await SubscriptionService.get_user_subscription_info(
        session, user_id
    )
    
    message_text = f"👤 <b>Пользователь ID {user_id}</b>\n"
    message_text += f"📛 <b>Имя:</b> {user.first_name}\n"
    message_text += f"🎭 <b>Роль:</b> {user.role.value}\n\n"
    
    message_text += SubscriptionService.format_subscription_message(subscription_info)
    
    if subscription_info["has_subscription"] and subscription_info.get("payment_info"):
        message_text += f"\n💳 <b>Последний платеж:</b> {subscription_info['payment_info']}"
    
    keyboard = get_admin_user_subscription_keyboard(user_id)
    
    await message.answer(
        message_text,
        parse_mode="HTML", 
        reply_markup=keyboard
    )
    
    await state.clear()


@business_models_router.callback_query(F.data.startswith("admin_set_tier:"))
async def admin_set_user_tier(callback: types.CallbackQuery, session: AsyncSession):
    """Установить тариф пользователю"""
    if not is_creator_by_environment(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
        
    parts = callback.data.split(":")
    user_id = int(parts[1])
    tier_value = parts[2]
    tier = SubscriptionTier(tier_value)
    
    # Устанавливаем тариф на 30 дней
    result = await SubscriptionService.upgrade_user_subscription(
        session=session,
        user_id=user_id,
        new_tier=tier,
        duration_days=30,
        payment_info="Установлено создателем",
        admin_notes=f"Тариф изменен создателем ID{callback.from_user.id}"
    )
    
    if result["success"]:
        await callback.message.edit_text(
            f"✅ <b>Тариф успешно установлен!</b>\n\n"
            f"👤 <b>Пользователь:</b> {user_id}\n"
            f"🎯 <b>Новый тариф:</b> {result['tier_name']}\n"
            f"🏠 <b>Лимит адресов:</b> {result['max_addresses']}\n"
            f"📅 <b>Действует до:</b> {result['expires_at'].strftime('%d.%m.%Y') if result['expires_at'] else 'Бессрочно'}",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text("❌ Ошибка при установке тарифа")
    
    await callback.answer()


@business_models_router.callback_query(F.data.startswith("admin_cancel_sub:"))
async def admin_cancel_subscription(callback: types.CallbackQuery, session: AsyncSession):
    """Отменить подписку пользователя"""
    if not is_creator_by_environment(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
        
    user_id = int(callback.data.split(":")[1])
    
    # Переводим на бесплатный тариф
    result = await SubscriptionService.upgrade_user_subscription(
        session=session,
        user_id=user_id,
        new_tier=SubscriptionTier.FREE,
        duration_days=None,
        payment_info="Отменено создателем",
        admin_notes=f"Подписка отменена создателем ID{callback.from_user.id}"
    )
    
    if result["success"]:
        await callback.message.edit_text(
            f"❌ <b>Подписка отменена</b>\n\n"
            f"👤 <b>Пользователь:</b> {user_id}\n"
            f"🎯 <b>Тариф:</b> {result['tier_name']}\n"
            f"🏠 <b>Лимит адресов:</b> {result['max_addresses']}",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text("❌ Ошибка при отмене подписки")
    
    await callback.answer()


@business_models_router.callback_query(F.data == "admin_sub_expire")
async def admin_expire_subscriptions(callback: types.CallbackQuery, session: AsyncSession):
    """Принудительно истечь просроченные подписки"""
    if not is_creator_by_environment(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
        
    expired_count = await SubscriptionService.expire_overdue_subscriptions(session)
    
    await callback.message.edit_text(
        f"✅ <b>Обновление завершено</b>\n\n"
        f"Истекло подписок: {expired_count}",
        parse_mode="HTML",
        reply_markup=get_admin_subscription_keyboard()
    )
    await callback.answer()


@business_models_router.callback_query(F.data == "admin_sub_expiring")
async def admin_show_expiring(callback: types.CallbackQuery, session: AsyncSession):
    """Показать истекающие подписки"""
    if not is_creator_by_environment(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
        
    stats = await SubscriptionService.get_admin_statistics(session)
    expiring = stats['expiring_subscriptions']
    
    if not expiring:
        message_text = "✅ <b>Нет истекающих подписок</b>\n\nВсе подписки в порядке!"
    else:
        message_text = f"⚠️ <b>ИСТЕКАЮЩИЕ ПОДПИСКИ ({len(expiring)})</b>\n\n"
        for sub in expiring[:10]:  # Показываем первые 10
            message_text += f"👤 ID{sub['user_id']}: {sub['tier']}\n"
            message_text += f"   ⏰ Осталось: {sub['days_left']} дн.\n"
            message_text += f"   📅 Истекает: {sub['expires_at'].strftime('%d.%m.%Y')}\n\n"
        
        if len(expiring) > 10:
            message_text += f"... и еще {len(expiring) - 10} подписок"
    
    keyboard = get_admin_subscription_keyboard()
    
    # Проверяем, отличается ли контент от текущего
    current_text = callback.message.text or ""
    if current_text.strip() == message_text.strip():
        await callback.answer("⚠️ Данные актуальны")
        return
    
    await callback.message.edit_text(
        message_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()
