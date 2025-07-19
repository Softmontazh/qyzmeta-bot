# -*- coding: utf-8 -*-
# handlers/offer_media_handlers.py
"""
Обработчики для работы с медиафайлами заявок через BUS систему.
"""

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.orm_offer import orm_get_offer_by_id
from services.bus_service import bus_service

offer_media_router = Router()


@offer_media_router.callback_query(F.data.startswith("show_offer_media:"))
async def show_offer_media(callback: CallbackQuery, session: AsyncSession):
    """Показать медиафайлы заявки через BUS систему."""
    try:
        offer_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Неверный ID заявки", show_alert=True)
        return
    
    # Получаем заявку
    offer = await orm_get_offer_by_id(session, offer_id)
    if not offer:
        await callback.answer("❌ Заявка не найдена", show_alert=True)
        return
    
    # Проверяем наличие медиа
    if not offer.bus_media_id:
        await callback.answer("📄 К этой заявке не прикреплены медиафайлы", show_alert=True)
        return
    
    # Отправляем медиа по bus_media_id
    caption = (
        f"📸 <b>Медиафайл к заявке #{offer.id}</b>\n\n"
        f"<b>Категория:</b> {offer.category}\n"
        f"<b>Название:</b> {offer.title}\n"
        f"<b>Описание:</b> {offer.description[:100]}{'...' if len(offer.description) > 100 else ''}"
    )
    
    try:
        # Пробуем отправить как фото
        await callback.bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=offer.bus_media_id,
            caption=caption,
            parse_mode="HTML"
        )
        await callback.answer("✅ Медиафайл отправлен")
    except Exception as photo_error:
        try:
            # Если не фото, пробуем как видео
            await callback.bot.send_video(
                chat_id=callback.message.chat.id,
                video=offer.bus_media_id,
                caption=caption,
                parse_mode="HTML"
            )
            await callback.answer("✅ Медиафайл отправлен")
        except Exception as video_error:
            print(f"Error sending BUS media {offer.bus_media_id}: photo_error={photo_error}, video_error={video_error}")
            await callback.answer("❌ Ошибка отправки медиафайла", show_alert=True)
