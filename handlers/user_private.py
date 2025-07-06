# -*- coding: utf-8 -*-
# handlers/user_private.py

from datetime import timedelta, timezone
from aiogram import F, Router, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import (
    as_section,
    as_marked_section,
    Bold,
    Italic,
)
from sqlalchemy import select
from database.models.orm_user import orm_add_user, orm_get_user_by_id
from database.models.orm_lot import (
    orm_delete_lot,
    orm_get_lot,
    orm_get_lots,
    orm_get_lots_by_user,
)

from database.enums.user_enums import UserRole
from asyncio import sleep
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.model_user import User
from database.enums.lot_enums import LotStatus
from keyboards.inline_for_jk import get_btns_control_jk, unlink_keyboard
from database.models.orm_user_jk import orm_get_jks_by_user_id
from database.models.model_user_jk import UserJK
from static.privacy_policy import privacy_policy_text as policy_text
from static.about_bot import about_bot_text as about_bot
from static.help import help_text

from filters.chat_types import ChatTypeFilter
from keyboards.reply import MAIN_KB, get_keyboard
from keyboards.inline_for_lot import get_btns_control_lots
from handlers.fsm.add_jk_fsm import add_jk_router
from handlers.fsm.add_lot_fsm import add_lot_router
from handlers.fsm.search_lot_fsm import search_lot_router
from handlers.fsm.user_to_jk_fsm import user_to_jk_router

user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(chat_types=["private"]))
user_private_router.include_router(add_jk_router)
user_private_router.include_router(add_lot_router)
user_private_router.include_router(search_lot_router)
user_private_router.include_router(user_to_jk_router)

NAVIGATION_KB = get_keyboard(
    "Назад",
    "Отмена",
    placeholder="Navigation",
    sizes=(2,),
)

"""Обработчики команд и текстовых сообщений от пользователей в личных сообщениях"""


# Обработчик команды /start
@user_private_router.message(CommandStart())
async def start_cmd(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    start_user = await orm_get_user_by_id(session, user_id)
    if not start_user:
        # Если пользователь не найден в базе, добавляем его
        new_user = {
            "user_id": user_id,
            "first_name": first_name,
            "role": UserRole.GUEST,  # Устанавливаем роль пользователя как GUEST (гость)
        }
        await orm_add_user(session, new_user)
        await session.commit()

        await message.answer(
            "👋 Привет, Гость!\n\n"
            "Я — Qyzmeta, твой помощник 🤖\n\n"
            "Рад видеть тебя здесь впервые! Чтобы начать пользоваться всеми возможностями сервиса, пожалуйста, отправь свой номер телефона 📱\n\n"
            "👇 Просто нажми на кнопку ниже 👇",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_keyboard(
                "Отправить номер 📞",
                request_contact=0,
                placeholder="нажми кнопку",
                sizes=(1,),
            ),
        )
    else:
        # Если пользователь уже существует, отправляем приветствие
        await message.answer(
            f"Привет, {first_name}! 😊\n\nЯ рад тебя видеть снова! 🤗\n\n"
        )
        # Показываем основную клавиатуру
        await message.answer("Чем я могу тебе помочь? 🤓", reply_markup=MAIN_KB)


# Обработчик команды /отмена и текста "отмена" для отмены процесса добавления лота
@add_lot_router.message(StateFilter("*"), Command("отмена"))
@add_lot_router.message(StateFilter("*"), F.text.casefold() == "отмена")
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await message.answer("Действия отменены", reply_markup=MAIN_KB)
    else:
        await message.answer("Отменено", reply_markup=MAIN_KB)
    await state.clear()


# Обработчик команды "Отзывы"
@user_private_router.callback_query(F.data.startswith("feedback_lot_"))
async def feedback_lot(callback: CallbackQuery, session: AsyncSession):
    await callback.message.answer("В разработке...")
    await callback.answer()


# Обработчик команды "Удалить заявку (лот)"
@user_private_router.callback_query(F.data.startswith("delete_lot_"))
async def delete_lot(callback: CallbackQuery, session: AsyncSession):
    print(f"Обработка команды 'Удалить заявку (лот)' для заявки: {callback.data}")
    lot_id = int(callback.data.split(":")[-1])
    await orm_delete_lot(session, lot_id)
    await callback.message.answer(f"Заявка №{lot_id} удалена")
    await callback.message.delete()


# Обработчик команды "В архив"
@user_private_router.callback_query(F.data.startswith("archive_lot_"))
async def archive_lot(callback: CallbackQuery, session: AsyncSession):
    print(f"Обработка команды 'В архив' для лота: {callback.data}")
    lot_id = int(callback.data.split(":")[-1])
    lot = await orm_get_lot(session, lot_id)

    # Меняем статус лота
    if lot.status == LotStatus.ACTIVE:
        lot.status = LotStatus.ARCHIVED
        await callback.message.answer(f"Лот №{lot_id} перемещен в архив")
    elif lot.status == "ARCHIVED":
        await callback.message.answer(f"Лот №{lot_id} находится в архиве")
    else:
        await callback.message.answer("Архивирование невозможно")

    await session.commit()
    await callback.message.delete()


# Обработчик команды "Активировать"
@user_private_router.callback_query(F.data.startswith("activate_lot_"))
async def activate_lot(callback: CallbackQuery, session: AsyncSession):
    print(f"Обработка команды 'Активировать' для лота: {callback.data}")
    lot_id = int(callback.data.split(":")[-1])
    lot = await orm_get_lot(session, lot_id)

    # Меняем статус лота
    if lot.status == LotStatus.ARCHIVED:
        lot.status = LotStatus.ACTIVE
        await callback.message.answer(f"Заявка №{lot_id} активирована")
    elif lot.status == "ARCHIVED":
        await callback.message.answer(f"Заявка №{lot_id} активна")
    else:
        await callback.message.answer("Активирование невозможно")

    await session.commit()
    await callback.message.delete()


# Обработчик команды "Продлить заявку (лот)"
@user_private_router.callback_query(F.data.startswith("renew_lot_"))
async def extend_lot(callback: CallbackQuery, session: AsyncSession):
    print(f"Обработка команды 'Продлить заявку (лот)' для заявки: {callback.data}")
    lot_id = int(callback.data.split(":")[-1])
    lot = await orm_get_lot(session, lot_id)

    expires_at = lot.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    lot.expires_at += timedelta(days=7)
    await session.commit()
    await callback.message.delete()

    await callback.message.answer(
        "Срок действия заявки продлен на 7 дней!\n\n"
        f"Новый срок действия: {lot.expires_at.strftime('%d.%m.%Y')}"
    )


# Обработчик команды "Изменить заявку (лот)"
@user_private_router.callback_query(StateFilter(None), F.data.startswith("edit_lot_"))
async def edit_lot(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    lot_id = int(callback.data.split(":")[-1])
    lot_for_edit = await orm_get_lot(session, lot_id)

    await state.update_data(lot_for_edit=lot_for_edit)
    await callback.answer()
    # Импортируем функцию для начала добавления/изменения лота
    from handlers.fsm.add_lot_fsm import check_to_addedit_lot

    # Переходим к состоянию добавления/изменения лота через функцию проверки
    await check_to_addedit_lot(
        user_id=callback.from_user.id,
        state=state,
        session=session,
        send_func=callback.message.answer,
    )


# Обработчик команды /market
@user_private_router.message(or_f(Command("market")))
async def market_cmd(message: Message, session: AsyncSession):
    for lot in await orm_get_lots(session):
        await message.answer_photo(
            lot.image_id,
            caption=f"*{lot.type_lot}*\n\n{lot.name}\n_{lot.description}_\n\n{round(lot.price, 0)} тг.\n\n{lot.city}\n{lot.phone}",
            parse_mode="Markdown",
        )
    await message.answer(
        "На витрине представлены товары и услуги. Выбирай то, что тебе нужно!\n\n"
    )


# Обработчик команды /help
@user_private_router.message(F.text.lower().contains("помощь"))
@user_private_router.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(help_text, parse_mode=ParseMode.MARKDOWN)


# Обработчик команды /settings
@user_private_router.message(F.text.lower().contains("настройк"))
@user_private_router.message(Command("settings"))
async def settings_cmd(message: Message):
    await message.answer(
        "⚙️ Настройки бота пока не реализованы, но скоро будут добавлены!\n\n"
        "Если у тебя есть предложения или пожелания, напиши в поддержку бота @qyzmetasup",
        parse_mode=ParseMode.MARKDOWN,
    )


# Обработчик команды /support
@user_private_router.message(F.text.lower().contains("поддержка"))
@user_private_router.message(Command("support"))
async def support_cmd(message: Message):
    await message.answer(about_bot, parse_mode=ParseMode.MARKDOWN)


# Обработчик команды /policy
@user_private_router.message(F.text.lower().contains("политик" or "конфиденциальност"))
@user_private_router.message(Command("policy"))
async def policy_cmd(message: Message):
    await message.answer(policy_text, parse_mode=ParseMode.MARKDOWN)


# Ввод номера телефона
@user_private_router.message(F.contact)
async def get_contact(message: Message, bot: Bot, session: AsyncSession):
    """Первичная регистрация, получаем номер телефона."""

    user_id = message.from_user.id
    first_name = message.from_user.first_name
    contact = message.contact.phone_number

    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    # Если пользователь не найден, создаем нового
    if not user:
        new_user = {
            "user_id": user_id,
            "first_name": first_name,
            "phone": contact,
            "role": UserRole.USER,  # Устанавливаем роль пользователя
        }
        # Сохраняем пользователя в базе данных
        await orm_add_user(session, new_user)
        await session.commit()
    # Если пользователь уже существует, обновляем его данные
    else:
        user.first_name = first_name
        user.phone = contact
        user.role = UserRole.USER  # Обновляем роль пользователя
        await session.commit()
    # Отправляем приветственное сообщение
    sent_msg = await message.answer(
        f"🎉 ПОЗДРАВЛЯЮ!!! 🎉\n\n"
        f"Теперь ты пользователь сервиса и сможешь создавать заявки и учавствовать в жизни своего дома.\n\n"
        f"Твой номер телефона {contact} зафиксирован для подтверждения.\n\n"
        f"Желаю тебе, чтобы все твои заявки были успешно выполнены!\n\nА жизнь в доме стала еще комфортнее\n\n✨ Удачи!!! ✨"
    )

    # Удаляем последнее сообщение с номером и приветствие
    try:
        await message.delete()
        await message.bot.delete_message(
            chat_id=message.chat.id, message_id=message.message_id - 1
        )
    except Exception:
        pass

    # Удаляем сообщение о сохранении номера через 10 секунд
    async def delete_saved_message(msg):
        await sleep(15)
        try:
            await msg.delete()
        except Exception:
            pass

    # Запускаем задачу для удаления сообщения
    asyncio.create_task(delete_saved_message(sent_msg))

    # Показываем основную клавиатуру
    await message.answer(
        "Чем я могу тебе помочь? 🤓",
        reply_markup=get_keyboard(
            "Создать заявку 📝",
            "Мои заявки 📝",
            "Мой профиль 👤",
            "Мой дом 🏢",
            placeholder="User Menu",
            sizes=(1, 2),
        ),
    )


# Обработчик "Мои заявки"
@user_private_router.message(F.text.lower().contains("мои заявки"))
@user_private_router.message(Command("my_offers"))
async def my_requests_cmd(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    user = await orm_get_user_by_id(session, user_id)

    # Проверяем, зарегистрирован ли пользователь
    if not user:
        await message.answer(
            "Вы не зарегистрированы в системе."
            "Для начала отправьте свой номер телефона, чтобы зарегистрироваться.",
            reply_markup=get_keyboard(
                "Отправить номер 📞",
                request_contact=0,
                placeholder="нажми кнопку",
                sizes=(1, 1),
            ),
        )
        return

    # Получаем заявки (лоты) пользователя
    lots = await orm_get_lots_by_user(session, user_id=user_id)

    # Если у пользователя нет заявок, отправляем сообщение
    if not lots:
        await message.answer("У Вас пока нет заявок. Добавь свою первую заявку! 📝")
        return

    # Формируем список заявок для отображения
    for lot in lots:
        await message.answer_photo(
            lot.image_id,
            caption=as_section(
                f"{lot.type_lot}\n",
                f"{lot.offer_type.value}\n",
                f"{lot.name}\n",
                f"-" * 24 + "\n",
                f"{round(lot.price, 0):,} тг.".replace(",", " "),
                f"\n\n{lot.city}\n",
                f"{lot.phone}\n\n",
                Italic(f"Описание: \n{lot.description}\n"),
                Italic(f"\n\nСтатус заявки: {lot.status.value}"),
                Italic(f"\nВидимость заявки: {lot.visibility.value}"),
                Italic(f"\nПубликуется до: {lot.expires_at.strftime('%d.%m.%Y')}"),
            ).as_html(),
            parse_mode="HTML",
            reply_markup=get_btns_control_lots(
                lot_id=lot.id,
                status=lot.status,
                user_role=user.role,
            ),
        )


# Обработчик "Мой дом"
@user_private_router.message(F.text.lower().contains("мой дом"))
@user_private_router.message(Command("my_jk"))
async def my_jk_cmd(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    jk_by_user = await orm_get_jks_by_user_id(session, user_id)
    # Проверяем, есть ли у пользователя ЖК
    if not jk_by_user:
        await message.answer(
            'Вы не привязаны ни к одному дому.\n\nЧтобы привязаться к дому, нажмите на кнопку "Добавить мою квартиру" в меню.',
            reply_markup=get_keyboard(
                "Добавить мою квартиру",
                "Главное меню 🏠",
                placeholder="User Menu",
                sizes=(1, 1),
            ),
        )
        return
    else:
        await message.answer(
            "Вот ваши зарегистрированные дома:",
            reply_markup=get_keyboard(
                "Добавить мою квартиру",
                "Главное меню 🏠",
                placeholder="User Menu",
                sizes=(1, 1),
            ),
        )
        for jk, user_jk in jk_by_user:
            user_jk_id = user_jk.id
            appartment = user_jk.appartment
            if jk.image_id:  # Проверяем, что image_id не None и не пустой
                await message.answer_photo(
                    jk.image_id,
                    caption=as_section(
                        f"{jk.name}\n",
                        f"{jk.city}\n",
                        f"{jk.street}, {jk.house}, {jk.block or ''}\n\n",
                        f"Ваша квартира: {appartment}\n",
                    ).as_html(),
                    reply_markup=unlink_keyboard(user_jk_id),
                    parse_mode="HTML",
                )
            else:
                # Формируем строку адреса без лишней запятой, если блока нет
                address = f"{jk.street}, дом {jk.house}"
                if jk.block:
                    address += f", {jk.block}"
                await message.answer(
                    as_section(
                        f"{jk.name}\n",
                        f"{jk.city}\n",
                        f"{address}\n\n",
                        f"Ваша квартира: {appartment}\n",
                    ).as_html(),
                    reply_markup=unlink_keyboard(user_jk_id),
                    parse_mode="HTML",
                )


# Обработчик команды "Отменить регистрацию в ЖК"
@user_private_router.callback_query(StateFilter(None), F.data.startswith("unlink:"))
async def unlink_jk_handler(callback: CallbackQuery, session: AsyncSession):
    user_jk_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    stmt = select(UserJK).where(UserJK.id == user_jk_id, UserJK.user_id == user_id)
    result = await session.execute(stmt)
    user_jk = result.scalar_one_or_none()

    if user_jk:
        await session.delete(user_jk)
        await session.commit()
        # Проверяем, есть ли caption у сообщения
        if callback.message.caption is not None:
            await callback.message.edit_caption("✅ Регистрация отменена")
        else:
            await callback.message.edit_text("✅ Регистрация отменена")
    else:
        await callback.answer("Привязка не найдена или уже удалена", show_alert=True)


# Обработчик команды "Создать заявку"
@user_private_router.message(F.text.lower().contains("создать заявку"))
@user_private_router.message(Command("create_offer"))
async def create_offer_cmd(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    user = await orm_get_user_by_id(session, user_id)

    # Проверяем, зарегистрирован ли пользователь
    if not user:
        await message.answer(
            "Вы не зарегистрированы в системе."
            "Для начала отправьте свой номер телефона, чтобы зарегистрироваться.",
            reply_markup=get_keyboard(
                "Отправить номер 📞",
                request_contact=0,
                placeholder="нажми кнопку",
                sizes=(1, 1),
            ),
        )
        return

    await message.answer("Пожалуйста, введите данные для заявки:")
    # Здесь можно добавить логику для сбора данных заявки


@user_private_router.message(F.text.lower().contains("мой профиль"))
@user_private_router.message(Command("my_profile"))
async def my_profile_cmd(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    user = await orm_get_user_by_id(session, user_id)

    # Проверяем, зарегистрирован ли пользователь
    if not user:
        await message.answer(
            "Вы не зарегистрированы в системе."
            "Чтобы зарегистрироваться, отправьте свой номер телефона.",
            reply_markup=get_keyboard(
                "Отправить номер 📞",
                request_contact=0,
                placeholder="нажми кнопку",
                sizes=(1, 1),
            ),
        )
        return

    # Отправляем информацию о пользователе

    text = (
        f"Ваш профиль:\n\n"
        f"Имя: {user.first_name}\n"
        f"Номер телефона: {user.phone}\n"
        f"Роль: {user.role.value}\n\n"
        f"Ваши Жилищные Комплексы: {len(await orm_get_jks_by_user_id(session, user_id))}\n\n"
    )
    text_jks = await orm_get_jks_by_user_id(session, user_id)
    if text_jks:
        text += "Ваши ЖК:\n"
        for jk, user_jk in text_jks:
            text += f"- {jk.name}, {jk.city}, {jk.street}, {jk.house}, {jk.block or ''}, {user_jk.appartment}\n"
    else:
        text += "У вас нет привязанных ЖК.\n"

    await message.answer(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_keyboard(
            "Удалить профиль ❌",
            "Главное меню 🏠",
            placeholder="User Profile Menu",
            sizes=(1, 1),
        ),
    )


# Обработчик команды "Удалить профиль"
@user_private_router.message(F.text.lower().contains("удалить профиль"))
@user_private_router.message(Command("delete_profile"))
async def delete_profile_cmd(message: Message, session: AsyncSession):
    user_id = message.from_user.id  # <-- добавьте эту строку
    CONFIRM_DELETE = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, удалить профиль ❌",
                    callback_data=f"confirm_delete_{user_id}",
                ),
                InlineKeyboardButton(
                    text="Нет, отменить удаление ✅",
                    callback_data=f"cancel_delete_{user_id}",
                ),
            ]
        ]
    )
    await message.answer(
        "Вы уверены, что хотите удалить свой профиль? Это действие необратимо.",
        reply_markup=CONFIRM_DELETE,
    )


# Обработчик подтверждения удаления профиля
@user_private_router.callback_query(F.data.startswith("confirm_delete"))
async def confirm_delete_profile(callback: CallbackQuery, session: AsyncSession):
    try:
        user_id = int(callback.data.split("_")[-1])
    except Exception:
        await callback.message.edit_text("Ошибка: не удалось определить пользователя.")
        await callback.answer()
        return

    user = await orm_get_user_by_id(session, user_id)
    user_jks = await orm_get_jks_by_user_id(session, user_id)
    # Удаляем все привязки пользователя к ЖК
    for jk, user_jk in user_jks:
        await session.delete(user_jk)
        await callback.message.answer(
            f"Привязка к ЖК {jk.name} удалена.",
        )
    # Удаляем профиль пользователя
    if user:
        await session.delete(user)
        await session.commit()
        await callback.message.edit_text("Ваш профиль успешно удален. До свидания!")
    else:
        await callback.message.edit_text("Профиль не найден или уже удален.")

    await callback.answer()


# Обработчик отмены удаления профиля
@user_private_router.callback_query(F.data.startswith("cancel_delete"))
async def cancel_delete_profile(callback: CallbackQuery, session: AsyncSession):
    await callback.message.edit_text("Удаление профиля отменено.")
    await callback.answer()
