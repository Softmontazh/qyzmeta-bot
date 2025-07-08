# -*- coding: utf-8 -*-
# handlers/fsm/my_offers_fsm.py

from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from filters.chat_types import ChatTypeFilter
from database.models.orm_offer import (
    orm_get_offers_by_user_id,
    orm_archive_offer,
    orm_get_offer_by_id
)
from database.enums.offer_enums import OfferStatus
from database.enums.offer_category_enum import OfferCategory
from keyboards.inline import get_callback_btns


my_offers_router = Router()


class MyOffersStates(StatesGroup):
    viewing_offers = State()
    confirming_archive = State()


@my_offers_router.message(
    ChatTypeFilter(["private"]),
    F.text == "Мои заявки 📝"
)
async def my_offers_cmd(message: Message, session: AsyncSession, state: FSMContext):
    """Показать все заявки пользователя"""
    
    offers = await orm_get_offers_by_user_id(session, message.from_user.id)
    
    if not offers:
        await message.answer(
            "У вас пока нет заявок.\n"
            "Используйте кнопку '📝 Подать заявку' для создания новой заявки."
        )
        return
    
    # Группируем заявки по статусам
    active_offers = [o for o in offers if o.status != OfferStatus.ARCHIVED and o.status is not None]
    legacy_offers = [o for o in offers if o.status is None]  # Старые заявки без статуса
    archived_offers = [o for o in offers if o.status == OfferStatus.ARCHIVED]
    
    # Объединяем активные и legacy заявки
    all_active = active_offers + legacy_offers
    
    text = "📋 **Ваши заявки:**\n\n"
    
    if all_active:
        text += "🔔 **Активные заявки:**\n"
        for offer in all_active:
            # Получаем русское название категории
            category_display = OfferCategory.get_display_name(offer.category)
            status_display = OfferStatus.get_display_name(offer.status) if offer.status else "Не указан"
            
            text += (
                f"• {category_display}\n"
                f"  📝 {offer.description[:50]}{'...' if len(offer.description) > 50 else ''}\n"
                f"  📊 Статус: {status_display}\n"
                f"  📅 {offer.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
    
    if archived_offers:
        text += f"📦 **Архивные заявки:** {len(archived_offers)} шт.\n"
    
    # Создаем кнопки для управления заявками
    btns = {}
    if all_active:
        btns["🗂 Управлять заявками"] = "manage_offers"
    if archived_offers:
        btns["📦 Показать архив"] = "show_archived"
    btns["🔙 Назад"] = "back_to_main"
    
    await message.answer(
        text,
        reply_markup=get_callback_btns(btns=btns),
        parse_mode="Markdown"
    )
    await state.set_state(MyOffersStates.viewing_offers)


@my_offers_router.callback_query(
    StateFilter(MyOffersStates.viewing_offers, MyOffersStates.confirming_archive),
    F.data == "manage_offers"
)
async def manage_offers(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Показать активные заявки для управления"""
    
    offers = await orm_get_offers_by_user_id(session, callback.from_user.id)
    active_offers = [o for o in offers if o.status != OfferStatus.ARCHIVED and o.status is not None]
    legacy_offers = [o for o in offers if o.status is None]  # Старые заявки без статуса
    all_active = active_offers + legacy_offers
    
    if not all_active:
        await callback.answer("У вас нет активных заявок")
        return
    
    text = "🗂 **Управление заявками:**\n\n"
    text += "Выберите заявку для архивирования:\n\n"
    
    btns = {}
    for i, offer in enumerate(all_active, 1):
        category_display = OfferCategory.get_display_name(offer.category)
        btn_text = f"{i}. {category_display}"
        if len(btn_text) > 30:
            btn_text = btn_text[:27] + "..."
        btns[btn_text] = f"archive_offer_{offer.id}"
    
    btns["🔙 Назад"] = "back_to_my_offers"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_callback_btns(btns=btns),
        parse_mode="Markdown"
    )
    await state.set_state(MyOffersStates.viewing_offers)


@my_offers_router.callback_query(
    StateFilter(MyOffersStates.viewing_offers),
    F.data.startswith("archive_offer_")
)
async def confirm_archive_offer(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Подтверждение архивирования заявки"""
    
    offer_id = callback.data.replace("archive_offer_", "")
    
    try:
        offer_id = int(offer_id)
    except ValueError:
        await callback.answer("Ошибка: неверный ID заявки")
        return
    
    offer = await orm_get_offer_by_id(session, offer_id)
    
    if not offer or offer.user_id != callback.from_user.id:
        await callback.answer("Заявка не найдена или вам не принадлежит")
        return
    
    category_display = OfferCategory.get_display_name(offer.category)
    
    text = f"🗂 **Архивирование заявки**\n\n"
    text += f"**Категория:** {category_display}\n"
    text += f"**Описание:** {offer.description[:100]}{'...' if len(offer.description) > 100 else ''}\n\n"
    text += "⚠️ Вы уверены, что хотите переместить эту заявку в архив?\n"
    text += "Архивные заявки можно будет просмотреть, но не редактировать."
    
    btns = {
        "✅ Да, архивировать": f"confirm_archive_{offer_id}",
        "❌ Отменить": "manage_offers"
    }
    
    await callback.message.edit_text(
        text,
        reply_markup=get_callback_btns(btns=btns),
        parse_mode="Markdown"
    )
    await state.set_state(MyOffersStates.confirming_archive)


@my_offers_router.callback_query(
    StateFilter(MyOffersStates.confirming_archive),
    F.data.startswith("confirm_archive_")
)
async def archive_offer(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Архивировать заявку"""
    
    offer_id = callback.data.replace("confirm_archive_", "")
    
    try:
        offer_id = int(offer_id)
    except ValueError:
        await callback.answer("Ошибка: неверный ID заявки")
        return
    
    success = await orm_archive_offer(session, offer_id)
    
    if success:
        await callback.answer("✅ Заявка успешно архивирована")
        
        # Возвращаемся к списку заявок
        await my_offers_cmd(callback.message, session, state)
    else:
        await callback.answer("❌ Ошибка при архивировании заявки")


@my_offers_router.callback_query(
    StateFilter(MyOffersStates.viewing_offers),
    F.data == "show_archived"
)
async def show_archived_offers(callback: CallbackQuery, session: AsyncSession):
    """Показать архивные заявки"""
    
    offers = await orm_get_offers_by_user_id(session, callback.from_user.id)
    archived_offers = [o for o in offers if o.status == OfferStatus.ARCHIVED]
    
    if not archived_offers:
        await callback.answer("У вас нет архивных заявок")
        return
    
    text = "📦 **Архивные заявки:**\n\n"
    
    for i, offer in enumerate(archived_offers, 1):
        category_display = OfferCategory.get_display_name(offer.category)
        text += (
            f"{i}. {category_display}\n"
            f"   📝 {offer.description[:50]}{'...' if len(offer.description) > 50 else ''}\n"
            f"   📅 {offer.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        )
    
    btns = {"🔙 Назад": "back_to_my_offers"}
    
    await callback.message.edit_text(
        text,
        reply_markup=get_callback_btns(btns=btns),
        parse_mode="Markdown"
    )


@my_offers_router.callback_query(
    F.data.in_(["back_to_my_offers", "back_to_main"])
)
async def back_navigation(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Навигация назад"""
    
    if callback.data == "back_to_my_offers":
        await my_offers_cmd(callback.message, session, state)
    else:  # back_to_main
        await callback.message.edit_text(
            "Главное меню",
            reply_markup=None
        )
        await state.clear()


# Очистка состояния при выходе
@my_offers_router.message(
    StateFilter(MyOffersStates.viewing_offers, MyOffersStates.confirming_archive),
    F.text.in_(["🏠 Главная", "/start"])
)
async def cancel_my_offers(message: Message, state: FSMContext):
    """Отмена просмотра заявок и возврат в главное меню"""
    await state.clear()
    await message.answer("Возвращение в главное меню")
