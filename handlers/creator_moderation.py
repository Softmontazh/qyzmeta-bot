# handlers/creator_moderation.py

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
import os

from database.models.orm_partner_application import (
    orm_get_pending_applications,
    orm_get_application_by_id,
    orm_approve_application,
    orm_reject_application
)
from keyboards.platform_role_keyboards import (
    get_applications_list_keyboard,
    get_application_actions_keyboard,
    get_creator_moderation_keyboard
)

# Создаем роутер
router = Router()


def is_creator_by_environment(user_id: int) -> bool:
    """Проверяет, является ли пользователь создателем через переменную окружения"""
    creator_ids = os.getenv("CREATOR_ID")
    if not creator_ids:
        return False
    
    creator_id_list = [id_str.strip() for id_str in creator_ids.split(",")]
    return str(user_id) in creator_id_list


@router.callback_query(F.data == "view_applications")
async def view_applications(callback: CallbackQuery, session: AsyncSession):
    """Просмотр списка заявок на роли"""
    if not is_creator_by_environment(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    applications = await orm_get_pending_applications(session)
    
    if applications:
        text = f"📋 <b>Заявки на роли</b>\n\nВсего заявок: {len(applications)}\n\nВыберите заявку для просмотра:"
    else:
        text = "📭 <b>Нет новых заявок</b>\n\nВсе заявки обработаны."
    
    keyboard = get_applications_list_keyboard(applications)
    
    try:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    except Exception:
        await callback.message.answer(
            text,
            parse_mode="HTML", 
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("view_app_"))
async def view_application_details(callback: CallbackQuery, session: AsyncSession):
    """Просмотр деталей заявки"""
    if not is_creator_by_environment(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    app_id = int(callback.data.split("_")[-1])
    application = await orm_get_application_by_id(session, app_id)
    
    if not application:
        await callback.answer("❌ Заявка не найдена", show_alert=True)
        return
    
    role_names = {
        "UserRole.ADMIN": "🛡️ Администратор",
        "UserRole.PARTNER": "🤝 Партнер",
        "UserRole.MODERATOR": "🛡️ Модератор"
    }
    
    role_name = role_names.get(str(application.requested_role), "👤 Неизвестно")
    
    text = (
        f"📋 <b>Заявка #{application.id}</b>\n\n"
        f"👤 <b>Пользователь:</b> {application.user_id}\n"
        f"🎯 <b>Роль:</b> {role_name}\n"
        f"📛 <b>ФИО:</b> {application.full_name}\n"
        f"🏢 <b>Компания:</b> {application.company}\n"
        f"📞 <b>Телефон:</b> {application.phone}\n"
        f"📅 <b>Дата подачи:</b> {application.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"📝 <b>Цель получения роли:</b>\n{application.purpose}\n\n"
        f"⏳ <b>Статус:</b> {application.status}"
    )
    
    keyboard = get_application_actions_keyboard(app_id)
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("approve_"))
async def approve_application(callback: CallbackQuery, session: AsyncSession):
    """Одобрение заявки"""
    if not is_creator_by_environment(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    app_id = int(callback.data.split("_")[-1])
    
    success = await orm_approve_application(session, app_id)
    
    if success:
        await callback.message.edit_text(
            "✅ <b>Заявка одобрена!</b>\n\n"
            f"Заявка #{app_id} успешно одобрена.\n"
            "Пользователю назначена запрашиваемая роль.",
            parse_mode="HTML",
            reply_markup=get_creator_moderation_keyboard()
        )
        await callback.answer("✅ Заявка одобрена")
    else:
        await callback.answer("❌ Ошибка при одобрении заявки", show_alert=True)


@router.callback_query(F.data.startswith("reject_"))
async def reject_application(callback: CallbackQuery, session: AsyncSession):
    """Отклонение заявки"""
    if not is_creator_by_environment(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    app_id = int(callback.data.split("_")[-1])
    
    success = await orm_reject_application(session, app_id)
    
    if success:
        await callback.message.edit_text(
            "❌ <b>Заявка отклонена!</b>\n\n"
            f"Заявка #{app_id} отклонена.\n"
            "Пользователь получит уведомление об отказе.",
            parse_mode="HTML",
            reply_markup=get_creator_moderation_keyboard()
        )
        await callback.answer("❌ Заявка отклонена")
    else:
        await callback.answer("❌ Ошибка при отклонении заявки", show_alert=True)


@router.callback_query(F.data == "no_apps")
async def no_applications_handler(callback: CallbackQuery):
    """Обработчик для пустого списка заявок"""
    await callback.answer("📭 Нет заявок для обработки")


@router.callback_query(F.data == "creator_panel")
async def creator_panel_handler(callback: CallbackQuery):
    """Возврат к панели создателя"""
    if not is_creator_by_environment(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    await callback.message.edit_text(
        "👑 <b>Панель создателя</b>\n\n"
        "Добро пожаловать в панель управления системой ролей.\n"
        "Выберите необходимое действие:",
        parse_mode="HTML",
        reply_markup=get_creator_moderation_keyboard()
    )
    await callback.answer()
