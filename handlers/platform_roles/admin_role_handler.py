# handlers/platform_roles/admin_role_handler.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.orm_user import orm_get_user_by_telegram_id
from database.enums.user_enums import UserRole

# Создаем роутер
router = Router()


@router.message(Command("is_admin"))
async def handle_is_admin_command(message: Message, session: AsyncSession):
    """Обработка команды /is_admin"""
    user = await orm_get_user_by_telegram_id(session, message.from_user.id)
    
    if user and user.role == UserRole.ADMIN:
        # У пользователя есть роль админа - показываем панель
        await message.answer(
            "🛡️ <b>Панель администратора платформы</b>\n\n"
            "Добро пожаловать в панель управления!\n"
            "Выберите необходимое действие:",
            parse_mode="HTML",
            reply_markup=get_admin_panel_keyboard()
        )
    else:
        # Роли нет - предлагаем подать заявку
        await message.answer(
            "🛡️ <b>Роль администратора</b>\n\n"
            "❌ У вас нет роли администратора платформы.\n\n"
            "📝 <b>Для получения роли необходимо:</b>\n"
            "• Подать заявку через форму\n"
            "• Указать цель использования прав\n"
            "• Дождаться одобрения создателем\n\n"
            "💡 Роль администратора дает доступ к:\n"
            "• Управлению пользователями платформы\n"
            "• Системной аналитике\n"
            "• Настройкам платформы",
            parse_mode="HTML",
            reply_markup=get_role_request_keyboard("admin")
        )


@router.callback_query(F.data == "admin_users")
async def handle_admin_users(callback: CallbackQuery):
    """Управление пользователями"""
    await callback.message.edit_text(
        "👥 <b>Управление пользователями</b>\n\n"
        "🚧 Функция в разработке\n\n"
        "Здесь будет:\n"
        "• Список всех пользователей\n"
        "• Поиск по критериям\n"
        "• Управление ролями\n"
        "• Статистика активности",
        parse_mode="HTML",
        reply_markup=get_admin_panel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def handle_admin_stats(callback: CallbackQuery):
    """Статистика платформы"""
    await callback.message.edit_text(
        "📊 <b>Статистика платформы</b>\n\n"
        "🚧 Функция в разработке\n\n"
        "Здесь будет:\n"
        "• Общая статистика пользователей\n"
        "• Активность по ЖК\n"
        "• Статистика заявок\n"
        "• Графики и отчеты",
        parse_mode="HTML",
        reply_markup=get_admin_panel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_settings")
async def handle_admin_settings(callback: CallbackQuery):
    """Настройки системы"""
    await callback.message.edit_text(
        "⚙️ <b>Настройки системы</b>\n\n"
        "🚧 Функция в разработке\n\n"
        "Здесь будет:\n"
        "• Системные параметры\n"
        "• Настройки уведомлений\n"
        "• Ограничения и лимиты\n"
        "• Конфигурация модулей",
        parse_mode="HTML",
        reply_markup=get_admin_panel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_logs")
async def handle_admin_logs(callback: CallbackQuery):
    """Логи системы"""
    await callback.message.edit_text(
        "📋 <b>Логи системы</b>\n\n"
        "🚧 Функция в разработке\n\n"
        "Здесь будет:\n"
        "• Системные логи\n"
        "• Логи ошибок\n"
        "• Активность пользователей\n"
        "• Фильтры и поиск",
        parse_mode="HTML",
        reply_markup=get_admin_panel_keyboard()
    )
    await callback.answer()


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


def get_role_request_keyboard(role: str) -> InlineKeyboardMarkup:
    """Клавиатура для запроса роли"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📝 Подать заявку", 
            callback_data=f"apply_for_{role}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
    )
    
    return builder.as_markup()
