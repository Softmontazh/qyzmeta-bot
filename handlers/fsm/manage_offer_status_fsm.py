# -*- coding: utf-8 -*-
# handlers/fsm/manage_offer_status_fsm.py

from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.orm_offer import orm_update_offer_status, orm_get_offer_with_user_info
from database.models.orm_jk_service_provider import orm_get_service_providers_by_user
from database.enums.offer_enums import OfferStatus
from services.notification_service import notify_user_status_change

manage_offer_status_router = Router()


class ManageOfferStatus(StatesGroup):
    """Состояния для управления статусом заявки."""
    select_offer = State()  # Выбор заявки
    select_status = State()  # Выбор нового статуса


def get_status_keyboard(current_status: OfferStatus) -> InlineKeyboardMarkup:
    """Создает клавиатуру со статусами (исключая текущий)."""
    statuses = [
        (OfferStatus.IN_PROGRESS, "⏳ Принять в работу"),
        (OfferStatus.COMPLETED, "✅ Выполнено"),
        (OfferStatus.CANCELLED, "❌ Отменить"),
        (OfferStatus.ARCHIVED, "📦 Архивировать"),
    ]
    
    keyboard = []
    for status, text in statuses:
        if status != current_status:
            keyboard.append([
                InlineKeyboardButton(
                    text=text, 
                    callback_data=f"set_status:{status.value}"
                )
            ])
    
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="cancel_status_change")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@manage_offer_status_router.message(Command("manage_offer_status"))
async def start_manage_offer_status(message: Message, state: FSMContext, session: AsyncSession):
    """Начало управления статусом заявки (только для поставщиков услуг)."""
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь АКТИВНЫМ поставщиком услуг
    service_providers = await orm_get_service_providers_by_user(session, user_id)
    active_providers = [sp for sp in service_providers if sp.is_active]
    
    if not active_providers:
        await message.answer(
            "❌ У вас нет активных прав для управления статусами заявок.\n"
            "Эта функция доступна только активным поставщикам услуг."
        )
        return
    
    await message.answer(
        "🔧 <b>Управление статусом заявки</b>\n\n"
        "Отправьте номер заявки для изменения её статуса.\n"
        "Например: <code>123</code>\n\n"
        "Или нажмите \"Отмена\" для выхода.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_manage_status")]
            ]
        )
    )
    await state.set_state(ManageOfferStatus.select_offer)


@manage_offer_status_router.message(ManageOfferStatus.select_offer)
async def select_offer(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка выбора заявки по номеру с проверкой принадлежности."""
    
    # Проверяем команды отмены
    if message.text.strip().lower() in ["❌ отмена", "/cancel", "/start", "/menu"]:
        await message.answer("❌ Выбор заявки отменен")
        await state.clear()
        return
    
    try:
        offer_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Неверный формат номера заявки. Введите число.\n"
            "Например: <code>123</code>\n\n"
            "Или отправьте /cancel для отмены.",
            parse_mode="HTML"
        )
        return
    
    # Получаем заявку с информацией о пользователе
    offer = await orm_get_offer_with_user_info(session, offer_id)
    
    if not offer:
        await message.answer(f"❌ Заявка №{offer_id} не найдена.")
        return
    
    # СТРОГАЯ ПРОВЕРКА ПРИНАДЛЕЖНОСТИ
    user_id = message.from_user.id
    service_providers = await orm_get_service_providers_by_user(session, user_id)
    
    # Проверяем, что пользователь является АКТИВНЫМ поставщиком услуг
    active_providers = [sp for sp in service_providers if sp.is_active]
    
    if not active_providers:
        await message.answer(
            "❌ У вас нет активных категорий услуг.\n"
            "Обратитесь к администратору для активации."
        )
        await state.clear()
        return
    
    # Проверяем, что заявка относится к ЖК и категории пользователя
    has_access = False
    user_jk_id = offer.user_jk.jk_id
    offer_category = offer.category
    
    for sp in active_providers:
        # Проверяем ЖК И категорию
        if sp.jk_id == user_jk_id and sp.category.value == offer_category:
            has_access = True
            break
    
    if not has_access:
        await message.answer(
            f"❌ <b>Нет доступа к заявке №{offer_id}</b>\n\n"
            f"Причины:\n"
            f"• Заявка не из вашего ЖК\n"
            f"• Категория заявки не входит в ваши обязанности\n"
            f"• Вы не являетесь активным поставщиком услуг\n\n"
            f"Вы можете управлять только заявками из ваших активных категорий.",
            parse_mode="HTML"
        )
        return
    
    # Определяем категорию для отображения
    try:
        from database.enums.offer_category_enum import OfferCategory
        category_enum = OfferCategory.from_string(offer.category)
        category_display = category_enum.display_name
        category_emoji = category_enum.emoji
    except:
        category_display = offer.category
        category_emoji = "📝"
    
    current_status = offer.status or OfferStatus.ACTIVE
    status_display = current_status.display_name
    status_emoji = current_status.emoji
    
    # Сохраняем ID заявки в состоянии
    await state.update_data(offer_id=offer_id)
    await state.set_state(ManageOfferStatus.select_status)
    
    await message.answer(
        f"📋 <b>Заявка №{offer.id}</b>\n\n"
        f"<b>ЖК:</b> {offer.user_jk.jk.name}\n"
        f"<b>Категория:</b> {category_display} {category_emoji}\n"
        f"<b>Название:</b> {offer.title}\n"
        f"<b>Описание:</b> {offer.description}\n\n"
        f"<b>Текущий статус:</b> {status_display} {status_emoji}\n\n"
        f"Выберите новый статус:",
        parse_mode="HTML",
        reply_markup=get_status_keyboard(current_status)
    )


@manage_offer_status_router.callback_query(
    StateFilter(ManageOfferStatus.select_status), 
    F.data.startswith("set_status:")
)
async def set_offer_status(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Установка нового статуса заявки."""
    new_status_value = callback.data.split(":")[1]
    new_status = OfferStatus(new_status_value)
    
    data = await state.get_data()
    offer_id = data.get("offer_id")
    
    if not offer_id:
        await callback.message.edit_text("❌ Ошибка: заявка не выбрана.")
        await callback.answer()
        await state.clear()
        return
    
    try:
        # Обновляем статус заявки
        offer, old_status = await orm_update_offer_status(session, offer_id, new_status)
        await session.commit()
        
        # Отправляем уведомление пользователю
        await notify_user_status_change(session, callback.bot, offer, old_status, new_status)
        
        await callback.message.edit_text(
            f"✅ <b>Статус заявки №{offer_id} успешно изменен!</b>\n\n"
            f"<b>Было:</b> {old_status.display_name} {old_status.emoji}\n"
            f"<b>Стало:</b> {new_status.display_name} {new_status.emoji}\n\n"
            f"Пользователь получил уведомление об изменении статуса.",
            parse_mode="HTML"
        )
        
        await callback.answer("Статус изменен!")
        await state.clear()
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при изменении статуса: {str(e)}")
        await callback.answer("Ошибка!")
        await state.clear()


@manage_offer_status_router.callback_query(
    StateFilter(ManageOfferStatus.select_status), 
    F.data == "cancel_status_change"
)
async def cancel_status_change(callback: CallbackQuery, state: FSMContext):
    """Отмена изменения статуса."""
    await callback.message.edit_text("❌ Изменение статуса отменено.")
    await callback.answer("Отменено")
    await state.clear()


@manage_offer_status_router.callback_query(F.data == "cancel_manage_status")
async def cancel_manage_status(callback: CallbackQuery, state: FSMContext):
    """Отмена управления статусом через кнопку"""
    await callback.message.edit_text(
        "❌ <b>Управление статусом отменено</b>",
        parse_mode="HTML"
    )
    await state.clear()
    await callback.answer("Отменено")


@manage_offer_status_router.message(StateFilter(ManageOfferStatus.select_offer), F.text.in_(["❌ Отмена", "/cancel", "/start"]))
async def cancel_offer_selection(message: Message, state: FSMContext):
    """Отмена выбора заявки через текстовые команды"""
    await message.answer(
        "❌ <b>Выбор заявки отменен</b>\n\n"
        "Для управления статусами заявок используйте команду из меню поставщика услуг.",
        parse_mode="HTML"
    )
    await state.clear()


@manage_offer_status_router.message(StateFilter(ManageOfferStatus.select_offer), Command("menu"))
async def return_to_menu_from_fsm(message: Message, state: FSMContext):
    """Возврат в главное меню из FSM"""
    from keyboards.reply import MAIN_KB
    
    await message.answer(
        "🏠 <b>Главное меню</b>\n\n"
        "Выбор заявки отменен.",
        parse_mode="HTML",
        reply_markup=MAIN_KB
    )
    await state.clear()
