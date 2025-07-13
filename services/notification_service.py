# -*- coding: utf-8 -*-
# services/notification_service.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.model_user_jk import UserJK
from database.models.orm_jk_service_provider import orm_get_service_provider_by_category
from database.models.orm_jk import orm_get_jk_by_id
from database.enums.offer_category_enum import OfferCategory
from database.enums.offer_enums import OfferStatus


async def notify_service_provider(session: AsyncSession, bot, offer, jk_data, user_jk_data, user_data, category: str):
    """Уведомить поставщика(ов) услуг о новой заявке с учетом приоритетов
    
    Args:
        session: Сессия базы данных
        bot: Экземпляр бота
        offer: Объект заявки
        jk_data: Объект JK из state
        user_jk_data: Объект UserJK из state  
        user_data: Объект User из state
        category: Категория заявки
    """
    from database.enums.offer_category_enum import OfferCategory
    from database.models.orm_jk_service_provider import orm_get_service_providers_by_category_and_jk
    
    try:
        category_enum = OfferCategory.from_string(category)
        jk_id = jk_data.id
        
        # Получаем всех поставщиков для этой категории (отсортированных по приоритету)
        service_providers = await orm_get_service_providers_by_category_and_jk(
            session, jk_id, category_enum
        )
        
        if not service_providers:
            print(f"❌ Нет поставщиков услуг для категории {category} в ЖК {jk_id}")
            return
        
        # Находим наивысший приоритет (минимальное значение)
        highest_priority = min(provider.priority for provider in service_providers)
        
        # Отбираем всех поставщиков с наивысшим приоритетом
        priority_providers = [
            provider for provider in service_providers 
            if provider.priority == highest_priority
        ]
        
        print(f"📋 Отправка уведомлений {len(priority_providers)} поставщикам с приоритетом {highest_priority}")
        
        # Отправляем уведомления всем поставщикам с наивысшим приоритетом
        for service_provider in priority_providers:
            await send_notification_to_provider(
                bot, service_provider, offer, jk_data, user_jk_data, user_data, category_enum
            )
            
    except Exception as e:
        print(f"❌ Ошибка при отправке уведомления поставщику услуг: {e}")
        
        
        print(f"✅ Все уведомления отправлены!")
        
    except Exception as e:
        print(f"❌ Ошибка при отправке уведомления поставщику услуг: {e}")


async def send_notification_to_provider(bot, service_provider, offer, jk_data, user_jk_data, user_data, category_enum):
    """Отправка уведомления конкретному поставщику услуг"""
    # Формируем информацию о пользователе
    user_info = user_data.first_name or "Неизвестно"
    if user_data.last_name:
        user_info += f" {user_data.last_name}"
    if user_data.username:
        user_info += f" (@{user_data.username})"
        
    # Формируем контактную информацию из переданных данных
    contact_info = user_data.phone or "не указан"
    
    # Формируем информацию о квартире из переданных данных
    apartment_info = user_jk_data.appartment or "не указана"
    
    # Формируем сообщение
    notification_text = (
        f"🔔 <b>Новая заявка!</b>\n\n"
        f"<b>ЖК:</b> {jk_data.name}\n"
        f"<b>Квартира:</b> {apartment_info}\n"
        f"<b>Заявитель:</b> {user_info}\n"
        f"📞 <b>Телефон заявителя:</b> {contact_info}\n\n"
        f"<b>Категория:</b> {category_enum.display_name} {category_enum.emoji}\n"
        f"<b>Заявка №:</b> {offer.id}\n"
        f"<b>Название:</b> {offer.title}\n"
        f"<b>Описание:</b> {offer.description}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Для организации:</b> {service_provider.organization_name}\n"
        f"📞 <b>Контакт организации:</b> {service_provider.contact_phone or 'не указан'}"
    )
    
    # Создаем клавиатуру с кнопками действий
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⏳ Принять в работу", 
                callback_data=f"offer_status:{offer.id}:in_progress"
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Выполнено", 
                callback_data=f"offer_status:{offer.id}:completed"
            ),
            InlineKeyboardButton(
                text="❌ Отменить", 
                callback_data=f"offer_status:{offer.id}:cancelled"
            )
        ],
        [
            InlineKeyboardButton(
                text="📞 Связаться", 
                url=f"tg://user?id={user_data.user_id}"
            ),
            InlineKeyboardButton(
                text="📋 Управление", 
                callback_data=f"manage_offer:{offer.id}"
            )
        ]
    ])

    try:
        await bot.send_message(
            chat_id=service_provider.responsible_user_id,
            text=notification_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        print(f"✅ Уведомление отправлено поставщику {service_provider.responsible_user_id} ({service_provider.organization_name})")
        
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления поставщику {service_provider.responsible_user_id}: {e}")


async def notify_user_status_change(session: AsyncSession, bot, offer, old_status: OfferStatus, new_status: OfferStatus):
    """Уведомить пользователя об изменении статуса его заявки"""
    try:
        # Получаем информацию о пользователе и ЖК
        from database.models.model_user import User
        result = await session.execute(
            select(UserJK, User).join(User, UserJK.user_id == User.user_id).where(UserJK.id == offer.user_jk_id)
        )
        row = result.first()
        
        if not row:
            print(f"⚠️ Пользователь для заявки #{offer.id} не найден")
            return
            
        user_jk, user = row
        
        # Получаем информацию о ЖК
        jk = await orm_get_jk_by_id(session, user_jk.jk_id)
        jk_name = jk.name if jk else f"ЖК #{user_jk.jk_id}"
        
        # Определяем категорию
        try:
            category_enum = OfferCategory.from_string(offer.category)
            category_display = OfferCategory.get_display_name(category_enum)
            category_emoji = OfferCategory.get_emoji(category_enum)
        except:
            category_display = offer.category
            category_emoji = "📝"
        
        # Формируем сообщение в зависимости от нового статуса
        if new_status == OfferStatus.IN_PROGRESS:
            title = f"⏳ <b>Заявка принята в работу!</b>"
            message_text = (
                f"{title}\n\n"
                f"<b>Заявка №:</b> {offer.id}\n"
                f"<b>ЖК:</b> {jk_name}\n"
                f"<b>Категория:</b> {category_display} {category_emoji}\n"
                f"<b>Название:</b> {offer.title}\n\n"
                f"🔧 Ваша заявка принята в работу и скоро будет выполнена!"
            )
        elif new_status == OfferStatus.COMPLETED:
            title = f"✅ <b>Заявка выполнена!</b>"
            message_text = (
                f"{title}\n\n"
                f"<b>Заявка №:</b> {offer.id}\n"
                f"<b>ЖК:</b> {jk_name}\n"
                f"<b>Категория:</b> {category_display} {category_emoji}\n"
                f"<b>Название:</b> {offer.title}\n\n"
                f"🎉 Ваша заявка успешно выполнена! Спасибо за обращение."
            )
        elif new_status == OfferStatus.CANCELLED:
            title = f"❌ <b>Заявка отменена</b>"
            message_text = (
                f"{title}\n\n"
                f"<b>Заявка №:</b> {offer.id}\n"
                f"<b>ЖК:</b> {jk_name}\n"
                f"<b>Категория:</b> {category_display} {category_emoji}\n"
                f"<b>Название:</b> {offer.title}\n\n"
                f"ℹ️ Ваша заявка была отменена. При необходимости создайте новую заявку."
            )
        elif new_status == OfferStatus.ARCHIVED:
            title = f"📦 <b>Заявка архивирована</b>"
            message_text = (
                f"{title}\n\n"
                f"<b>Заявка №:</b> {offer.id}\n"
                f"<b>ЖК:</b> {jk_name}\n"
                f"<b>Категория:</b> {category_display} {category_emoji}\n"
                f"<b>Название:</b> {offer.title}\n\n"
                f"📦 Ваша заявка перемещена в архив."
            )
        else:
            # Общее уведомление для других статусов
            title = f"🔄 <b>Статус заявки изменен</b>"
            message_text = (
                f"{title}\n\n"
                f"<b>Заявка №:</b> {offer.id}\n"
                f"<b>ЖК:</b> {jk_name}\n"
                f"<b>Категория:</b> {category_display} {category_emoji}\n"
                f"<b>Название:</b> {offer.title}\n\n"
                f"<b>Новый статус:</b> {new_status.display_name} {new_status.emoji}"
            )
        
        # Отправляем уведомление пользователю
        await bot.send_message(
            chat_id=user.user_id,
            text=message_text,
            parse_mode="HTML"
        )
        
        print(f"✅ Уведомление об изменении статуса отправлено пользователю {user.first_name} (user_id: {user.user_id})")
        
    except Exception as e:
        print(f"❌ Ошибка при отправке уведомления пользователю об изменении статуса: {e}")
