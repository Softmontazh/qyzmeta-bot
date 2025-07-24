# handlers/fsm/role_application_fsm.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.orm_partner_application import orm_create_partner_application
from database.enums.user_enums import UserRole

# Создаем роутер
router = Router()


class RoleApplicationStates(StatesGroup):
    """Состояния для подачи заявки на роль"""
    waiting_full_name = State()
    waiting_company = State()
    waiting_purpose = State()
    waiting_phone = State()
    waiting_confirmation = State()


@router.callback_query(F.data.startswith("apply_for_role:"))
async def start_role_application(callback: CallbackQuery, state: FSMContext):
    """Начало подачи заявки на роль"""
    role = callback.data.split(":")[1]
    
    await state.update_data(requested_role=role)
    await state.set_state(RoleApplicationStates.waiting_full_name)
    
    role_names = {
        "ADMIN": "Администратор платформы",
        "PARTNER": "Партнер",
        "MODERATOR": "Модератор",
        "MANAGER": "Менеджер",
        "SUPPORT": "Поддержка"
    }
    
    role_name = role_names.get(role, role)
    
    await callback.message.edit_text(
        f"📝 <b>Заявка на роль: {role_name}</b>\n\n"
        "Для рассмотрения заявки нам необходима следующая информация:\n\n"
        "👤 <b>Введите ваше полное имя (ФИО):</b>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(RoleApplicationStates.waiting_full_name)
async def process_full_name(message: Message, state: FSMContext):
    """Обработка ввода полного имени"""
    full_name = message.text.strip()
    
    if len(full_name) < 3:
        await message.answer(
            "❌ Имя должно содержать минимум 3 символа. Попробуйте еще раз:"
        )
        return
    
    await state.update_data(full_name=full_name)
    await state.set_state(RoleApplicationStates.waiting_company)
    
    await message.answer(
        "🏢 <b>Введите название вашей компании или организации:</b>\n\n"
        "💡 <i>Если вы работаете как ИП, укажите 'ИП Фамилия' или просто 'Индивидуальный предприниматель'</i>",
        parse_mode="HTML"
    )


@router.message(RoleApplicationStates.waiting_company)
async def process_company(message: Message, state: FSMContext):
    """Обработка ввода компании"""
    company = message.text.strip()
    
    if len(company) < 2:
        await message.answer(
            "❌ Название компании должно содержать минимум 2 символа. Попробуйте еще раз:"
        )
        return
    
    await state.update_data(company=company)
    await state.set_state(RoleApplicationStates.waiting_purpose)
    
    data = await state.get_data()
    role = data.get("requested_role")
    
    purpose_examples = {
        "ADMIN": "управление пользователями платформы, аналитика",
        "PARTNER": "управление ЖК, предоставление услуг жильцам",
        "MODERATOR": "модерация контента, обработка жалоб",
        "MANAGER": "управление заказами, работа с клиентами",
        "SUPPORT": "поддержка пользователей, консультации"
    }
    
    example = purpose_examples.get(role, "работа с системой")
    
    await message.answer(
        f"🎯 <b>Опишите цель получения роли:</b>\n\n"
        f"Расскажите, для чего вам нужна эта роль и как вы планируете её использовать.\n\n"
        f"💡 <i>Например: {example}</i>",
        parse_mode="HTML"
    )


@router.message(RoleApplicationStates.waiting_purpose)
async def process_purpose(message: Message, state: FSMContext):
    """Обработка ввода цели"""
    purpose = message.text.strip()
    
    if len(purpose) < 10:
        await message.answer(
            "❌ Описание цели должно содержать минимум 10 символов. Попробуйте еще раз:"
        )
        return
    
    await state.update_data(purpose=purpose)
    await state.set_state(RoleApplicationStates.waiting_phone)
    
    await message.answer(
        "📞 <b>Введите ваш контактный телефон:</b>\n\n"
        "💡 <i>Формат: +7XXXXXXXXXX или 8XXXXXXXXXX</i>",
        parse_mode="HTML"
    )


@router.message(RoleApplicationStates.waiting_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка ввода телефона"""
    phone = message.text.strip()
    
    # Простая валидация телефона
    if len(phone) < 10 or not any(char.isdigit() for char in phone):
        await message.answer(
            "❌ Некорректный формат телефона. Попробуйте еще раз:\n"
            "💡 <i>Формат: +7XXXXXXXXXX или 8XXXXXXXXXX</i>",
            parse_mode="HTML"
        )
        return
    
    await state.update_data(phone=phone)
    await state.set_state(RoleApplicationStates.waiting_confirmation)
    
    # Показываем сводку для подтверждения
    data = await state.get_data()
    
    role_names = {
        "ADMIN": "Администратор платформы",
        "PARTNER": "Партнер", 
        "MODERATOR": "Модератор",
        "MANAGER": "Менеджер",
        "SUPPORT": "Поддержка"
    }
    
    role_name = role_names.get(data["requested_role"], data["requested_role"])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_application"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_application")
            ]
        ]
    )
    
    await message.answer(
        f"📋 <b>Проверьте данные заявки:</b>\n\n"
        f"🎯 <b>Роль:</b> {role_name}\n"
        f"👤 <b>ФИО:</b> {data['full_name']}\n"
        f"🏢 <b>Компания:</b> {data['company']}\n"
        f"📞 <b>Телефон:</b> {data['phone']}\n"
        f"💬 <b>Цель:</b> {data['purpose']}\n\n"
        "✅ Всё верно? Подтвердите отправку заявки:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "confirm_application")
async def confirm_application(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Подтверждение и отправка заявки"""
    data = await state.get_data()
    user_id = callback.from_user.id
    
    try:
        application = await orm_create_partner_application(
            session=session,
            user_id=user_id,
            requested_role=UserRole[data["requested_role"]],
            full_name=data["full_name"],
            company=data["company"],
            purpose=data["purpose"],
            phone=data["phone"]
        )
        
        await callback.message.edit_text(
            f"✅ <b>Заявка #{application.id} успешно отправлена!</b>\n\n"
            "📋 Ваша заявка передана на рассмотрение администрации.\n"
            "⏰ Обычно рассмотрение занимает 1-3 рабочих дня.\n\n"
            "📧 Результат рассмотрения будет направлен вам в личные сообщения.",
            parse_mode="HTML"
        )
        
        await state.clear()
        
    except Exception as e:
        await callback.message.edit_text(
            "❌ <b>Ошибка при отправке заявки</b>\n\n"
            "Попробуйте еще раз позже или обратитесь в поддержку.",
            parse_mode="HTML"
        )
        print(f"Ошибка создания заявки: {e}")
    
    await callback.answer()


@router.callback_query(F.data == "cancel_application")
async def cancel_application(callback: CallbackQuery, state: FSMContext):
    """Отмена заявки"""
    await callback.message.edit_text(
        "❌ <b>Заявка отменена</b>\n\n"
        "Вы можете подать заявку позже, воспользовавшись соответствующей командой.",
        parse_mode="HTML"
    )
    await state.clear()
    await callback.answer()
