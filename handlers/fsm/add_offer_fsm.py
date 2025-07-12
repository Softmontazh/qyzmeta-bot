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
from sqlalchemy import select

from database.models.model_offer import Offer
from database.models.model_user_jk import UserJK
from database.models.orm_user_jk import orm_get_jks_by_user_id
from database.models.orm_offer import orm_add_offer
from database.models.orm_jk_service_provider import orm_get_service_provider_by_category
from database.models.orm_jk import orm_get_jk_by_id
from database.enums.offer_category_enum import OfferCategory
from database.enums.offer_enums import OfferStatus

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

    choose_jk = State()  # Выбор ЖК (если нужно)
    choose_category = State()  # Выбор категории
    set_title = State()  # Ввод названия
    set_description = State()  # Ввод описания
    set_media = State()  # Загрузка фото/видео (опционально)
    confirm = State()  # Подтверждение заявки


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


async def notify_service_provider(session: AsyncSession, bot, offer, user_jk_id: int, category: str):
    """Уведомить поставщика услуг о новой заявке"""
    try:
        # Получаем связь пользователя с ЖК по user_jk_id с информацией о пользователе
        from database.models.model_user import User
        result = await session.execute(
            select(UserJK, User).join(User, UserJK.user_id == User.user_id).where(UserJK.id == user_jk_id)
        )
        row = result.first()
        
        if not row:
            print(f"⚠️ Связь пользователя с ЖК (user_jk_id={user_jk_id}) не найдена")
            return
            
        user_jk, user = row
        jk_id = user_jk.jk_id
        
        # Конвертируем категорию в enum
        category_enum = OfferCategory.from_string(category)
        
        print(f"🔍 Ищем поставщика услуг для категории: {category} -> {category_enum.value} в ЖК {jk_id}")
        
        # Находим поставщика услуг для данной категории в ЖК
        service_provider = await orm_get_service_provider_by_category(session, jk_id, category_enum)
        
        if not service_provider:
            print(f"⚠️ Поставщик услуг для категории {category_enum.display_name} в ЖК {jk_id} не найден")
            return
            
        if not service_provider.receives_notifications:
            print(f"⚠️ Поставщик услуг {service_provider.organization_name} отключил уведомления")
            return
            
        # Получаем информацию о ЖК
        jk = await orm_get_jk_by_id(session, jk_id)
        jk_name = jk.name if jk else f"ЖК #{jk_id}"
        
        # Формируем информацию о заявителе
        user_info = f"{user.first_name or ''}"
        if user.last_name:
            user_info += f" {user.last_name}"
        if user.username:
            user_info += f" (@{user.username})"
            
        # Формируем контактную информацию
        contact_info = user.phone or "не указан"
        
        # Формируем информацию о квартире
        apartment_info = user_jk.appartment or "не указана"
        
        # Формируем сообщение
        notification_text = (
            f"🔔 <b>Новая заявка!</b>\n\n"
            f"<b>ЖК:</b> {jk_name}\n"
            f"<b>Квартира:</b> {apartment_info}\n"
            f"<b>Заявитель:</b> {user_info}\n"
            f"📞 <b>Телефон заявителя:</b> {contact_info}\n\n"
            f"<b>Категория:</b> {OfferCategory.get_display_name(category_enum)} {OfferCategory.get_emoji(category_enum)}\n"
            f"<b>Заявка №:</b> {offer.id}\n"
            f"<b>Название:</b> {offer.title}\n"
            f"<b>Описание:</b> {offer.description}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Для организации:</b> {service_provider.organization_name}\n"
            f"📞 <b>Контакт организации:</b> {service_provider.contact_phone or 'не указан'}"
        )
        
        # Создаем клавиатуру с кнопками действий
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏳ Принять в работу", 
                    callback_data=f"offer_status:{offer.id}:in_progress"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Выполнено", 
                    callback_data=f"offer_status:{offer.id}:completed"
                ),
                InlineKeyboardButton(
                    text="❌ Отменить", 
                    callback_data=f"offer_status:{offer.id}:cancelled"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📞 Связаться", 
                    url=f"tg://user?id={user.user_id}"
                ),
                InlineKeyboardButton(
                    text="📋 Управление", 
                    callback_data=f"manage_offer:{offer.id}"
                )
            ]
        ])
        
        # Отправляем уведомление ответственному лицу с кнопками
        await bot.send_message(
            chat_id=service_provider.responsible_user_id,
            text=notification_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        print(f"✅ Уведомление отправлено поставщику услуг {service_provider.organization_name} (user_id: {service_provider.responsible_user_id})")
        
    except Exception as e:
        print(f"❌ Ошибка при отправке уведомления поставщику услуг: {e}")


async def notify_user_status_change(session: AsyncSession, bot, offer, old_status: OfferStatus, new_status: OfferStatus):
    """Уведомить пользователя об изменении статуса его заявки"""
    try:
        # Получаем информацию о пользователе и ЖК
        from database.models.model_user import User
        result = await session.execute(
            select(UserJK, User).join(User, UserJK.user_id == User.user_id).where(UserJK.id == offer.user_jk_id)
        )
        row = result.first()
        
        if not row:
            print(f"⚠️ Пользователь для заявки #{offer.id} не найден")
            return
            
        user_jk, user = row
        
        # Получаем информацию о ЖК
        jk = await orm_get_jk_by_id(session, user_jk.jk_id)
        jk_name = jk.name if jk else f"ЖК #{user_jk.jk_id}"
        
        # Определяем категорию
        try:
            category_enum = OfferCategory.from_string(offer.category)
            category_display = OfferCategory.get_display_name(category_enum)
            category_emoji = OfferCategory.get_emoji(category_enum)
        except:
            category_display = offer.category
            category_emoji = "📝"
        
        # Формируем сообщение в зависимости от нового статуса
        if new_status == OfferStatus.IN_PROGRESS:
            title = f"⏳ <b>Заявка принята в работу!</b>"
            message_text = (
                f"{title}\n\n"
                f"<b>Заявка №:</b> {offer.id}\n"
                f"<b>ЖК:</b> {jk_name}\n"
                f"<b>Категория:</b> {category_display} {category_emoji}\n"
                f"<b>Название:</b> {offer.title}\n\n"
                f"🔧 Ваша заявка принята в работу и скоро будет выполнена!"
            )
        elif new_status == OfferStatus.COMPLETED:
            title = f"✅ <b>Заявка выполнена!</b>"
            message_text = (
                f"{title}\n\n"
                f"<b>Заявка №:</b> {offer.id}\n"
                f"<b>ЖК:</b> {jk_name}\n"
                f"<b>Категория:</b> {category_display} {category_emoji}\n"
                f"<b>Название:</b> {offer.title}\n\n"
                f"🎉 Ваша заявка успешно выполнена! Спасибо за обращение."
            )
        elif new_status == OfferStatus.CANCELLED:
            title = f"❌ <b>Заявка отменена</b>"
            message_text = (
                f"{title}\n\n"
                f"<b>Заявка №:</b> {offer.id}\n"
                f"<b>ЖК:</b> {jk_name}\n"
                f"<b>Категория:</b> {category_display} {category_emoji}\n"
                f"<b>Название:</b> {offer.title}\n\n"
                f"ℹ️ Ваша заявка была отменена. При необходимости создайте новую заявку."
            )
        elif new_status == OfferStatus.ARCHIVED:
            title = f"📦 <b>Заявка архивирована</b>"
            message_text = (
                f"{title}\n\n"
                f"<b>Заявка №:</b> {offer.id}\n"
                f"<b>ЖК:</b> {jk_name}\n"
                f"<b>Категория:</b> {category_display} {category_emoji}\n"
                f"<b>Название:</b> {offer.title}\n\n"
                f"📦 Ваша заявка перемещена в архив."
            )
        else:
            # Общее уведомление для других статусов
            title = f"🔄 <b>Статус заявки изменен</b>"
            message_text = (
                f"{title}\n\n"
                f"<b>Заявка №:</b> {offer.id}\n"
                f"<b>ЖК:</b> {jk_name}\n"
                f"<b>Категория:</b> {category_display} {category_emoji}\n"
                f"<b>Название:</b> {offer.title}\n\n"
                f"<b>Новый статус:</b> {new_status.display_name} {new_status.emoji}"
            )
        
        # Отправляем уведомление пользователю
        await bot.send_message(
            chat_id=user.user_id,
            text=message_text,
            parse_mode="HTML"
        )
        
        print(f"✅ Уведомление об изменении статуса отправлено пользователю {user.first_name} (user_id: {user.user_id})")
        
    except Exception as e:
        print(f"❌ Ошибка при отправке уведомления пользователю об изменении статуса: {e}")


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
            "❌ Для подачи заявки необходимо сначала привязаться к жилому комплексу.\n"
            "Используйте команду /add_my_jk"
        )
        return

    # Если ЖК несколько — предлагаем выбрать
    if len(jk_by_user) > 1:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"{jk.name}, {jk.city}, {jk.street}, {jk.house}",
                        callback_data=f"choose_jk:{user_jk.id}",
                    )
                ]
                for jk, user_jk in jk_by_user
            ]
        )
        await state.set_state(AddOffer.choose_jk)
        await message.answer(
            "🏢 У вас несколько ЖК. Выберите, для какого дома оформить заявку:",
            reply_markup=kb,
        )
        return

    # Если ЖК только один — сразу сохраняем user_jk_id и переходим к категориям
    jk, user_jk = jk_by_user[0]
    await state.update_data(user_jk_id=user_jk.id)
    await state.set_state(AddOffer.choose_category)
    await message.answer(
        "📋 <b>Создание заявки</b>\n\n" "Укажите, с чем связана ваша заявка:",
        parse_mode="HTML",
        reply_markup=get_categories_keyboard(),
    )


@add_offer_router.callback_query(
    StateFilter(AddOffer.choose_jk), F.data.startswith("choose_jk:")
)
async def choose_jk(callback: CallbackQuery, state: FSMContext):
    user_jk_id = int(callback.data.split(":")[1])
    await state.update_data(user_jk_id=user_jk_id)
    await state.set_state(AddOffer.choose_category)
    await callback.message.edit_text(
        "📋 <b>Создание заявки</b>\n\n" "Укажите, с чем связана ваша заявка:",
        parse_mode="HTML",
        reply_markup=get_categories_keyboard(),
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
    await notify_service_provider(session, callback.bot, offer, user_jk_id, data["category"])

    await state.clear()
    await callback.answer("Заявка создана!")


@add_offer_router.callback_query(F.data == "cancel_offer")
async def cancel_offer(callback: CallbackQuery, state: FSMContext):
    """Отмена создания заявки."""
    await callback.message.edit_text("❌ Создание заявки отменено.")
    await state.clear()
    await callback.answer("Отменено")


@add_offer_router.callback_query(F.data.startswith("offer_status:"))
async def handle_offer_status_change(callback: CallbackQuery, session: AsyncSession):
    """Обработка изменения статуса заявки через кнопки в уведомлении."""
    try:
        # Парсим данные из callback
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer("❌ Ошибка в данных кнопки", show_alert=True)
            return
            
        offer_id = int(parts[1])
        status_value = parts[2]
        
        # Определяем новый статус
        status_mapping = {
            "in_progress": OfferStatus.IN_PROGRESS,
            "completed": OfferStatus.COMPLETED,
            "cancelled": OfferStatus.CANCELLED,
            "archived": OfferStatus.ARCHIVED
        }
        
        new_status = status_mapping.get(status_value)
        if not new_status:
            await callback.answer("❌ Неизвестный статус", show_alert=True)
            return
        
        # Проверяем права доступа
        user_id = callback.from_user.id
        from database.models.orm_jk_service_provider import orm_get_service_providers_by_user
        service_providers = await orm_get_service_providers_by_user(session, user_id)
        
        if not service_providers:
            await callback.answer(
                "❌ У вас нет прав для изменения статуса заявок", 
                show_alert=True
            )
            return
        
        # Получаем заявку
        from database.models.orm_offer import orm_update_offer_status, orm_get_offer_with_user_info
        offer = await orm_get_offer_with_user_info(session, offer_id)
        
        if not offer:
            await callback.answer("❌ Заявка не найдена", show_alert=True)
            return
        
        # Проверяем, что пользователь имеет право управлять этой заявкой
        has_access = False
        for sp in service_providers:
            if sp.jk_id == offer.user_jk.jk_id:
                has_access = True
                break
        
        if not has_access:
            await callback.answer(
                "❌ У вас нет прав для управления этой заявкой", 
                show_alert=True
            )
            return
        
        # Обновляем статус
        updated_offer, old_status = await orm_update_offer_status(session, offer_id, new_status)
        await session.commit()
        
        # Отправляем уведомление пользователю
        await notify_user_status_change(session, callback.bot, updated_offer, old_status, new_status)
        
        # Обновляем сообщение с уведомлением
        status_text = {
            OfferStatus.IN_PROGRESS: "⏳ ПРИНЯТА В РАБОТУ",
            OfferStatus.COMPLETED: "✅ ВЫПОЛНЕНА", 
            OfferStatus.CANCELLED: "❌ ОТМЕНЕНА",
            OfferStatus.ARCHIVED: "📦 АРХИВИРОВАНА"
        }
        
        current_text = callback.message.text
        updated_text = f"{current_text}\n\n🔄 <b>СТАТУС: {status_text.get(new_status, new_status.display_name.upper())}</b>"
        
        # Создаем новую клавиатуру с оставшимися опциями
        new_keyboard = None
        if new_status not in [OfferStatus.COMPLETED, OfferStatus.ARCHIVED]:
            new_keyboard = get_status_keyboard_for_offer(offer_id, new_status)
        
        # Обновляем сообщение
        await callback.message.edit_text(
            text=updated_text,
            parse_mode="HTML",
            reply_markup=new_keyboard
        )
        
        await callback.answer(f"✅ Статус изменен на: {new_status.display_name}")
        
    except Exception as e:
        print(f"❌ Ошибка при изменении статуса через кнопку: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


def get_status_keyboard_for_offer(offer_id: int, current_status: OfferStatus) -> InlineKeyboardMarkup:
    """Создает клавиатуру со статусами для заявки (исключая текущий)."""
    buttons = []
    
    # Добавляем кнопки только для возможных переходов
    if current_status != OfferStatus.IN_PROGRESS:
        buttons.append([
            InlineKeyboardButton(
                text="⏳ Принять в работу", 
                callback_data=f"offer_status:{offer_id}:in_progress"
            )
        ])
    
    if current_status != OfferStatus.COMPLETED:
        buttons.append([
            InlineKeyboardButton(
                text="✅ Выполнено", 
                callback_data=f"offer_status:{offer_id}:completed"
            )
        ])
    
    if current_status != OfferStatus.CANCELLED:
        buttons.append([
            InlineKeyboardButton(
                text="❌ Отменить", 
                callback_data=f"offer_status:{offer_id}:cancelled"
            )
        ])
    
    # Кнопка архивирования (всегда доступна)
    if current_status != OfferStatus.ARCHIVED:
        buttons.append([
            InlineKeyboardButton(
                text="📦 Архивировать", 
                callback_data=f"offer_status:{offer_id}:archived"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@add_offer_router.callback_query(F.data.startswith("manage_offer:"))
async def handle_manage_offer(callback: CallbackQuery, session: AsyncSession):
    """Обработка управления заявкой - показать текущий статус и доступные действия."""
    try:
        offer_id = int(callback.data.split(":")[1])
        
        # Проверяем права доступа
        user_id = callback.from_user.id
        from database.models.orm_jk_service_provider import orm_get_service_providers_by_user
        service_providers = await orm_get_service_providers_by_user(session, user_id)
        
        if not service_providers:
            await callback.answer("❌ У вас нет прав для управления заявками", show_alert=True)
            return
        
        # Получаем заявку
        from database.models.orm_offer import orm_get_offer_with_user_info
        offer = await orm_get_offer_with_user_info(session, offer_id)
        
        if not offer:
            await callback.answer("❌ Заявка не найдена", show_alert=True)
            return
        
        # Проверяем права на эту конкретную заявку
        has_access = False
        for sp in service_providers:
            if sp.jk_id == offer.user_jk.jk_id:
                has_access = True
                break
        
        if not has_access:
            await callback.answer("❌ У вас нет прав для управления этой заявкой", show_alert=True)
            return
        
        # Определяем категорию
        try:
            category_enum = OfferCategory.from_string(offer.category)
            category_display = OfferCategory.get_display_name(category_enum)
            category_emoji = OfferCategory.get_emoji(category_enum)
        except:
            category_display = offer.category
            category_emoji = "📝"
        
        current_status = offer.status or OfferStatus.ACTIVE
        
        # Формируем сообщение с информацией о заявке
        manage_text = (
            f"📋 <b>Управление заявкой №{offer.id}</b>\n\n"
            f"<b>ЖК:</b> {offer.user_jk.jk.name}\n"
            f"<b>Категория:</b> {category_display} {category_emoji}\n"
            f"<b>Название:</b> {offer.title}\n"
            f"<b>Описание:</b> {offer.description}\n\n"
            f"<b>Текущий статус:</b> {current_status.display_name} {current_status.emoji}\n\n"
            f"Выберите действие:"
        )
        
        # Создаем клавиатуру с доступными статусами
        keyboard = get_status_keyboard_for_offer(offer_id, current_status)
        
        await callback.message.edit_text(
            text=manage_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        await callback.answer()
        
    except Exception as e:
        print(f"❌ Ошибка при управлении заявкой: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)
