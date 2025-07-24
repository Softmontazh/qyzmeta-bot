# handlers/platform_roles/partner_role_handler.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.orm_user import orm_get_user_by_telegram_id
from database.enums.user_enums import UserRole
from keyboards.platform_role_keyboards import get_partner_panel_keyboard, get_role_request_keyboard

# Создаем роутер
router = Router()


@router.message(Command("is_partner"))
async def handle_is_partner_command(message: Message, session: AsyncSession):
    """Обработка команды /is_partner"""
    user = await orm_get_user_by_telegram_id(session, message.from_user.id)
    
    if user and user.role == UserRole.PARTNER:
        # У пользователя есть роль партнера - показываем панель
        await message.answer(
            "🤝 <b>Панель партнера</b>\n\n"
            "Добро пожаловать в партнерскую панель!\n"
            "Выберите необходимое действие:",
            parse_mode="HTML",
            reply_markup=get_partner_panel_keyboard()
        )
    else:
        # Роли нет - предлагаем подать заявку
        await message.answer(
            "🤝 <b>Роль партнера</b>\n\n"
            "❌ У вас нет роли партнера платформы.\n\n"
            "📝 <b>Для получения роли необходимо:</b>\n"
            "• Подать заявку через форму\n"
            "• Указать компанию и цели\n"
            "• Дождаться одобрения создателем\n\n"
            "💡 Роль партнера дает доступ к:\n"
            "• Управлению несколькими ЖК\n"
            "• Расширенной аналитике\n"
            "• Приоритетной поддержке\n"
            "• Специальным инструментам",
            parse_mode="HTML",
            reply_markup=get_role_request_keyboard("partner")
        )


@router.callback_query(F.data.startswith("apply_for_role:"))
async def handle_role_application_temp(callback: CallbackQuery):
    """Временный обработчик подачи заявки (пока FSM недоступен)"""
    role = callback.data.split(":")[1]
    
    role_names = {
        "ADMIN": "Администратор платформы",
        "PARTNER": "Партнер",
        "MODERATOR": "Модератор",
        "MANAGER": "Менеджер",
        "SUPPORT": "Поддержка"
    }
    
    role_name = role_names.get(role, role)
    
    await callback.message.edit_text(
        f"📝 <b>Подача заявки на роль: {role_name}</b>\n\n"
        "⚠️ <b>Система подачи заявок временно недоступна</b>\n\n"
        "📞 Для получения роли обратитесь к администратору:\n"
        "• Напишите создателю бота\n"
        "• Укажите желаемую роль\n"
        "• Опишите цели использования\n\n"
        "🔄 Система автоматической подачи заявок будет восстановлена в ближайшее время.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "partner_jks")
async def handle_partner_jks(callback: CallbackQuery):
    """Управление ЖК партнера"""
    await callback.message.edit_text(
        "🏢 <b>Мои ЖК</b>\n\n"
        "🚧 Функция в разработке\n\n"
        "Здесь будет:\n"
        "• Список ваших ЖК\n"
        "• Добавление новых ЖК\n"
        "• Управление настройками\n"
        "• Статистика по каждому ЖК",
        parse_mode="HTML",
        reply_markup=get_partner_panel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "partner_analytics")
async def handle_partner_analytics(callback: CallbackQuery):
    """Аналитика партнера"""
    await callback.message.edit_text(
        "📈 <b>Аналитика</b>\n\n"
        "🚧 Функция в разработке\n\n"
        "Здесь будет:\n"
        "• Общая статистика по ЖК\n"
        "• Активность жителей\n"
        "• Эффективность заявок\n"
        "• Финансовые отчеты",
        parse_mode="HTML",
        reply_markup=get_partner_panel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "partner_tools")
async def handle_partner_tools(callback: CallbackQuery):
    """Инструменты партнера"""
    await callback.message.edit_text(
        "🛠️ <b>Инструменты</b>\n\n"
        "🚧 Функция в разработке\n\n"
        "Здесь будет:\n"
        "• Массовые операции\n"
        "• Импорт/экспорт данных\n"
        "• Автоматизация процессов\n"
        "• Интеграции с внешними системами",
        parse_mode="HTML",
        reply_markup=get_partner_panel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "partner_support")
async def handle_partner_support(callback: CallbackQuery):
    """Поддержка партнера"""
    await callback.message.edit_text(
        "📞 <b>Поддержка</b>\n\n"
        "🎧 Приоритетная поддержка для партнеров\n\n"
        "📱 <b>Контакты:</b>\n"
        "• Telegram: @bySpecialist\n"
        "• Email: partner@softmontazh.kz\n"
        "• Телефон: +7 (XXX) XXX-XX-XX\n\n"
        "⏰ Время работы: 9:00 - 18:00 (UTC+6)\n"
        "🚀 Время ответа: до 2 часов",
        parse_mode="HTML",
        reply_markup=get_partner_panel_keyboard()
    )
    await callback.answer()
