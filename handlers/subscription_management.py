# -*- coding: utf-8 -*-
# handlers/subscription_management.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import session_maker
from services.price_management_service import PriceManagementService
from services.subscription_service import SubscriptionService
from database.enums.subscription_enums import SubscriptionTier
from keyboards.subscription_keyboards import (
    get_subscription_management_keyboard,
    get_price_management_keyboard,
    get_price_confirm_keyboard,
    get_back_to_management_keyboard
)
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


subscription_management_router = Router()


class PriceEditStates(StatesGroup):
    waiting_for_price = State()
    confirming_price = State()


@subscription_management_router.callback_query(F.data == "subscription_management")
async def subscription_management_menu(callback: CallbackQuery, session: AsyncSession):
    """Главное меню управления подписками"""
    user_id = callback.from_user.id
    
    try:
        # Получаем сводку по управлению ценами
        summary = await PriceManagementService.get_management_summary(session)
        stats = summary["statistics"]
        
        # Инициализируем цены если нужно
        was_initialized = await PriceManagementService.initialize_prices_if_needed(session, user_id)
        if was_initialized:
            await session.commit()
            summary = await PriceManagementService.get_management_summary(session)
            stats = summary["statistics"]
        
        text = (
            "⚙️ <b>Управление подписками</b>\n\n"
            "📊 <b>Статистика:</b>\n"
            f"• Всего тарифов: {stats['total_tiers']}\n"
            f"• Настроено цен: {stats['configured_tiers']}\n"
            f"• Общий потенциал: {stats['revenue_potential']:,} ₸/мес\n"
            f"• Изменений всего: {stats['total_changes']}\n"
        )
        
        if stats['last_update']:
            text += f"• Последнее обновление: {stats['last_update'].strftime('%d.%m.%Y %H:%M')}\n"
        
        text += "\n💡 Выберите действие:"
        
        keyboard = get_subscription_management_keyboard()
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        # Создаем кнопку "Назад к панели создателя"
        back_keyboard = InlineKeyboardBuilder()
        back_keyboard.button(text="🔙 Назад", callback_data="creator_panel")
        
        await callback.message.edit_text(
            f"❌ Ошибка при загрузке управления подписками: {str(e)}",
            reply_markup=back_keyboard.as_markup(),
            parse_mode="HTML"
        )
    
    await callback.answer()


@subscription_management_router.callback_query(F.data == "price_management")
async def price_management_menu(callback: CallbackQuery, session: AsyncSession):
    """Меню управления ценами"""
    try:
        current_prices = await PriceManagementService.get_current_prices(session)
        
        text = "💰 <b>Управление ценами тарифов</b>\n\n"
        
        for tier in SubscriptionTier:
            tier_data = current_prices.get(tier.value, {})
            tier_name = tier.get_russian_name()
            price_text = tier_data.get("formatted_price", "Не установлено")
            status = "✅" if tier_data.get("is_active", False) else "⭕"
            
            text += f"{status} <b>{tier_name}</b>: {price_text}\n"
        
        text += "\n💡 Выберите тариф для изменения цены:"
        
        keyboard = get_price_management_keyboard()
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при загрузке цен: {str(e)}",
            reply_markup=get_back_to_management_keyboard(),
            parse_mode="HTML"
        )
    
    await callback.answer()


@subscription_management_router.callback_query(F.data.startswith("edit_price_"))
async def start_price_edit(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Начать редактирование цены тарифа"""
    tier_value = callback.data.replace("edit_price_", "")
    
    try:
        # Найдем тариф
        tier = None
        for t in SubscriptionTier:
            if t.value == tier_value:
                tier = t
                break
        
        if not tier:
            await callback.answer("❌ Неверный тариф")
            return
        
        # Получаем текущую цену
        current_price = await PriceManagementService.get_tier_price(session, tier)
        
        # Сохраняем данные в состояние
        await state.update_data(
            tier=tier.value,
            current_price=current_price
        )
        
        await state.set_state(PriceEditStates.waiting_for_price)
        
        tier_name = tier.get_russian_name()
        current_price_text = f"{current_price:,} ₸" if current_price > 0 else "Не установлено"
        
        text = (
            f"💰 <b>Изменение цены тарифа</b>\n\n"
            f"📋 Тариф: <b>{tier_name}</b>\n"
            f"💵 Текущая цена: {current_price_text}\n\n"
            f"💡 Введите новую цену в тенге (только число):\n\n"
            f"<i>Примеры:</i>\n"
            f"• 2990 (для 2,990 ₸)\n"
            f"• 5000 (для 5,000 ₸)\n"
            f"• 0 (отключить тариф)</i>"
        )
        
        if tier == SubscriptionTier.FREE:
            text += "\n\n⚠️ <b>Внимание:</b> Бесплатный тариф может иметь только цену 0"
        
        keyboard = get_back_to_management_keyboard()
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при начале редактирования: {str(e)}",
            reply_markup=get_back_to_management_keyboard(),
            parse_mode="HTML"
        )
    
    await callback.answer()


@subscription_management_router.message(PriceEditStates.waiting_for_price)
async def process_price_input(message: Message, state: FSMContext, session: AsyncSession):
    """Обработать ввод новой цены"""
    user_data = await state.get_data()
    tier_value = user_data.get("tier")
    current_price = user_data.get("current_price", 0)
    
    # Найдем тариф
    tier = None
    for t in SubscriptionTier:
        if t.value == tier_value:
            tier = t
            break
    
    if not tier:
        await message.answer("❌ Ошибка: тариф не найден")
        await state.clear()
        return
    
    # Валидируем ввод
    is_valid, new_price, error_msg = PriceManagementService.validate_price_input(message.text)
    
    if not is_valid:
        await message.answer(f"❌ {error_msg}\n\n💡 Попробуйте еще раз или используйте кнопку 'Назад'")
        return
    
    # Дополнительная проверка для FREE тарифа
    if tier == SubscriptionTier.FREE and new_price != 0:
        await message.answer("❌ Бесплатный тариф может иметь только цену 0\n\n💡 Попробуйте еще раз")
        return
    
    # Сохраняем новую цену в состояние
    await state.update_data(new_price=new_price)
    await state.set_state(PriceEditStates.confirming_price)
    
    # Формируем сообщение подтверждения
    tier_name = tier.get_russian_name()
    current_price_text = f"{current_price:,} ₸" if current_price > 0 else "Не установлено"
    new_price_text = f"{new_price:,} ₸" if new_price > 0 else "Отключен"
    
    if new_price == current_price:
        text = (
            f"💰 <b>Подтверждение изменения цены</b>\n\n"
            f"📋 Тариф: <b>{tier_name}</b>\n"
            f"💵 Цена остается: {new_price_text}\n\n"
            f"ℹ️ <i>Цена не изменится</i>"
        )
    else:
        change_icon = "📈" if new_price > current_price else "📉"
        text = (
            f"💰 <b>Подтверждение изменения цены</b>\n\n"
            f"📋 Тариф: <b>{tier_name}</b>\n"
            f"💵 Было: {current_price_text}\n"
            f"💰 Будет: {new_price_text}\n\n"
            f"{change_icon} <b>Подтвердить изменение?</b>"
        )
    
    keyboard = get_price_confirm_keyboard()
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@subscription_management_router.callback_query(F.data == "confirm_price_change", PriceEditStates.confirming_price)
async def confirm_price_change(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Подтвердить изменение цены"""
    user_data = await state.get_data()
    tier_value = user_data.get("tier")
    new_price = user_data.get("new_price", 0)
    current_price = user_data.get("current_price", 0)
    user_id = callback.from_user.id
    
    # Найдем тариф
    tier = None
    for t in SubscriptionTier:
        if t.value == tier_value:
            tier = t
            break
    
    if not tier:
        await callback.answer("❌ Ошибка: тариф не найден")
        await state.clear()
        return
    
    try:
        # Обновляем цену
        result = await PriceManagementService.update_tier_price(
            session=session,
            tier=tier,
            new_price=new_price,
            updated_by=user_id,
            notes=f"Изменено через бот пользователем {user_id}"
        )
        
        if result["success"]:
            await session.commit()
            
            # Формируем сообщение об успехе
            success_msg = PriceManagementService.format_price_change_message(
                tier=tier,
                old_price=current_price,
                new_price=new_price,
                updated_by=user_id
            )
            
            text = f"✅ <b>Цена успешно обновлена!</b>\n\n{success_msg}"
            
            keyboard = get_back_to_management_keyboard()
            
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            
        else:
            await callback.message.edit_text(
                f"❌ Ошибка: {result['error']}",
                reply_markup=get_back_to_management_keyboard(),
                parse_mode="HTML"
            )
        
    except Exception as e:
        await session.rollback()
        await callback.message.edit_text(
            f"❌ Ошибка при обновлении цены: {str(e)}",
            reply_markup=get_back_to_management_keyboard(),
            parse_mode="HTML"
        )
    
    await state.clear()
    await callback.answer()


@subscription_management_router.callback_query(F.data == "cancel_price_change")
async def cancel_price_change(callback: CallbackQuery, state: FSMContext):
    """Отменить изменение цены"""
    await state.clear()
    
    text = "❌ <b>Изменение цены отменено</b>\n\n💡 Выберите другое действие:"
    
    keyboard = get_back_to_management_keyboard()
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@subscription_management_router.callback_query(F.data == "price_history")
async def show_price_history(callback: CallbackQuery, session: AsyncSession):
    """Показать историю изменений цен"""
    try:
        history = await PriceManagementService.get_price_history(session, limit=10)
        
        if not history:
            text = (
                "📜 <b>История изменений цен</b>\n\n"
                "ℹ️ История пуста\n"
                "Изменения цен будут отображаться здесь"
            )
        else:
            text = "📜 <b>История изменений цен</b>\n<i>(последние 10 записей)</i>\n\n"
            
            for i, record in enumerate(history, 1):
                date_str = record["created_at"].strftime("%d.%m.%Y %H:%M")
                tier_name = record["tier_display"]
                price_text = f"{record['price']:,} ₸" if record['price'] > 0 else "Отключен"
                
                text += f"{i}. <b>{tier_name}</b> → {price_text}\n"
                text += f"   📅 {date_str}\n\n"
        
        keyboard = get_back_to_management_keyboard()
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при загрузке истории: {str(e)}",
            reply_markup=get_back_to_management_keyboard(),
            parse_mode="HTML"
        )
    
    await callback.answer()


@subscription_management_router.callback_query(F.data == "subscription_analytics")
async def show_subscription_analytics(callback: CallbackQuery, session: AsyncSession):
    """Показать аналитику подписок"""
    try:
        # Получаем статистику подписок через SubscriptionService
        analytics = await SubscriptionService.get_subscription_analytics(session)
        
        text = (
            "📊 <b>Аналитика подписок</b>\n\n"
            f"👥 <b>Всего пользователей:</b> {analytics['total_users']}\n"
            f"💳 <b>Активных подписок:</b> {analytics['active_subscriptions']}\n\n"
            f"<b>По тарифам:</b>\n"
        )
        
        for tier_stats in analytics['by_tier']:
            tier_name = tier_stats['tier_display']
            count = tier_stats['count']
            percentage = tier_stats['percentage']
            
            text += f"• {tier_name}: {count} ({percentage:.1f}%)\n"
        
        if analytics['revenue']:
            text += f"\n💰 <b>Месячная выручка:</b> {analytics['revenue']:,} ₸"
        
        keyboard = get_back_to_management_keyboard()
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при загрузке аналитики: {str(e)}",
            reply_markup=get_back_to_management_keyboard(),
            parse_mode="HTML"
        )
    
    await callback.answer()


@subscription_management_router.callback_query(F.data == "back_to_subscription_management")
async def back_to_subscription_management(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Вернуться к главному меню управления подписками"""
    await state.clear()
    await subscription_management_menu(callback, session)
