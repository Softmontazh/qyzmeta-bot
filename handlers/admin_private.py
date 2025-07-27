# coding: utf-8
# handlers/admin_private.py

from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession

from filters.chat_types import ChatTypeFilter, IsAdmin
from keyboards.reply import get_keyboard, USER_KB
from keyboards.subscription_keyboards import get_admin_subscription_keyboard, get_admin_user_subscription_keyboard
from services.subscription_service import SubscriptionService
from database.enums.subscription_enums import SubscriptionTier
from database.models.orm_user import orm_get_user_by_id


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


class AdminSubscriptionStates(StatesGroup):
    """Состояния для админ панели подписок"""
    searching_user = State()
    setting_tier = State()


ADMIN_KB = get_keyboard(
    "🕵️‍♂️ Лоты на модерации",
    "🚨 Лоты с жалобами", 
    "💰 Бизнес-модели",
    "🚪 Выйти из админки",
    placeholder="Админ панель",
    sizes=(
        2,
        1,
        1,
    ),
)


# Обработчик команды /admin
@admin_router.message(Command("admin"))
async def adm_chat(message: types.Message):
    print(f"это админка {message.from_user.id}")
    await message.answer("Вы в админке", reply_markup=ADMIN_KB)


# Обработчик нажатия на кнопку "🚪 Выйти из админки"
@admin_router.message(F.text.lower().contains("выйти из админки"))
@admin_router.message(Command("exit_admin"))
async def exit_admin(message: types.Message):
    print(f"выход из админки {message.from_user.id}")
    await message.answer("Вы вышли из админки", reply_markup=USER_KB)
    await message.delete()
    await message.answer("Вы можете вернуться в админку, через команду /admin")


# ==================== БИЗНЕС-МОДЕЛИ ====================

# Обработчик кнопки "💰 Бизнес-модели"
@admin_router.message(F.text.lower().contains("бизнес-модели"))
async def business_models_menu(message: types.Message, session: AsyncSession):
    """Главное меню бизнес-моделей"""
    stats = await SubscriptionService.get_admin_statistics(session)
    
    message_text = f"💰 <b>БИЗНЕС-МОДЕЛИ</b>\n\n"
    message_text += f"📊 <b>Статистика подписок:</b>\n"
    message_text += f"• Активных: {stats['summary']['total_active']}\n"
    message_text += f"• Истекших: {stats['summary']['total_expired']}\n"
    message_text += f"• Отмененных: {stats['summary']['total_cancelled']}\n"
    message_text += f"• Истекают скоро: {stats['summary']['expiring_soon']}\n\n"
    message_text += f"💵 <b>Месячный доход:</b> {stats['summary']['monthly_revenue']:,} ₸"
    
    keyboard = get_admin_subscription_keyboard()
    
    await message.answer(
        message_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@admin_router.callback_query(F.data == "admin_business_models")
async def admin_business_models_callback(callback: types.CallbackQuery, session: AsyncSession):
    """Callback для возврата в бизнес-модели"""
    await business_models_menu(callback.message, session)
    await callback.answer()


@admin_router.callback_query(F.data == "admin_sub_stats")
async def admin_subscription_stats(callback: types.CallbackQuery, session: AsyncSession):
    """Подробная статистика подписок"""
    stats = await SubscriptionService.get_admin_statistics(session)
    
    message_text = f"📊 <b>ПОДРОБНАЯ СТАТИСТИКА</b>\n\n"
    
    # Разбивка по тарифам
    message_text += f"🎯 <b>По тарифам:</b>\n"
    for tier_data in stats['tier_breakdown']:
        message_text += f"• {tier_data['name']}: {tier_data['count']} чел. "
        message_text += f"({tier_data['monthly_revenue']:,} ₸)\n"
    
    message_text += f"\n💰 <b>Общий доход:</b> {stats['summary']['monthly_revenue']:,} ₸/мес\n"
    
    # Истекающие подписки
    if stats['expiring_subscriptions']:
        message_text += f"\n⚠️ <b>Истекают в ближайшие 7 дней:</b>\n"
        for sub in stats['expiring_subscriptions'][:5]:  # Показываем первые 5
            message_text += f"• ID{sub['user_id']}: {sub['tier']} ({sub['days_left']} дн.)\n"
        
        if len(stats['expiring_subscriptions']) > 5:
            message_text += f"... и еще {len(stats['expiring_subscriptions']) - 5}\n"
    
    keyboard = get_admin_subscription_keyboard()
    
    await callback.message.edit_text(
        message_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@admin_router.callback_query(F.data == "admin_sub_search")
async def admin_search_user_start(callback: types.CallbackQuery, state: FSMContext):
    """Начать поиск пользователя"""
    await state.set_state(AdminSubscriptionStates.searching_user)
    
    await callback.message.edit_text(
        "🔍 <b>Поиск пользователя</b>\n\n"
        "Введите ID пользователя для просмотра и управления его подпиской:",
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(StateFilter(AdminSubscriptionStates.searching_user))
async def admin_search_user_process(message: types.Message, session: AsyncSession, state: FSMContext):
    """Обработка поиска пользователя"""
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


@admin_router.callback_query(F.data.startswith("admin_set_tier:"))
async def admin_set_user_tier(callback: types.CallbackQuery, session: AsyncSession):
    """Установить тариф пользователю"""
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
        payment_info="Установлено администратором",
        admin_notes=f"Тариф изменен админом ID{callback.from_user.id}"
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


@admin_router.callback_query(F.data.startswith("admin_cancel_sub:"))
async def admin_cancel_subscription(callback: types.CallbackQuery, session: AsyncSession):
    """Отменить подписку пользователя"""
    user_id = int(callback.data.split(":")[1])
    
    # Переводим на бесплатный тариф
    result = await SubscriptionService.upgrade_user_subscription(
        session=session,
        user_id=user_id,
        new_tier=SubscriptionTier.FREE,
        duration_days=None,
        payment_info="Отменено администратором",
        admin_notes=f"Подписка отменена админом ID{callback.from_user.id}"
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


@admin_router.callback_query(F.data == "admin_sub_expire")
async def admin_expire_subscriptions(callback: types.CallbackQuery, session: AsyncSession):
    """Принудительно истечь просроченные подписки"""
    expired_count = await SubscriptionService.expire_overdue_subscriptions(session)
    
    await callback.message.edit_text(
        f"✅ <b>Обновление завершено</b>\n\n"
        f"Истекло подписок: {expired_count}",
        parse_mode="HTML",
        reply_markup=get_admin_subscription_keyboard()
    )
    await callback.answer()


@admin_router.callback_query(F.data == "admin_sub_expiring")
async def admin_show_expiring(callback: types.CallbackQuery, session: AsyncSession):
    """Показать истекающие подписки"""
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
    
    await callback.message.edit_text(
        message_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()
