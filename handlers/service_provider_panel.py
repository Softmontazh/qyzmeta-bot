# -*- coding: utf-8 -*-
# handlers/service_provider_panel.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
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
        await message.answer(
            "❌ <b>Доступ запрещен</b>\n\n"
            "Эта панель доступна только для поставщиков услуг.\n"
            "Если вы являетесь поставщиком услуг, обратитесь к администратору ЖК.",
            parse_mode="HTML"
        )
        return
    
    # Проверяем, есть ли у пользователя назначенные сервисы
    service_providers = await orm_get_service_providers_by_user(session, user_id)
    
    if not service_providers:
        await message.answer(
            "⚠️ <b>Сервисы не найдены</b>\n\n"
            "У вас роль поставщика услуг, но вы не назначены ответственным "
            "ни за одну категорию услуг.\n\n"
            "Обратитесь к администратору ЖК для назначения сервисов.",
            parse_mode="HTML"
        )
        return
    
    # Формируем приветственное сообщение
    jk_count = len(set(sp.jk_id for sp in service_providers))
    categories_count = len(service_providers)
    
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


@service_provider_panel_router.message(F.text == "Управление статусами заявок 📝")
async def manage_offer_status_button(message: Message, session: AsyncSession, state: FSMContext):
    """Обработчик кнопки управления статусами заявок"""
    # Проверяем роль
    user = await orm_get_user_by_id(session, message.from_user.id)
    if not user or user.role != UserRole.SERVICE_PROVIDER:
        await message.answer("❌ Доступ запрещен")
        return
    
    # Запускаем FSM управления статусами заявок
    from handlers.fsm.manage_offer_status_fsm import ManageOfferStatus
    from database.models.orm_jk_service_provider import orm_get_service_providers_by_user
    
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь поставщиком услуг
    service_providers = await orm_get_service_providers_by_user(session, user_id)
    
    if not service_providers:
        await message.answer(
            "❌ У вас нет прав для управления статусами заявок.\n"
            "Эта функция доступна только поставщикам услуг."
        )
        return
    
    await message.answer(
        "🔧 <b>Управление статусом заявки</b>\n\n"
        "Отправьте номер заявки для изменения её статуса.\n"
        "Например: <code>123</code>",
        parse_mode="HTML"
    )
    await state.set_state(ManageOfferStatus.select_offer)


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
