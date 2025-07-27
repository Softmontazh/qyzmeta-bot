# handlers/platform_roles/partner_role_handler.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.orm_user import orm_get_user_by_telegram_id
from database.enums.user_enums import UserRole
from keyboards.platform_role_keyboards import get_partner_panel_keyboard, get_role_request_keyboard

# Создаем роутер
router = Router()


@router.message(Command("is_partner"))
async def handle_is_partner_command(message: Message, session: AsyncSession):
    """Обработка команды /is_partner"""
    user_id = message.from_user.id
    user = await orm_get_user_by_telegram_id(session, user_id)
    
    # Проверяем наличие одобренной заявки партнера
    from database.models.model_partner_application import PartnerApplication
    from database.enums.user_enums import ApplicationStatus
    from keyboards.reply import PARTNER_PANEL_KB
    
    stmt = select(PartnerApplication).where(
        PartnerApplication.user_id == user_id,
        PartnerApplication.status == ApplicationStatus.APPROVED
    ).limit(1)
    result = await session.execute(stmt)
    approved_application = result.scalar_one_or_none()
    
    print(f"DEBUG /is_partner: user_id={user_id}, approved_application={approved_application}")
    
    if approved_application:
        # У пользователя есть одобренная заявка - показываем партнерскую панель
        await message.answer(
            f"🤝 <b>Добро пожаловать, партнер!</b>\n\n"
            f"👤 <b>Партнер:</b> {approved_application.full_name}\n"
            f"🏢 <b>Компания:</b> {approved_application.company}\n\n"
            f"📊 Выберите необходимое действие в партнерской панели:",
            parse_mode="HTML",
            reply_markup=PARTNER_PANEL_KB
        )
    else:
        # Роли нет - предлагаем подать заявку
        from keyboards.reply import MAIN_KB
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        # Создаем inline-кнопку для подачи заявки
        apply_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📝 Стать партнером", callback_data="apply_for_role:PARTNER")]
            ]
        )
        
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
            "• Специальным инструментам\n\n"
            "� Нажмите кнопку ниже для подачи заявки:",
            parse_mode="HTML",
            reply_markup=apply_keyboard
        )
