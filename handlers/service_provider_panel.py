# -*- coding: utf-8 -*-
# handlers/service_provider_panel.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.orm_user import orm_get_user_by_id
from database.models.orm_jk_service_provider import orm_get_service_providers_by_user
from database.models.orm_offer import orm_get_service_provider_statistics
from database.enums.user_enums import UserRole
from keyboards.reply import MANAGE_OFFER_STATUS_KB, MAIN_KB

service_provider_panel_router = Router()


@service_provider_panel_router.message(Command("is_service"))
async def show_service_provider_panel(message: Message, session: AsyncSession):
    """Показать панель управления для поставщиков услуг"""
    user_id = message.from_user.id
    
    # Проверяем роль пользователя
    user = await orm_get_user_by_id(session, user_id)
    
    if not user or user.role != UserRole.SERVICE_PROVIDER:
        # Показываем кнопку подачи заявки БЕЗ проверки существующих заявок
        from database.models.orm_jk_service_provider import orm_get_user_service_provider_requests
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📝 Стать поставщиком услуг",
                        callback_data="become_service_provider"
                    )
                ]
            ]
        )
        
        await message.answer(
            "❌ <b>Доступ запрещен</b>\n\n"
            "Эта панель доступна только для поставщиков услуг.\n\n"
            "💡 Хотите стать поставщиком услуг?\n"
            "Подайте заявку на рассмотрение администратору.",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    # Для пользователей с ролью SERVICE_PROVIDER проверяем АКТИВНЫЕ записи
    service_providers = await orm_get_service_providers_by_user(session, user_id)
    active_providers = [sp for sp in service_providers if sp.is_active]
    
    if not active_providers:
        # Есть записи, но неактивные - ждем активации
        inactive_count = len([sp for sp in service_providers if not sp.is_active])
        
        if inactive_count > 0:
            await message.answer(
                f"⏳ <b>Ожидание активации</b>\n\n"
                f"У вас есть {inactive_count} заявка(и) на статус поставщика услуг, "
                f"но они еще не активированы администратором.\n\n"
                f"Дождитесь активации или обратитесь к администратору ЖК.",
                parse_mode="HTML"
            )
            return
        else:
            await message.answer(
                "⚠️ <b>Сервисы не найдены</b>\n\n"
                "У вас роль поставщика услуг, но нет назначенных категорий услуг.\n\n"
                "Обратитесь к администратору ЖК для назначения сервисов.",
                parse_mode="HTML"
            )
            return
    
    # Формируем приветственное сообщение
    jk_count = len(set(sp.jk_id for sp in active_providers))
    categories_count = len(active_providers)
    
    user_name = user.first_name
    if user.last_name:
        user_name += f" {user.last_name}"
    
    welcome_text = (
        f"🏛️ <b>Панель поставщика услуг</b>\n\n"
        f"👋 Добро пожаловать, <b>{user_name}</b>!\n\n"
        f"📊 <b>Ваши сервисы:</b>\n"
        f"• ЖК: {jk_count}\n"
        f"• Категорий услуг: {categories_count}\n\n"
        f"🔧 Выберите действие:"
    )
    
    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=MANAGE_OFFER_STATUS_KB
    )


@service_provider_panel_router.message(F.text == "Управление заявками 📋")
async def manage_offer_status_button(message: Message, session: AsyncSession, state: FSMContext):
    """Показать меню управления заявками по статусам"""
    # Проверяем роль
    user = await orm_get_user_by_id(session, message.from_user.id)
    if not user or user.role != UserRole.SERVICE_PROVIDER:
        await message.answer("❌ Доступ запрещен")
        return
    
    # Проверяем, является ли пользователь поставщиком услуг
    from database.models.orm_jk_service_provider import orm_get_service_providers_by_user
    user_id = message.from_user.id
    service_providers = await orm_get_service_providers_by_user(session, user_id)
    
    if not service_providers:
        await message.answer(
            "❌ У вас нет прав для управления заявками.\n"
            "Эта функция доступна только поставщикам услуг."
        )
        return
    
    # Создаем меню выбора статуса
    keyboard_buttons = [
        [InlineKeyboardButton(text="🆕 Активные заявки", callback_data="offers_status:active")],
        [InlineKeyboardButton(text="⏳ Заявки в работе", callback_data="offers_status:in_progress")], 
        [InlineKeyboardButton(text="❌ Отмененные", callback_data="offers_status:cancelled")],
        [InlineKeyboardButton(text="✅ Выполненные", callback_data="offers_status:completed")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(
        "� <b>Управление заявками</b>\n\n"
        "Выберите категорию заявок для просмотра:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@service_provider_panel_router.message(F.text == "Мои сервисы в ЖК 📝")
async def my_services_in_jk(message: Message, session: AsyncSession):
    """Показать список сервисов пользователя в разных ЖК"""
    user_id = message.from_user.id
    
    # Проверяем роль
    user = await orm_get_user_by_id(session, user_id)
    if not user or user.role != UserRole.SERVICE_PROVIDER:
        await message.answer("❌ Доступ запрещен")
        return
    
    service_providers = await orm_get_service_providers_by_user(session, user_id)
    
    if not service_providers:
        await message.answer("❌ У вас нет назначенных сервисов")
        return
    
    # Группируем по ЖК
    jk_services = {}
    for sp in service_providers:
        jk_name = sp.jk.name
        if jk_name not in jk_services:
            jk_services[jk_name] = []
        jk_services[jk_name].append(sp)
    
    text = f"🏢 <b>Ваши сервисы в ЖК</b>\n\n"
    
    for jk_name, services in jk_services.items():
        text += f"🏠 <b>{jk_name}</b>\n"
        
        for service in services:
            status_icon = "🟢" if service.is_active else "🔴"
            priority_stars = "⭐" * min(service.priority, 3)
            
            text += (
                f"  {status_icon} {service.category.display_name} {service.category.emoji}\n"
                f"    Приоритет: {priority_stars} ({service.priority})\n"
            )
            
            if service.organization_name:
                text += f"    Организация: {service.organization_name}\n"
                
            if service.contact_phone:
                text += f"    Телефон: {service.contact_phone}\n"
                
            notifications = "✅" if service.receives_notifications else "❌"
            text += f"    Уведомления: {notifications}\n"
            
            # Рабочее время
            if service.work_hours_start and service.work_hours_end:
                text += f"    Время: {service.work_hours_start}-{service.work_hours_end}\n"
            
            text += "\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    text += "💡 <i>Для изменения настроек обратитесь к администратору ЖК</i>"
    
    await message.answer(text, parse_mode="HTML")


@service_provider_panel_router.message(F.text == "Моя статистика 📊")  
async def my_statistics(message: Message, session: AsyncSession):
    """Показать статистику по заявкам поставщика услуг"""
    user_id = message.from_user.id
    
    # Проверяем роль
    user = await orm_get_user_by_id(session, user_id)
    if not user or user.role != UserRole.SERVICE_PROVIDER:
        await message.answer("❌ Доступ запрещен")
        return
    
    # Получаем статистику
    stats = await orm_get_service_provider_statistics(session, user_id)
    
    if not stats:
        await message.answer("📊 Статистика пока недоступна - нет обработанных заявок")
        return
    
    text = (
        f"📊 <b>Ваша статистика</b>\n\n"
        f"📋 <b>Заявки в ваших ЖК:</b>\n"
        f"• Всего: {stats['total_offers']}\n"
        f"• В работе: {stats['in_progress_offers']} ⏳\n"
        f"• Завершено: {stats['completed_offers']} ✅\n"
        f"• Отменено: {stats['cancelled_offers']} ❌\n\n"
        f"⏱️ <b>Время реагирования:</b>\n"
        f"• Среднее: {stats['avg_response_time_hours']} ч.\n\n"
        f"📈 <b>Эффективность:</b>\n"
        f"• Процент завершения: {stats['completion_rate']}%\n\n"
        f"🏢 <b>Ваши ЖК:</b>\n"
        f"{chr(10).join([f'• {jk}' for jk in stats['jk_list']]) if stats['jk_list'] else '• Нет привязанных ЖК'}"
    )
    
    await message.answer(text, parse_mode="HTML")


@service_provider_panel_router.message(F.text == "Выход из режима сервисника")
async def exit_service_mode(message: Message):
    """Выход из режима поставщика услуг"""
    await message.answer(
        "🏠 <b>Обычный режим</b>\n\n"
        "Вы вернулись в обычный режим пользователя.\n"
        "Для возврата в режим поставщика услуг используйте /is_service",
        parse_mode="HTML",
        reply_markup=MAIN_KB
    )


@service_provider_panel_router.callback_query(F.data.startswith("offers_status:"))
async def show_offers_by_status(callback: CallbackQuery, session: AsyncSession):
    """Показать заявки по выбранному статусу"""
    try:
        status_key = callback.data.split(":")[1]
        user_id = callback.from_user.id
        
        # Получаем поставщиков услуг для текущего пользователя
        from database.models.orm_jk_service_provider import orm_get_service_providers_by_user
        service_providers = await orm_get_service_providers_by_user(session, user_id)
        
        if not service_providers:
            await callback.answer("❌ У вас нет прав для просмотра заявок", show_alert=True)
            return
        
        # Получаем заявки по статусу для этого сервисника
        from database.models.orm_offer import orm_get_offers_by_status_for_provider
        
        status_mapping = {
            "active": "active",
            "in_progress": "in_progress", 
            "cancelled": "cancelled",
            "completed": "completed"
        }
        
        status_display = {
            "active": "🆕 Активные заявки",
            "in_progress": "⏳ Заявки в работе",
            "cancelled": "❌ Отмененные заявки", 
            "completed": "✅ Выполненные заявки"
        }
        
        offers = await orm_get_offers_by_status_for_provider(
            session, user_id, status_mapping[status_key], page=0, limit=2
        )
        
        if not offers:
            await callback.answer(f"📭 Нет заявок в категории '{status_display[status_key]}'", show_alert=True)
            return
        
        await show_offers_list(callback, offers, status_key, status_display[status_key], page=0)
        
    except Exception as e:
        print(f"Error in show_offers_by_status: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


async def show_offers_list(callback: CallbackQuery, offers, status_key: str, status_title: str, page: int = 0):
    """Показать список заявок с пагинацией"""
    text = f"📋 <b>{status_title}</b>\n\n"
    
    keyboard_buttons = []
    
    for i, offer in enumerate(offers):
        # Получаем информацию о ЖК и пользователе
        jk_name = offer.user_jk.jk.name if offer.user_jk and offer.user_jk.jk else "Неизвестный ЖК"
        apartment = offer.user_jk.appartment if offer.user_jk else "не указана"
        
        # Информация о пользователе
        user_info = "Неизвестный пользователь"
        if hasattr(offer, 'user') and offer.user:
            user_info = offer.user.first_name or "Пользователь"
            if offer.user.last_name:
                user_info += f" {offer.user.last_name}"
        
        text += (
            f"<b>Заявка #{offer.id}</b>\n"
            f"🏠 ЖК: {jk_name}\n"
            f"🚪 Квартира: {apartment}\n"
            f"👤 Заявитель: {user_info}\n"
            f"📝 {offer.title}\n"
            f"📄 {offer.description[:100]}{'...' if len(offer.description) > 100 else ''}\n"
            f"📅 {offer.created_at.strftime('%d.%m.%Y %H:%M') if offer.created_at else 'Дата неизвестна'}\n\n"
        )
        
        # Кнопка для детального просмотра заявки
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"📋 Заявка #{offer.id}",
                callback_data=f"offer_details:{offer.id}:{status_key}"
            )
        ])
    
    # Пагинация
    pagination_row = []
    if page > 0:
        pagination_row.append(
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"offers_page:{status_key}:{page-1}")
        )
    
    # Проверяем, есть ли еще заявки для следующей страницы
    if len(offers) == 2:  # Если получили максимальное количество, возможно есть еще
        pagination_row.append(
            InlineKeyboardButton(text="Вперед ▶️", callback_data=f"offers_page:{status_key}:{page+1}")
        )
    
    if pagination_row:
        keyboard_buttons.append(pagination_row)
    
    # Кнопка возврата к меню
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Назад к меню", callback_data="back_to_offers_menu")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@service_provider_panel_router.callback_query(F.data.startswith("offers_page:"))
async def handle_offers_pagination(callback: CallbackQuery, session: AsyncSession):
    """Обработка пагинации заявок"""
    try:
        _, status_key, page_str = callback.data.split(":")
        page = int(page_str)
        user_id = callback.from_user.id
        
        # Получаем заявки для новой страницы
        from database.models.orm_offer import orm_get_offers_by_status_for_provider
        
        status_mapping = {
            "active": "active",
            "in_progress": "in_progress",
            "cancelled": "cancelled", 
            "completed": "completed"
        }
        
        status_display = {
            "active": "🆕 Активные заявки",
            "in_progress": "⏳ Заявки в работе",
            "cancelled": "❌ Отмененные заявки",
            "completed": "✅ Выполненные заявки"
        }
        
        offers = await orm_get_offers_by_status_for_provider(
            session, user_id, status_mapping[status_key], page=page, limit=2
        )
        
        if not offers:
            await callback.answer("❌ Больше заявок нет", show_alert=True)
            return
        
        await show_offers_list(callback, offers, status_key, status_display[status_key], page)
        
    except Exception as e:
        print(f"Error in handle_offers_pagination: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@service_provider_panel_router.callback_query(F.data == "back_to_offers_menu")
async def back_to_offers_menu(callback: CallbackQuery, session: AsyncSession):
    """Возврат к меню выбора статуса заявок"""
    # Создаем меню выбора статуса
    keyboard_buttons = [
        [InlineKeyboardButton(text="🆕 Активные заявки", callback_data="offers_status:active")],
        [InlineKeyboardButton(text="⏳ Заявки в работе", callback_data="offers_status:in_progress")], 
        [InlineKeyboardButton(text="❌ Отмененные", callback_data="offers_status:cancelled")],
        [InlineKeyboardButton(text="✅ Выполненные", callback_data="offers_status:completed")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        "📋 <b>Управление заявками</b>\n\n"
        "Выберите категорию заявок для просмотра:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@service_provider_panel_router.callback_query(F.data.startswith("offer_details:"))
async def manage_single_offer(callback: CallbackQuery, session: AsyncSession):
    """Показать детальную информацию о заявке с возможностью изменения статуса"""
    try:
        parts = callback.data.split(":")
        offer_id = int(parts[1])
        status_key = parts[2] if len(parts) > 2 else "active"
        
        # Получаем подробную информацию о заявке
        from database.models.orm_offer import orm_get_offer_with_user_info
        offer = await orm_get_offer_with_user_info(session, offer_id)
        
        if not offer:
            await callback.answer("❌ Заявка не найдена", show_alert=True)
            return
        
        # Формируем детальную информацию
        jk_name = offer.user_jk.jk.name if offer.user_jk and offer.user_jk.jk else "Неизвестный ЖК"
        apartment = offer.user_jk.appartment if offer.user_jk else "не указана"
        
        # Информация о пользователе
        user_info = "Неизвестный пользователь"
        phone_info = "не указан"
        if hasattr(offer, 'user') and offer.user:
            user_info = offer.user.first_name or "Пользователь"
            if offer.user.last_name:
                user_info += f" {offer.user.last_name}"
            if offer.user.username:
                user_info += f" (@{offer.user.username})"
            phone_info = offer.user.phone or "не указан"
        
        text = (
            f"📋 <b>Заявка #{offer.id}</b>\n\n"
            f"🏠 <b>ЖК:</b> {jk_name}\n"
            f"🚪 <b>Квартира:</b> {apartment}\n"
            f"👤 <b>Заявитель:</b> {user_info}\n"
            f"📞 <b>Телефон:</b> {phone_info}\n\n"
            f"📝 <b>Название:</b> {offer.title}\n"
            f"📄 <b>Описание:</b> {offer.description}\n"
            f"📅 <b>Создана:</b> {offer.created_at.strftime('%d.%m.%Y %H:%M') if offer.created_at else 'Неизвестно'}\n"
            f"📊 <b>Статус:</b> {offer.status.display_name if offer.status else 'Неизвестно'} {offer.status.emoji if offer.status else ''}\n"
        )
        
        if offer.bus_media_id:
            text += f"\n📎 <b>Есть медиафайл</b>"
        
        # Создаем кнопки в зависимости от текущего статуса
        keyboard_buttons = []
        
        if offer.status.value == "active":
            keyboard_buttons.extend([
                [InlineKeyboardButton(text="⏳ Принять в работу", callback_data=f"change_status:{offer_id}:IN_PROGRESS:{status_key}")],
                [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"change_status:{offer_id}:CANCELLED:{status_key}")]
            ])
        elif offer.status.value == "in_progress":
            keyboard_buttons.extend([
                [InlineKeyboardButton(text="✅ Завершить", callback_data=f"change_status:{offer_id}:COMPLETED:{status_key}")],
                [InlineKeyboardButton(text="❌ Отменить", callback_data=f"change_status:{offer_id}:CANCELLED:{status_key}")]
            ])
        elif offer.status.value == "cancelled":
            keyboard_buttons.append([
                InlineKeyboardButton(text="🔄 Возобновить", callback_data=f"change_status:{offer_id}:IN_PROGRESS:{status_key}")
            ])
        
        # Кнопки связи с пользователем
        if hasattr(offer, 'user') and offer.user:
            keyboard_buttons.append([
                InlineKeyboardButton(text="📞 Связаться", url=f"tg://user?id={offer.user.user_id}")
            ])
        
        # Кнопка просмотра медиа, если есть
        if offer.bus_media_id:
            keyboard_buttons.append([
                InlineKeyboardButton(text="📎 Посмотреть медиа", callback_data=f"view_media:{offer_id}")
            ])
        
        # Кнопка возврата
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 К списку", callback_data=f"offers_status:{status_key}")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        print(f"Error in manage_single_offer: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@service_provider_panel_router.callback_query(F.data.startswith("change_status:"))
async def change_offer_status(callback: CallbackQuery, session: AsyncSession):
    """Изменение статуса заявки"""
    try:
        parts = callback.data.split(":")
        offer_id = int(parts[1])
        new_status_str = parts[2]
        status_key = parts[3] if len(parts) > 3 else "active"
        
        # Обновляем статус заявки
        from database.models.orm_offer import orm_update_offer_status
        from database.enums.offer_enums import OfferStatus
        
        # Преобразуем строку статуса в enum
        status_mapping = {
            "ACTIVE": OfferStatus.ACTIVE,
            "IN_PROGRESS": OfferStatus.IN_PROGRESS,
            "COMPLETED": OfferStatus.COMPLETED,
            "CANCELLED": OfferStatus.CANCELLED
        }
        
        new_status = status_mapping.get(new_status_str)
        if not new_status:
            await callback.answer("❌ Неизвестный статус", show_alert=True)
            return
            
        offer, old_status = await orm_update_offer_status(session, offer_id, new_status)
        await session.commit()
        
        # Уведомляем пользователя об изменении статуса
        from services.notification_service import notify_user_status_change
        await notify_user_status_change(session, callback.bot, offer, old_status, new_status)
        
        await callback.answer(f"✅ Статус изменен на: {new_status.display_name}")
        
        # Возвращаемся к детальному просмотру заявки
        await manage_single_offer(callback, session)
        
    except Exception as e:
        print(f"Error in change_offer_status: {e}")
        await callback.answer("❌ Ошибка при изменении статуса", show_alert=True)


@service_provider_panel_router.callback_query(F.data.startswith("view_media:"))
async def view_offer_media(callback: CallbackQuery, session: AsyncSession):
    """Показать медиафайл заявки"""
    try:
        offer_id = int(callback.data.split(":")[1])
        
        from database.models.orm_offer import orm_get_offer_by_id
        offer = await orm_get_offer_by_id(session, offer_id)
        
        if not offer or not offer.bus_media_id:
            await callback.answer("❌ Медиафайл не найден", show_alert=True)
            return
        
        try:
            # Пробуем отправить как фото
            await callback.bot.send_photo(
                chat_id=callback.from_user.id,
                photo=offer.bus_media_id,
                caption=f"📎 Медиафайл к заявке #{offer.id}"
            )
        except:
            try:
                # Если не фото, пробуем как видео
                await callback.bot.send_video(
                    chat_id=callback.from_user.id,
                    video=offer.bus_media_id,
                    caption=f"📎 Медиафайл к заявке #{offer.id}"
                )
            except:
                await callback.answer("❌ Не удалось отправить медиафайл", show_alert=True)
                return
        
        await callback.answer("📎 Медиафайл отправлен вам в личные сообщения")
        
    except Exception as e:
        print(f"Error in view_offer_media: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)
