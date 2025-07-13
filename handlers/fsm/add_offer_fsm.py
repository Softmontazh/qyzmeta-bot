# -*- coding: utf-8 -*-
# handlers/fsm/add_offer_fsm.py

from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.orm_user_jk import orm_get_jks_by_user_id
from database.models.orm_offer import orm_add_offer
from database.enums.offer_category_enum import OfferCategory
from services.notification_service import notify_service_provider

add_offer_router = Router()

# Категории заявок (соответствуют OfferCategory enum)
OFFER_CATEGORIES = {
    "domofon": "Домофон",
    "video": "Видеонаблюдение", 
    "elektrika": "Электрика",
    "santehnika": "Сантехника",
    "blagoustroystvo": "Благоустройство",
    "repair": "Ремонт",
    "drugoe": "Другое",
}


class AddOffer(StatesGroup):
    """Состояния для создания заявки."""
    choose_jk = State()        # Выбор ЖК (ВСЕГДА первый шаг)
    choose_category = State()  # Выбор категории  
    set_title = State()        # Ввод названия
    set_description = State()  # Ввод описания
    set_media = State()        # Загрузка медиа
    confirm = State()          # Подтверждение


def get_categories_keyboard():
    """Создает клавиатуру с категориями заявок."""
    keyboard = []
    for key, value in OFFER_CATEGORIES.items():
        keyboard.append(
            [InlineKeyboardButton(text=value, callback_data=f"category:{key}")]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirm_keyboard():
    """Создает клавиатуру подтверждения."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Отправить заявку", callback_data="confirm_offer"
                ),
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_offer"),
            ]
        ]
    )


@add_offer_router.message(F.text.lower().contains("создать заявку"))
@add_offer_router.message(Command("add_offer"))
async def start_add_offer(message: Message, state: FSMContext, session: AsyncSession):
    # Проверяем завершенность регистрации
    from utils.registration_check import check_user_registration
    if not await check_user_registration(message, session):
        return
        
    user_id = message.from_user.id
    jk_by_user = await orm_get_jks_by_user_id(session, user_id)
    
    if not jk_by_user:
        await message.answer(
            "❌ Для подачи заявки необходимо сначала привязаться к ЖК.\n"
            "Используйте команду /add_my_jk"
        )
        return

    # ВСЕГДА показываем выбор ЖК (даже если один)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🏢 {jk.name}, кв. {user_jk.appartment}",
                    callback_data=f"choose_jk:{user_jk.id}"
                )
            ]
            for jk, user_jk in jk_by_user
        ]
    )
    
    await state.set_state(AddOffer.choose_jk)
    await message.answer(
        "🏢 <b>Выберите ЖК для создания заявки:</b>",
        parse_mode="HTML",
        reply_markup=kb
    )


@add_offer_router.callback_query(F.data.startswith("choose_jk:"))
async def choose_jk(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    user_jk_id = int(callback.data.split(":")[1])
    
    # Получаем полные данные ЖК и UserJK для сохранения в state
    from database.models.orm_user_jk import orm_get_user_jk_with_jk_by_id
    user_jk_data = await orm_get_user_jk_with_jk_by_id(session, user_jk_id)
    
    if not user_jk_data:
        await callback.answer("❌ ЖК не найден")
        return
    
    user_jk, jk = user_jk_data
    
    # Сохраняем ВСЕ данные в state чтобы не делать повторные запросы
    await state.update_data(
        user_jk_id=user_jk_id,
        jk_id=jk.id,
        jk_name=jk.name,
        apartment=user_jk.appartment,
        jk_data=jk,  # Полные данные ЖК
        user_jk_data=user_jk  # Полные данные UserJK
    )
    
    await state.set_state(AddOffer.choose_category)
    await callback.message.edit_text(
        f"✅ <b>Выбран ЖК:</b> {jk.name}, кв. {user_jk.appartment}\n\n"
        "📋 Укажите категорию заявки:",
        parse_mode="HTML",
        reply_markup=get_categories_keyboard()
    )
    await callback.answer()


@add_offer_router.callback_query(F.data.startswith("category:"))
async def choose_category(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории."""
    category_key = callback.data.split(":")[1]
    category_name = OFFER_CATEGORIES.get(category_key, "Неизвестная категория")

    await state.update_data(category=category_key, category_name=category_name)
    await state.set_state(AddOffer.set_title)

    await callback.message.edit_text(
        f"✅ Выбрана категория: <b>{category_name}</b>\n\n"
        "📝 Введите краткое название вашей заявки:",
        parse_mode="HTML",
    )
    await callback.answer()


@add_offer_router.message(AddOffer.set_title)
async def set_title(message: Message, state: FSMContext):
    """Обработка ввода названия заявки."""
    title = message.text.strip()

    if len(title) < 5:
        await message.answer(
            "❌ Название должно содержать минимум 5 символов. Попробуйте еще раз:"
        )
        return

    if len(title) > 200:
        await message.answer(
            "❌ Название слишком длинное (максимум 200 символов). Попробуйте еще раз:"
        )
        return

    await state.update_data(title=title)
    await state.set_state(AddOffer.set_description)

    await message.answer(
        f"✅ Название: <b>{title}</b>\n\n" "📝 Опишите подробно вашу заявку:",
        parse_mode="HTML",
    )


@add_offer_router.message(AddOffer.set_description)
async def set_description(message: Message, state: FSMContext):
    """Обработка ввода описания заявки."""
    description = message.text.strip()

    if len(description) < 10:
        await message.answer(
            "❌ Описание должно содержать минимум 10 символов. Попробуйте еще раз:"
        )
        return

    await state.update_data(description=description)
    await state.set_state(AddOffer.set_media)

    # Создаем инлайн-клавиатуру с кнопкой "Пропустить"
    skip_media_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_media")]
    ])

    await message.answer(
        "✅ Описание сохранено.\n\n"
        "📸 Если хотите, прикрепите фото или видео к заявке.\n"
        "Или нажмите кнопку ниже для перехода к подтверждению.",
        reply_markup=skip_media_keyboard
    )


@add_offer_router.message(AddOffer.set_media, F.photo | F.video)
async def set_media(message: Message, state: FSMContext):
    """Обработка загрузки медиа."""
    if message.photo:
        media_id = message.photo[-1].file_id
        media_type = "фото"
    elif message.video:
        media_id = message.video.file_id
        media_type = "видео"
    else:
        await message.answer("❌ Поддерживаются только фото и видео.")
        return

    await state.update_data(media_id=media_id)
    await show_confirmation(message, state)


@add_offer_router.message(AddOffer.set_media, F.text.lower().contains("пропустить"))
async def skip_media(message: Message, state: FSMContext):
    """Пропуск загрузки медиа."""
    await show_confirmation(message, state)


# Новый обработчик для кнопки "Пропустить"
@add_offer_router.callback_query(F.data == "skip_media", StateFilter(AddOffer.set_media))
async def skip_media_callback(callback: CallbackQuery, state: FSMContext):
    """Пропуск загрузки медиа через кнопку."""
    await callback.answer()
    
    # Получаем данные состояния для подтверждения
    data = await state.get_data()

    text = (
        "📋 <b>Подтверждение заявки</b>\n\n"
        f"<b>Категория:</b> {data['category_name']}\n"
        f"<b>Название:</b> {data['title']}\n"
        f"<b>Описание:</b> {data['description']}\n"
        "\n✅ Отправить заявку?"
    )

    await state.set_state(AddOffer.confirm)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_confirm_keyboard())


@add_offer_router.message(AddOffer.set_media)
async def invalid_media(message: Message, state: FSMContext):
    """Обработка некорректного ввода медиа."""
    await message.answer(
        "❌ Пожалуйста, отправьте фото или видео, либо напишите 'пропустить'."
    )


async def show_confirmation(message: Message, state: FSMContext):
    """Показывает подтверждение заявки."""
    data = await state.get_data()

    text = (
        "📋 <b>Подтверждение заявки</b>\n\n"
        f"<b>Категория:</b> {data['category_name']}\n"
        f"<b>Название:</b> {data['title']}\n"
        f"<b>Описание:</b> {data['description']}\n"
    )

    if data.get("media_id"):
        text += "<b>Медиа:</b> прикреплено\n"

    text += "\n✅ Отправить заявку?"

    await state.set_state(AddOffer.confirm)
    await message.answer(text, parse_mode="HTML", reply_markup=get_confirm_keyboard())


@add_offer_router.callback_query(F.data == "confirm_offer")
async def confirm_offer(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    """Подтверждение и сохранение заявки."""
    data = await state.get_data()
    user_id = callback.from_user.id

    user_jk_id = data.get("user_jk_id")
    if not user_jk_id:
        await callback.message.edit_text("❌ Ошибка: не выбран ЖК.")
        await callback.answer()
        return

    # Создаем заявку через ORM
    offer_data = {
        "category": data["category"],
        "title": data["title"],
        "description": data["description"],
        "media_id": data.get("media_id"),
        "user_id": user_id,
        "user_jk_id": user_jk_id,
    }
    
    offer = await orm_add_offer(session, offer_data)
    await session.commit()

    await callback.message.edit_text(
        f"✅ <b>Заявка успешно создана!</b>\n\n"
        f"<b>Номер заявки:</b> #{offer.id}\n"
        f"<b>Категория:</b> {data['category_name']}\n"
        f"<b>Название:</b> {data['title']}\n\n"
        f"Ваша заявка будет рассмотрена в ближайшее время.",
        parse_mode="HTML",
    )

    # Уведомляем поставщика услуг о новой заявке
    # Получаем данные пользователя для уведомления
    from database.models.orm_user import orm_get_user_by_id
    user_data = await orm_get_user_by_id(session, user_id)
    
    # Вызываем с полными данными из state
    await notify_service_provider(
        session, 
        callback.bot, 
        offer, 
        data['jk_data'],      # Данные ЖК из state
        data['user_jk_data'], # Данные UserJK из state
        user_data,            # Данные User
        data["category"]
    )

    await state.clear()
    await callback.answer("Заявка создана!")


@add_offer_router.callback_query(F.data == "cancel_offer")
async def cancel_offer(callback: CallbackQuery, state: FSMContext):
    """Отмена создания заявки."""
    await callback.message.edit_text("❌ Создание заявки отменено.")
    await state.clear()
    await callback.answer("Отменено")
