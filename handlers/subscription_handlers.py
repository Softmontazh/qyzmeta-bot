# -*- coding: utf-8 -*-
# handlers/subscription_handlers.py

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession

from services.subscription_service import SubscriptionService
from keyboards.subscription_keyboards import (
    get_subscription_upgrade_keyboard,
    get_user_subscription_management_keyboard,
    get_tier_comparison_keyboard,
    get_subscription_duration_keyboard,
    get_payment_confirmation_keyboard,
    get_subscription_info_keyboard
)
from database.enums.subscription_enums import SubscriptionTier
from database.models.orm_user import orm_get_user_by_id

subscription_router = Router()


class SubscriptionStates(StatesGroup):
    """Состояния для работы с подписками"""
    selecting_tier = State()
    selecting_duration = State()
    confirming_payment = State()


@subscription_router.callback_query(F.data.startswith("sub_info:"))
async def show_subscription_info(callback: CallbackQuery, session: AsyncSession):
    """Показать подробную информацию о подписке"""
    user_id = int(callback.data.split(":")[1])
    
    # Проверяем права доступа (пользователь может смотреть только свою подписку)
    if callback.from_user.id != user_id:
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    subscription_info = await SubscriptionService.get_user_subscription_info(
        session, user_id
    )
    
    message = SubscriptionService.format_subscription_message(subscription_info)
    
    # Добавляем дополнительную информацию
    if subscription_info["has_subscription"] and subscription_info["expires_at"]:
        message += f"\n📅 <b>Действует до:</b> {subscription_info['expires_at'].strftime('%d.%m.%Y')}"
    
    if subscription_info.get("payment_info"):
        message += f"\n💳 <b>Платеж:</b> {subscription_info['payment_info']}"
    
    keyboard = get_subscription_info_keyboard(user_id)
    
    await callback.message.edit_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@subscription_router.callback_query(F.data.startswith("sub_upgrade:"))
async def start_subscription_upgrade(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Начать процесс апгрейда подписки"""
    user_id = int(callback.data.split(":")[1])
    
    # Проверяем права доступа
    if callback.from_user.id != user_id:
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    subscription_info = await SubscriptionService.get_user_subscription_info(
        session, user_id
    )
    
    current_tier = subscription_info["tier"]
    suggestions = await SubscriptionService.get_upgrade_suggestions(session, current_tier)
    
    if not suggestions:
        await callback.answer("✅ У вас уже максимальный тариф!", show_alert=True)
        return
    
    message = f"⬆️ <b>Улучшить тариф</b>\n\n"
    message += f"📊 <b>Текущий:</b> {subscription_info['tier_name']}\n"
    message += f"🏠 <b>Адреса:</b> {subscription_info['current_addresses']}/{subscription_info['max_addresses']}\n\n"
    message += "🎯 <b>Выберите новый тариф:</b>"
    
    keyboard = get_subscription_upgrade_keyboard(current_tier, suggestions)
    
    await callback.message.edit_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@subscription_router.callback_query(F.data.startswith("upgrade_tier:"))
async def select_upgrade_tier(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Выбор тарифа для апгрейда"""
    tier_value = callback.data.split(":")[1]
    tier = SubscriptionTier(tier_value)
    
    await state.update_data(selected_tier=tier)
    await state.set_state(SubscriptionStates.selecting_duration)
    
    # Получаем актуальную цену из базы данных
    monthly_price = await tier.get_monthly_price_async(session)
    
    message = f"⏰ <b>Выберите срок подписки</b>\n\n"
    message += f"🎯 <b>Тариф:</b> {tier.get_russian_name()}\n"
    message += f"💰 <b>Стоимость:</b> {monthly_price:,} ₸/мес\n\n"
    message += "📅 <b>Варианты оплаты:</b>"
    
    keyboard = get_subscription_duration_keyboard()
    
    await callback.message.edit_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@subscription_router.callback_query(F.data.startswith("sub_duration:"))
async def select_subscription_duration(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Выбор длительности подписки"""
    duration_days = int(callback.data.split(":")[1])
    
    state_data = await state.get_data()
    tier = state_data.get("selected_tier")
    
    if not tier:
        await callback.answer("❌ Ошибка: тариф не выбран", show_alert=True)
        return
    
    await state.update_data(duration_days=duration_days)
    await state.set_state(SubscriptionStates.confirming_payment)
    
    # Получаем актуальную цену из базы данных
    monthly_price = await tier.get_monthly_price_async(session)
    total_price = monthly_price * (duration_days / 30)
    
    message = f"💳 <b>Подтверждение платежа</b>\n\n"
    message += f"🎯 <b>Тариф:</b> {tier.get_russian_name()}\n"
    message += f"📅 <b>Срок:</b> {duration_days} дней\n"
    message += f"💰 <b>К оплате:</b> {total_price:,.0f} ₸\n\n"
    
    # Преимущества тарифа
    benefits = SubscriptionService._get_tier_benefits(tier)
    message += "✨ <b>Что входит:</b>\n"
    for benefit in benefits:
        message += f"• {benefit}\n"
    
    keyboard = get_payment_confirmation_keyboard(tier, duration_days)
    
    await callback.message.edit_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@subscription_router.callback_query(F.data.startswith("pay_confirm:"))
async def confirm_payment(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Подтверждение и обработка платежа"""
    parts = callback.data.split(":")
    tier_value = parts[1]
    duration_days = int(parts[2])
    
    tier = SubscriptionTier(tier_value)
    user_id = callback.from_user.id
    
    # В реальном приложении здесь была бы интеграция с платежной системой
    # Пока что просто создаем подписку напрямую
    
    # Формируем информацию о платеже  
    monthly_price = await tier.get_monthly_price_async(session)
    total_price = monthly_price * (duration_days / 30)
    payment_info = f"Тестовый платеж {total_price:,.0f} ₸ за {tier.get_russian_name()}"
    
    # Создаем/обновляем подписку
    result = await SubscriptionService.upgrade_user_subscription(
        session=session,
        user_id=user_id,
        new_tier=tier,
        duration_days=duration_days,
        payment_info=payment_info,
        admin_notes="Оплата через бота"
    )
    
    if result["success"]:
        message = f"✅ <b>Подписка успешно оформлена!</b>\n\n"
        message += f"🎯 <b>Тариф:</b> {result['tier_name']}\n"
        message += f"🏠 <b>Лимит адресов:</b> {result['max_addresses']}\n"
        
        if result["expires_at"]:
            message += f"📅 <b>Действует до:</b> {result['expires_at'].strftime('%d.%m.%Y')}\n"
        
        message += f"\n💰 <b>Оплачено:</b> {total_price:,.0f} ₸"
        
        keyboard = get_subscription_info_keyboard(user_id)
        
        await callback.message.edit_text(
            message,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(
            "❌ <b>Ошибка при оформлении подписки</b>\n\nПопробуйте позже или обратитесь в поддержку.",
            parse_mode="HTML"
        )
    
    await state.clear()
    await callback.answer()


@subscription_router.callback_query(F.data.startswith("quick_upgrade:"))
async def quick_upgrade(callback: CallbackQuery, session: AsyncSession):
    """Быстрое обновление до следующего тарифа"""
    tier_value = callback.data.split(":")[1]
    tier = SubscriptionTier(tier_value)
    user_id = callback.from_user.id
    
    # Обновляем на месяц по умолчанию
    duration_days = 30
    total_price = await tier.get_monthly_price_async(session)
    
    payment_info = f"Быстрый апгрейд {total_price:,} ₸"
    
    result = await SubscriptionService.upgrade_user_subscription(
        session=session,
        user_id=user_id,
        new_tier=tier,
        duration_days=duration_days,
        payment_info=payment_info,
        admin_notes="Быстрый апгрейд"
    )
    
    if result["success"]:
        message = f"🚀 <b>Тариф обновлен!</b>\n\n"
        message += f"🎯 <b>Новый тариф:</b> {result['tier_name']}\n"
        message += f"🏠 <b>Лимит адресов:</b> {result['max_addresses']}\n"
        message += f"💰 <b>Оплачено:</b> {total_price:,} ₸\n\n"
        message += "✨ Теперь вы можете зарегистрировать дополнительные адреса!"
        
        await callback.message.edit_text(message, parse_mode="HTML")
    else:
        await callback.answer("❌ Ошибка обновления тарифа", show_alert=True)
    
    await callback.answer()


@subscription_router.callback_query(F.data == "view_all_tiers")
async def view_all_tiers(callback: CallbackQuery, session: AsyncSession):
    """Показать сравнение всех тарифов"""
    message = "📋 <b>Сравнение тарифов</b>\n\n"
    
    for tier in SubscriptionTier:
        message += f"🎯 <b>{tier.get_russian_name()}</b>\n"
        message += f"   🏠 Адреса: {tier.get_address_limit()}\n"
        
        # Получаем актуальную цену из базы данных
        monthly_price = await tier.get_monthly_price_async(session)
        if monthly_price > 0:
            message += f"   💰 {monthly_price:,} ₸/мес\n"
        else:
            message += f"   💰 Бесплатно\n"
        
        benefits = SubscriptionService._get_tier_benefits(tier)
        for benefit in benefits[:2]:  # Показываем только первые 2 преимущества
            message += f"   • {benefit}\n"
        message += "\n"
    
    keyboard = get_tier_comparison_keyboard()
    
    await callback.message.edit_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@subscription_router.callback_query(F.data.startswith("select_tier:"))
async def select_tier_from_comparison(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Выбор тарифа из сравнительной таблицы"""
    tier_value = callback.data.split(":")[1]
    tier = SubscriptionTier(tier_value)
    
    await state.update_data(selected_tier=tier)
    await state.set_state(SubscriptionStates.selecting_duration)
    
    # Получаем актуальную цену из базы данных
    monthly_price = await tier.get_monthly_price_async(session)
    
    message = f"⏰ <b>Выбрать срок подписки</b>\n\n"
    message += f"🎯 <b>Тариф:</b> {tier.get_russian_name()}\n"
    message += f"💰 <b>Стоимость:</b> {monthly_price:,} ₸/мес"
    
    keyboard = get_subscription_duration_keyboard()
    
    await callback.message.edit_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@subscription_router.callback_query(F.data.in_(["cancel_upgrade", "cancel_subscription", "cancel_payment"]))
async def cancel_subscription_action(callback: CallbackQuery, state: FSMContext):
    """Отмена действий с подпиской"""
    await state.clear()
    
    await callback.message.edit_text(
        "❌ <b>Действие отменено</b>\n\n"
        "Вы можете вернуться к управлению подпиской в любое время.",
        parse_mode="HTML"
    )
    await callback.answer()


@subscription_router.callback_query(F.data == "back_to_subscription")
async def back_to_subscription(callback: CallbackQuery, session: AsyncSession):
    """Вернуться к информации о подписке"""
    user_id = callback.from_user.id
    
    subscription_info = await SubscriptionService.get_user_subscription_info(
        session, user_id
    )
    
    message = SubscriptionService.format_subscription_message(subscription_info)
    keyboard = get_user_subscription_management_keyboard(user_id, subscription_info)
    
    await callback.message.edit_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()
