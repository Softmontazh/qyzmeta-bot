# -*- coding: utf-8 -*-
# handlers/providers_view_handlers.py
"""
Обработчики для просмотра поставщиков услуг по категориям.
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.orm_jk_service_provider import orm_get_service_providers_by_jk_and_category, orm_get_service_provider_by_id
from database.models.orm_jk import orm_get_jk_by_id
from database.enums.offer_enums import OfferCategory
from keyboards.reply import get_providers_categories_kb, SERVICE_MANAGEMENT_KB
from keyboards.service_provider_keyboards import get_providers_by_category_keyboard, get_provider_actions_keyboard
from handlers.fsm.manage_service_providers_fsm import ManageServiceProviderStates
from filters.chat_types import IsAdmin

providers_view_router = Router()


@providers_view_router.message(F.text == "📋 Поставщики", IsAdmin())
async def handle_view_providers_button(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка нажатия кнопки 'Поставщики'."""
    data = await state.get_data()
    jk_id = data.get("selected_jk_id")
    
    if not jk_id:
        await message.answer("❌ ЖК не выбран. Используйте команду /manage_services")
        return
    
    # Получаем информацию о ЖК
    jk = await orm_get_jk_by_id(session, jk_id)
    
    await message.answer(
        f"🏢 <b>ЖК: {jk.name}</b>\n\n"
        "📋 <b>Просмотр поставщиков услуг</b>\n\n"
        "Выберите категорию для просмотра поставщиков:",
        parse_mode="HTML",
        reply_markup=get_providers_categories_kb()
    )


@providers_view_router.message(F.text.startswith("🔔 ") | F.text.startswith("📹 ") | F.text.startswith("⚡ ") | 
                              F.text.startswith("🚿 ") | F.text.startswith("🌳 ") | F.text.startswith("🔧 ") | 
                              F.text.startswith("📝 "), IsAdmin())
async def handle_category_selection_reply(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка выбора категории через reply-кнопку."""
    data = await state.get_data()
    jk_id = data.get("selected_jk_id")
    
    if not jk_id:
        await message.answer("❌ ЖК не выбран. Используйте команду /manage_services")
        return
    
    # Определяем категорию по тексту кнопки
    category_text = message.text
    category = None
    
    for cat in OfferCategory:
        if category_text.startswith(cat.emoji):
            category = cat
            break
    
    if not category:
        await message.answer("❌ Неизвестная категория")
        return
    
    # Сохраняем текущую категорию в состояние
    await state.update_data(current_category=category.value)
    
    # Получаем поставщиков по категории
    try:
        providers = await orm_get_service_providers_by_jk_and_category(session, jk_id, category.value)
    except Exception as e:
        print(f"ERROR: Ошибка при поиске поставщиков: {e}")
        await message.answer("❌ Ошибка при поиске поставщиков услуг.")
        return
    
    jk = await orm_get_jk_by_id(session, jk_id)
    
    # Проверяем результат
    if not providers or len(providers) == 0:
        await message.answer(
            f"🏢 <b>ЖК: {jk.name}</b>\n"
            f"📑 <b>Категория: {category.display_name}</b> {category.emoji}\n\n"
            "❌ Поставщики услуг не найдены для данной категории.\n\n"
            "💡 Используйте кнопку 'Добавить поставщика' для добавления.",
            parse_mode="HTML",
            reply_markup=get_providers_categories_kb()
        )
        return
    
    providers_text = (
        f"🏢 <b>ЖК: {jk.name}</b>\n"
        f"📑 <b>Категория: {category.display_name}</b> {category.emoji}\n\n"
        f"📋 <b>Найдено поставщиков: {len(providers)}</b>\n\n"
        "Выберите поставщика для просмотра подробной информации:"
    )
    
    await message.answer(
        providers_text,
        parse_mode="HTML",
        reply_markup=get_providers_by_category_keyboard(providers, category.value)
    )


@providers_view_router.message(F.text == "🔙 Назад", IsAdmin())
async def handle_back_to_management(message: Message, state: FSMContext, session: AsyncSession):
    """Возврат к управлению поставщиками."""
    data = await state.get_data()
    jk_id = data.get("selected_jk_id")
    
    if not jk_id:
        await message.answer("❌ ЖК не выбран. Используйте команду /manage_services")
        return
    
    jk = await orm_get_jk_by_id(session, jk_id)
    
    await message.answer(
        f"🏢 <b>ЖК: {jk.name}</b>\n\n"
        "🔧 <b>Управление поставщиками услуг</b>\n\n"
        "Используйте кнопки ниже для управления:",
        parse_mode="HTML",
        reply_markup=SERVICE_MANAGEMENT_KB
    )


@providers_view_router.callback_query(F.data.startswith("view_provider:"))
async def handle_view_provider_details(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Показ подробной информации о поставщике."""
    provider_id = int(callback.data.split(":")[1])
    
    # Получаем информацию о поставщике
    provider = await orm_get_service_provider_by_id(session, provider_id)
    if not provider:
        await callback.answer("❌ Поставщик не найден", show_alert=True)
        return
    
    # Получаем информацию о ЖК
    jk = await orm_get_jk_by_id(session, provider.jk_id)
    
    # Формируем подробную информацию
    status = "✅ Активен" if provider.is_active else "❌ Неактивен"
    notifications = "🔔 Включены" if provider.receives_notifications else "🔕 Отключены"
    
    details_text = (
        f"🏢 <b>ЖК: {jk.name}</b>\n"
        f"📑 <b>Категория:</b> {provider.category.display_name} {provider.category.emoji}\n\n"
        f"🏛️ <b>Организация:</b> {provider.organization_name}\n"
        f"👤 <b>Ответственный:</b> {provider.responsible_user_id}\n"
        f"📞 <b>Телефон:</b> {provider.contact_phone or 'не указан'}\n\n"
        f"📊 <b>Статус:</b> {status}\n"
        f"🔔 <b>Уведомления:</b> {notifications}\n"
        f"📅 <b>Создан:</b> {provider.created_at.strftime('%d.%m.%Y %H:%M')}"
    )
    
    await callback.message.edit_text(
        details_text,
        parse_mode="HTML",
        reply_markup=get_provider_actions_keyboard(provider_id)
    )
    await callback.answer()


@providers_view_router.callback_query(F.data.startswith("edit_provider:"))
async def handle_edit_provider_stub(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Заглушка для редактирования поставщика."""
    await callback.answer("🚧 Функция редактирования в разработке", show_alert=True)


@providers_view_router.callback_query(F.data.startswith("delete_provider:"))
async def handle_delete_provider_stub(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Заглушка для удаления поставщика."""
    await callback.answer("🚧 Функция удаления в разработке", show_alert=True)


@providers_view_router.callback_query(F.data == "back_to_categories")
async def handle_back_to_categories(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Возврат к выбору категорий."""
    data = await state.get_data()
    jk_id = data.get("selected_jk_id")
    
    if not jk_id:
        await callback.answer("❌ ЖК не выбран", show_alert=True)
        return
    
    jk = await orm_get_jk_by_id(session, jk_id)
    
    await callback.message.edit_text(
        f"🏢 <b>ЖК: {jk.name}</b>\n\n"
        "📋 <b>Просмотр поставщиков услуг</b>\n\n"
        "Выберите категорию для просмотра поставщиков:",
        parse_mode="HTML"
    )
    await callback.answer()


@providers_view_router.callback_query(F.data == "back_to_provider_list")
async def handle_back_to_provider_list(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Возврат к списку поставщиков текущей категории."""
    data = await state.get_data()
    jk_id = data.get("selected_jk_id")
    current_category_value = data.get("current_category")
    
    if not jk_id or not current_category_value:
        await callback.answer("❌ Данные не найдены", show_alert=True)
        return
    
    # Получаем категорию
    try:
        category = OfferCategory(current_category_value)
    except ValueError:
        await callback.answer("❌ Неизвестная категория", show_alert=True)
        return
    
    # Получаем поставщиков по категории
    providers = await orm_get_service_providers_by_jk_and_category(session, jk_id, category.value)
    jk = await orm_get_jk_by_id(session, jk_id)
    
    providers_text = (
        f"🏢 <b>ЖК: {jk.name}</b>\n"
        f"📑 <b>Категория: {category.display_name}</b> {category.emoji}\n\n"
        f"📋 <b>Найдено поставщиков: {len(providers)}</b>\n\n"
        "Выберите поставщика для просмотра подробной информации:"
    )
    
    await callback.message.edit_text(
        providers_text,
        parse_mode="HTML",
        reply_markup=get_providers_by_category_keyboard(providers, category.value)
    )
    await callback.answer()
