# handlers/platform_roles/moderator_role_handler.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.orm_user import orm_get_user_by_telegram_id
from database.enums.user_enums import UserRole
from keyboards.platform_role_keyboards import get_moderator_panel_keyboard, get_role_request_keyboard

# Создаем роутер
router = Router()


@router.message(Command("is_moderator"))
async def handle_is_moderator_command(message: Message, session: AsyncSession):
    """Обработка команды /is_moderator"""
    user = await orm_get_user_by_telegram_id(session, message.from_user.id)
    
    if user and user.role == UserRole.MODERATOR:
        # У пользователя есть роль модератора - показываем панель
        await message.answer(
            "🛡️ <b>Панель модератора</b>\n\n"
            "Добро пожаловать в панель модерации!\n"
            "Выберите необходимое действие:",
            parse_mode="HTML",
            reply_markup=get_moderator_panel_keyboard()
        )
    else:
        # Роли нет - предлагаем подать заявку
        await message.answer(
            "🛡️ <b>Роль модератора</b>\n\n"
            "❌ У вас нет роли модератора платформы.\n\n"
            "📝 <b>Для получения роли необходимо:</b>\n"
            "• Подать заявку через форму\n"
            "• Указать опыт модерации\n"
            "• Дождаться одобрения создателем\n\n"
            "💡 Роль модератора дает доступ к:\n"
            "• Модерации контента\n"
            "• Обработке жалоб\n"
            "• Статистике модерации\n"
            "• Инструментам безопасности",
            parse_mode="HTML",
            reply_markup=get_role_request_keyboard("moderator")
        )


@router.callback_query(F.data == "mod_content")
async def handle_mod_content(callback: CallbackQuery):
    """Модерация контента"""
    await callback.message.edit_text(
        "🔍 <b>Модерация контента</b>\n\n"
        "🚧 Функция в разработке\n\n"
        "Здесь будет:\n"
        "• Очередь на модерацию\n"
        "• Фильтры по типам контента\n"
        "• История действий\n"
        "• Автоматические правила",
        parse_mode="HTML",
        reply_markup=get_moderator_panel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "mod_reports")
async def handle_mod_reports(callback: CallbackQuery):
    """Обработка жалоб"""
    await callback.message.edit_text(
        "📝 <b>Жалобы пользователей</b>\n\n"
        "🚧 Функция в разработке\n\n"
        "Здесь будет:\n"
        "• Входящие жалобы\n"
        "• Статусы обработки\n"
        "• Действия по жалобам\n"
        "• Статистика нарушений",
        parse_mode="HTML",
        reply_markup=get_moderator_panel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "mod_stats")
async def handle_mod_stats(callback: CallbackQuery):
    """Статистика модерации"""
    await callback.message.edit_text(
        "📊 <b>Статистика модерации</b>\n\n"
        "🚧 Функция в разработке\n\n"
        "Здесь будет:\n"
        "• Количество обработанных случаев\n"
        "• Типы нарушений\n"
        "• Эффективность модерации\n"
        "• Отчеты по периодам",
        parse_mode="HTML",
        reply_markup=get_moderator_panel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "mod_settings")
async def handle_mod_settings(callback: CallbackQuery):
    """Настройки модерации"""
    await callback.message.edit_text(
        "⚙️ <b>Настройки модерации</b>\n\n"
        "🚧 Функция в разработке\n\n"
        "Здесь будет:\n"
        "• Правила модерации\n"
        "• Автоматические фильтры\n"
        "• Уведомления\n"
        "• Персональные настройки",
        parse_mode="HTML",
        reply_markup=get_moderator_panel_keyboard()
    )
    await callback.answer()
