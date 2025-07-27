# keyboards/platform_role_keyboards.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from database.models.model_partner_application import PartnerApplication


def get_role_application_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения заявки"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_application"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_application")
    )
    
    return builder.as_markup()


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Панель администратора платформы"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="👥 Управление пользователями", callback_data="admin_users"),
        InlineKeyboardButton(text="📊 Статистика платформы", callback_data="admin_stats")
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Настройки системы", callback_data="admin_settings"),
        InlineKeyboardButton(text="📋 Логи системы", callback_data="admin_logs")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_partner_panel_keyboard() -> InlineKeyboardMarkup:
    """Панель партнера"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🏢 Мои ЖК", callback_data="partner_jks"),
        InlineKeyboardButton(text="📈 Аналитика", callback_data="partner_analytics")
    )
    builder.row(
        InlineKeyboardButton(text="🛠️ Инструменты", callback_data="partner_tools"),
        InlineKeyboardButton(text="📞 Поддержка", callback_data="partner_support")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_moderator_panel_keyboard() -> InlineKeyboardMarkup:
    """Панель модератора"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🔍 Модерация контента", callback_data="mod_content"),
        InlineKeyboardButton(text="📝 Жалобы", callback_data="mod_reports")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика модерации", callback_data="mod_stats"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="mod_settings")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_role_request_keyboard(role: str) -> InlineKeyboardMarkup:
    """Клавиатура для запроса роли"""
    builder = InlineKeyboardBuilder()
    
    # Преобразуем роль в верхний регистр для соответствия UserRole
    role_mapping = {
        "partner": "PARTNER",
        "admin": "ADMIN", 
        "moderator": "MODERATOR",
        "manager": "MANAGER",
        "support": "SUPPORT"
    }
    
    role_upper = role_mapping.get(role.lower(), role.upper())
    
    builder.row(
        InlineKeyboardButton(
            text="📝 Подать заявку", 
            callback_data=f"apply_for_role:{role_upper}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_creator_moderation_keyboard() -> InlineKeyboardMarkup:
    """Панель создателя с кнопкой модерации заявок"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📋 Заявки на партнерство", callback_data="view_applications")
    )
    builder.row(
        InlineKeyboardButton(text="👑 Панель создателя", callback_data="creator_panel")
    )
    
    return builder.as_markup()


def get_applications_list_keyboard(applications: List["PartnerApplication"]) -> InlineKeyboardMarkup:
    """Клавиатура со списком заявок"""
    builder = InlineKeyboardBuilder()
    
    for app in applications:
        role_emoji = {
            "UserRole.ADMIN": "🛡️",
            "UserRole.PARTNER": "🤝", 
            "UserRole.MODERATOR": "🛡️"
        }
        emoji = role_emoji.get(str(app.requested_role), "👤")
        
        builder.row(
            InlineKeyboardButton(
                text=f"{emoji} #{app.id} - {app.full_name}",
                callback_data=f"view_app_{app.id}"
            )
        )
    
    # Кнопки управления (только если есть заявки)
    if applications:
        builder.row(
            InlineKeyboardButton(text="🔄 Обновить", callback_data="view_applications"),
            InlineKeyboardButton(text="❌ Закрыть", callback_data="close_applications")
        )
    
    return builder.as_markup()


def get_application_actions_keyboard(app_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для действий с заявкой"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{app_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{app_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 К списку", callback_data="view_applications")
    )
    
    return builder.as_markup()
