# -*- coding: utf-8 -*-
# handlers/offer_status_handlers.py

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F, Router
from sqlalchemy.ext.asyncio import AsyncSession

from database.enums.offer_enums import OfferStatus
from database.enums.offer_category_enum import OfferCategory
from services.notification_service import notify_user_status_change

offer_status_router = Router()


def get_status_keyboard_for_offer(offer_id: int, current_status: OfferStatus) -> InlineKeyboardMarkup:
    """Создает клавиатуру со статусами для заявки (исключая текущий)."""
    buttons = []
    
    # Добавляем кнопки только для возможных переходов
    if current_status != OfferStatus.IN_PROGRESS:
        buttons.append([
            InlineKeyboardButton(
                text="⏳ Принять в работу", 
                callback_data=f"offer_status:{offer_id}:in_progress"
            )
        ])
    
    if current_status != OfferStatus.COMPLETED:
        buttons.append([
            InlineKeyboardButton(
                text="✅ Выполнено", 
                callback_data=f"offer_status:{offer_id}:completed"
            )
        ])
    
    if current_status != OfferStatus.CANCELLED:
        buttons.append([
            InlineKeyboardButton(
                text="❌ Отменить", 
                callback_data=f"offer_status:{offer_id}:cancelled"
            )
        ])
    
    # Кнопка архивирования (всегда доступна)
    if current_status != OfferStatus.ARCHIVED:
        buttons.append([
            InlineKeyboardButton(
                text="📦 Архивировать", 
                callback_data=f"offer_status:{offer_id}:archived"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@offer_status_router.callback_query(F.data.startswith("offer_status:"))
async def handle_offer_status_change(callback: CallbackQuery, session: AsyncSession):
    """Обработка изменения статуса заявки через кнопки в уведомлении."""
    try:
        # Парсим данные из callback
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer("❌ Ошибка в данных кнопки", show_alert=True)
            return
            
        offer_id = int(parts[1])
        status_value = parts[2]
        
        # Определяем новый статус
        status_mapping = {
            "in_progress": OfferStatus.IN_PROGRESS,
            "completed": OfferStatus.COMPLETED,
            "cancelled": OfferStatus.CANCELLED,
            "archived": OfferStatus.ARCHIVED
        }
        
        new_status = status_mapping.get(status_value)
        if not new_status:
            await callback.answer("❌ Неизвестный статус", show_alert=True)
            return
        
        # Проверяем права доступа
        user_id = callback.from_user.id
        from database.models.orm_jk_service_provider import orm_get_service_providers_by_user
        service_providers = await orm_get_service_providers_by_user(session, user_id)
        
        if not service_providers:
            await callback.answer(
                "❌ У вас нет прав для изменения статуса заявок", 
                show_alert=True
            )
            return
        
        # Получаем заявку
        from database.models.orm_offer import orm_update_offer_status, orm_get_offer_with_user_info
        offer = await orm_get_offer_with_user_info(session, offer_id)
        
        if not offer:
            await callback.answer("❌ Заявка не найдена", show_alert=True)
            return
        
        # Проверяем, что пользователь имеет право управлять этой заявкой
        has_access = False
        for sp in service_providers:
            if sp.jk_id == offer.user_jk.jk_id:
                has_access = True
                break
        
        if not has_access:
            await callback.answer(
                "❌ У вас нет прав для управления этой заявкой", 
                show_alert=True
            )
            return
        
        # Обновляем статус
        updated_offer, old_status = await orm_update_offer_status(session, offer_id, new_status)
        await session.commit()
        
        # Отправляем уведомление пользователю
        await notify_user_status_change(session, callback.bot, updated_offer, old_status, new_status)
        
        # Обновляем сообщение с уведомлением
        status_text = {
            OfferStatus.IN_PROGRESS: "⏳ ПРИНЯТА В РАБОТУ",
            OfferStatus.COMPLETED: "✅ ВЫПОЛНЕНА", 
            OfferStatus.CANCELLED: "❌ ОТМЕНЕНА",
            OfferStatus.ARCHIVED: "📦 АРХИВИРОВАНА"
        }
        
        current_text = callback.message.text
        updated_text = f"{current_text}\n\n🔄 <b>СТАТУС: {status_text.get(new_status, new_status.display_name.upper())}</b>"
        
        # Создаем новую клавиатуру с оставшимися опциями
        new_keyboard = None
        if new_status not in [OfferStatus.COMPLETED, OfferStatus.ARCHIVED]:
            new_keyboard = get_status_keyboard_for_offer(offer_id, new_status)
        
        # Обновляем сообщение
        await callback.message.edit_text(
            text=updated_text,
            parse_mode="HTML",
            reply_markup=new_keyboard
        )
        
        await callback.answer(f"✅ Статус изменен на: {new_status.display_name}")
        
    except Exception as e:
        print(f"❌ Ошибка при изменении статуса через кнопку: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@offer_status_router.callback_query(F.data.startswith("manage_offer:"))
async def handle_manage_offer(callback: CallbackQuery, session: AsyncSession):
    """Обработка управления заявкой - показать текущий статус и доступные действия."""
    try:
        offer_id = int(callback.data.split(":")[1])
        
        # Проверяем права доступа
        user_id = callback.from_user.id
        from database.models.orm_jk_service_provider import orm_get_service_providers_by_user
        service_providers = await orm_get_service_providers_by_user(session, user_id)
        
        if not service_providers:
            await callback.answer("❌ У вас нет прав для управления заявками", show_alert=True)
            return
        
        # Получаем заявку
        from database.models.orm_offer import orm_get_offer_with_user_info
        offer = await orm_get_offer_with_user_info(session, offer_id)
        
        if not offer:
            await callback.answer("❌ Заявка не найдена", show_alert=True)
            return
        
        # Проверяем права на эту конкретную заявку
        has_access = False
        for sp in service_providers:
            if sp.jk_id == offer.user_jk.jk_id:
                has_access = True
                break
        
        if not has_access:
            await callback.answer("❌ У вас нет прав для управления этой заявкой", show_alert=True)
            return
        
        # Определяем категорию
        try:
            category_enum = OfferCategory.from_string(offer.category)
            category_display = OfferCategory.get_display_name(category_enum)
            category_emoji = OfferCategory.get_emoji(category_enum)
        except:
            category_display = offer.category
            category_emoji = "📝"
        
        current_status = offer.status or OfferStatus.ACTIVE
        
        # Формируем сообщение с информацией о заявке
        manage_text = (
            f"📋 <b>Управление заявкой №{offer.id}</b>\n\n"
            f"<b>ЖК:</b> {offer.user_jk.jk.name}\n"
            f"<b>Категория:</b> {category_display} {category_emoji}\n"
            f"<b>Название:</b> {offer.title}\n"
            f"<b>Описание:</b> {offer.description}\n\n"
            f"<b>Текущий статус:</b> {current_status.display_name} {current_status.emoji}\n\n"
            f"Выберите действие:"
        )
        
        # Создаем клавиатуру с доступными статусами
        keyboard = get_status_keyboard_for_offer(offer_id, current_status)
        
        await callback.message.edit_text(
            text=manage_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        await callback.answer()
        
    except Exception as e:
        print(f"❌ Ошибка при управлении заявкой: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)
