# coding: utf-8
# handlers/fsm/add_lot_fsm.py

from html import escape
from aiogram import F, types, Router
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.orm_lot import (
    orm_add_lot,
    orm_get_lot,
    orm_get_lots,
    orm_delete_lot,
    orm_update_lot,
)

from database.enums.user_enums import UserRole
from keyboards.inline_for_lot import get_btns_lots
from keyboards.reply import get_keyboard, USER_KB
from database.models.model_user import User
from services.lot_service import check_user_lot_limit
import os
from typing import Callable

add_lot_router = Router()

NAVIGATION_KB = get_keyboard(
    "Назад",
    "Отмена",
    placeholder="Navigation",
    sizes=(2,),
)

OFFER_KB = get_btns_lots(
    btns={
        "💰 Куплю": "offer_type:buy",
        "🛒 Продам": "offer_type:sell",
        "🔄 Обмен": "offer_type:exchange",
        "🎁 Отдам даром": "offer_type:giveaway",
        "⏳ Арендую": "offer_type:rent",
        "🔑 Сдам в аренду": "offer_type:rent_out",
        "✋ Требуется": "offer_type:request",
        "💡 Предложение": "offer_type:suggest",
    },
    default_row_size=2,
)


class AddLot(StatesGroup):
    """Состояния для добавления и редактирования лота"""

    offer_type = State()  # Состояние для выбора типа предложения (куплю и т.д.)
    type_lot = State()  # Состояние для выбора типа лота (товары, услуги и т.д.)
    name_lot = State()  # Состояние для ввода названия типа лота
    description_lot = State()  # Состояние для ввода описания лота
    price_lot = State()  # Состояние для ввода цены лота
    city_lot = State()  # Состояние для ввода города, в котором находится лот
    phone_lot = State()  # Состояние для ввода номера телефона для связи
    image_lot = State()  # Состояние для загрузки изображения лота

    texts = {
        "AddLot:offer_type": "Укажите тип предложения заново",
        "AddLot:type_lot": "Укажите тип лота заново",
        "AddLot:name_lot": "Введите название лота заново",
        "AddLot:description_lot": "Введите описание лота заново",
        "AddLot:price_lot": "Введите стоимость лота заново",
        "AddLot:city_lot": "Введите город, в котором находится лот заново",
        "AddLot:phone_lot": "Введите номер телефона для связи заново",
        "AddLot:image_lot": "Загрузите изображение лота заново",
    }


async def check_to_addedit_lot(
    user_id: int, state: FSMContext, session: AsyncSession, send_func: Callable
):
    user_stmt = select(User).where(User.user_id == user_id)
    result = await session.execute(user_stmt)
    user = result.scalar_one_or_none()

    """Проверка, зарегистрирован ли пользователь и имеет ли он права для добавления лота"""
    if not user or user.role == UserRole.GUEST:
        print(
            f"Пользователь {user_id} не зарегистрирован или не имеет прав для добавления лота."
        )
        await send_func(
            "🚫 Вы не зарегистрированы в системе или у вас нет прав для добавления лота. Пожалуйста, зарегистрируйтесь, чтобы добавить лот.",
            reply_markup=get_keyboard(
                "Отправить номер 📞",
                request_contact=0,
                placeholder="нажми кнопку",
                sizes=(1,),
            ),
        )
        return

    """Проверка лимита на добавление лота"""
    can_add, current_count, limit = await check_user_lot_limit(user, session)
    if not can_add:
        await send_func(
            f"⚠️ Вы уже добавили {current_count} из {limit} допустимых лотов по вашей роли <b>{user.role.value}</b>.\n\n"
            "Чтобы получить больше возможностей:\n"
            "• удалите или отредактируйте существующие лоты\n"
            "• или обратитесь в поддержку: @LotBoxSup",
            reply_markup=USER_KB,
            parse_mode="HTML",
        )
        return

    """Если пользователь зарегистрирован и имеет права, начинаем процесс добавления лота"""
    await send_func(
        "📝 Вы начали процесс добавления или изменения лота.\n\nСледуйте инструкциям...",
        reply_markup=NAVIGATION_KB,
    )
    await send_func(
        "<b>Выберите тип предложения:</b>\n\n"
        "<i>(куплю, продам, обмен, отдам даром, аренда, сдам в аренду, требуется, предложение)</i>\n\n",
        reply_markup=OFFER_KB,
        parse_mode=ParseMode.HTML,
    )
    await state.set_state(AddLot.offer_type)


"""Начало процесса добавления лота при вводе команды или текста"""


# Обработчик команды /добавить_лот и текста "добавить лот" для начала процесса добавления лота
@add_lot_router.message(F.text.lower().contains("добавить лот"))
async def start_add_lot(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    """Начало процесса добавления лота"""
    if message.from_user is not None:
        await check_to_addedit_lot(message.from_user.id, state, session, message.answer)
    else:
        await message.answer(
            "Ошибка: не удалось определить пользователя.", reply_markup=USER_KB
        )


# Обработчик команды /добавить_лот для начала процесса добавления лота
@add_lot_router.callback_query(F.data.startswith("offer_type:"))
async def offer_type_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.data is not None:
        offer_type = callback.data.split(":", 1)[1]
        await state.update_data(offer_type=offer_type)
        await state.set_state(AddLot.type_lot)
        if isinstance(callback.message, Message) and hasattr(
            callback.message, "edit_text"
        ):
            await callback.message.edit_text(
                "<b>Укажите тип лота:</b>\n\n"
                "<i>(товары, услуги, работа, недвижимость, транспорт, электроника, животные, другие)</i>",
                parse_mode=ParseMode.HTML,
            )
        else:
            await callback.message.answer(
                "<b>Укажите тип лота:</b>\n\n"
                "<i>(товары, услуги, работа, недвижимость, транспорт, электроника, животные, другие)</i>",
                parse_mode=ParseMode.HTML,
            )
    else:
        await callback.message.answer(
            "Ошибка: не удалось определить тип предложения.", reply_markup=OFFER_KB
        )
    await callback.answer()


# Обработчик команды /отмена и текста "отмена" для отмены процесса добавления лота
@add_lot_router.message(StateFilter("*"), Command("отмена"))
@add_lot_router.message(StateFilter("*"), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await message.answer("Добавление лота отменено", reply_markup=USER_KB)
    else:
        await message.answer("Отменено", reply_markup=USER_KB)
    await state.clear()


# Обработчик команды /назад и текста "назад" для возврата на предыдущий шаг
@add_lot_router.message(StateFilter("*"), Command("назад"))
@add_lot_router.message(StateFilter("*"), F.text.casefold() == "назад")
async def back_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()

    if current_state == AddLot.offer_type:
        await message.answer(
            "Предыдущий шаг не доступен.\nНажмите ОТМЕНА или укажите тип предложения заново:",
            reply_markup=OFFER_KB,
        )
        return
    previous = None
    for step in AddLot.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            if previous == AddLot.offer_type:
                await message.answer(
                    "<b>Тип предложения:</b>\n\n"
                    "<i>(куплю, продам, обмен, отдам даром, аренда, сдам в аренду, требуется, предложение)</i>\n\n",
                    reply_markup=OFFER_KB,
                    parse_mode=ParseMode.HTML,
                )
            else:
                await message.answer(
                    f"Вы вернулись на предыдущий шаг\n{AddLot.texts[previous.state]}"
                )
            return
        previous = step


# Обработчик для выбора типа предложения
@add_lot_router.message(AddLot.offer_type, F.text | (F.text == "."))
async def add_offer_type(message: types.Message, state: FSMContext):
    if message.text == ".":
        data = await state.get_data()
        lot_for_edit = data.get("lot_for_edit")
        if lot_for_edit is not None:
            await state.update_data(offer_type=lot_for_edit.offer_type)
        else:
            await message.answer(
                "Вы не указали тип предложения.\n\nУкажите тип предложения заново:",
                reply_markup=OFFER_KB,
            )
    else:
        if len(message.text) > 50:
            await message.answer(
                "Вы ввели тип предложения, который превышает 50 символов.\n\nУкажите тип предложения заново не более 50 символов"
            )
            return
        await state.update_data(offer_type=message.text)

    await state.set_state(AddLot.type_lot)
    await message.answer(
        "<b>Укажите тип лота:</b>\n\n"
        "<i>(товары, услуги, работа, недвижимость, транспорт, животные, люди и др.)</i>\n\n",
        reply_markup=NAVIGATION_KB,
        parse_mode=ParseMode.HTML,
    )


# Обработчик для обработки некорректного ввода типа предложения
@add_lot_router.message(AddLot.offer_type)
async def add_offer_type_error(message: types.Message, state: FSMContext):
    await message.answer(
        "Вы ввели некорректные данные.\n\nУкажите тип предложения заново:"
    )


# Обработчик для выбора типа лота
@add_lot_router.message(AddLot.type_lot, F.text | (F.text == "."))
async def add_type_lot(message: types.Message, state: FSMContext):
    if message.text == ".":
        data = await state.get_data()
        lot_for_edit = data.get("lot_for_edit")
        if lot_for_edit is not None:
            await state.update_data(type_lot=lot_for_edit.type_lot)
        else:
            await message.answer("Вы не указали тип лота.\n\nУкажите тип лота заново:")
    else:
        if len(message.text) > 50:
            await message.answer(
                "Вы ввели тип лота, который превышает 50 символов.\n\nУкажите тип лота заново не более 50 символов",
            )
            return
        await state.update_data(type_lot=message.text)
    await state.set_state(AddLot.name_lot)
    await message.answer(
        "Введите название лота:",
        reply_markup=NAVIGATION_KB,
    )


# Обработчик для обработки некорректного ввода типа лота
@add_lot_router.message(AddLot.type_lot)
async def add_type_lot_error(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели некорректные данные.\n\nУкажите тип лота заново:")


# Обработчик для ввода названия лота
@add_lot_router.message(AddLot.name_lot, F.text | (F.text == "."))
async def add_name_lot(message: types.Message, state: FSMContext):
    if message.text == ".":
        data = await state.get_data()
        lot_for_edit = data.get("lot_for_edit")
        if lot_for_edit is not None:
            await state.update_data(name_lot=lot_for_edit.name)
        else:
            await message.answer(
                "Вы не ввели название лота.\n\nВведите название лота заново:"
            )
    else:
        if len(message.text) > 50:
            await message.answer(
                "Вы ввели название лота, которое превышает 50 символов.\n\nВведите название лота заново не более 50 символов"
            )
            return
        await state.update_data(name_lot=message.text)
    await state.set_state(AddLot.description_lot)
    await message.answer(
        "Введите описание лота:",
        reply_markup=NAVIGATION_KB,
    )


# Обработчик для обработки некорректного ввода названия лота
@add_lot_router.message(AddLot.name_lot)
async def add_name_lot_error(message: types.Message, state: FSMContext):
    await message.answer(
        "Вы ввели некорректные данные.\n\nВведите название лота заново:"
    )


# Обработчик для ввода описания лота
@add_lot_router.message(AddLot.description_lot, F.text | (F.text == "."))
async def add_description_lot(message: types.Message, state: FSMContext):
    if message.text == ".":
        data = await state.get_data()
        lot_for_edit = data.get("lot_for_edit")
        if lot_for_edit is not None:
            await state.update_data(description_lot=lot_for_edit.description)
        else:
            await message.answer(
                "Вы не ввели описание лота.\n\nВведите описание лота заново:"
            )
    else:
        if len(message.text) > 200:
            await message.answer(
                "Вы ввели описание лота, которое превышает 200 символов.\n\nВведите описание лота заново не более 200 символов"
            )
            return
        await state.update_data(description_lot=message.text)
    await state.set_state(AddLot.price_lot)
    await message.answer(
        "Введите стоимость лота:",
        reply_markup=NAVIGATION_KB,
    )


# Обработчик для обработки некорректного ввода описания лота
@add_lot_router.message(AddLot.description_lot)
async def add_description_lot_error(message: types.Message, state: FSMContext):
    await message.answer(
        "Вы ввели некорректные данные.\n\nВведите описание лота заново:"
    )


# Обработчик для ввода цены лота
@add_lot_router.message(AddLot.price_lot, F.text | (F.text == "."))
async def add_price_lot(message: types.Message, state: FSMContext):
    if message.text == ".":
        data = await state.get_data()
        lot_for_edit = data.get("lot_for_edit")
        if lot_for_edit is not None:
            await state.update_data(price_lot=lot_for_edit.price)
        else:
            await message.answer(
                "Вы не ввели цену лота.\n\nУстановите цену лота заново:"
            )
    else:
        try:
            price = float(message.text)
            if price < 0:
                raise ValueError
        except ValueError:
            await message.answer(
                "Вы ввели некорректные данные.\n\nУстановите цену лота заново:"
            )
            return
        await state.update_data(price_lot=message.text)
    await state.set_state(AddLot.city_lot)
    await message.answer(
        "Укажите город, в котором находится лот:",
        reply_markup=NAVIGATION_KB,
    )


# Обработчик для обработки некорректного ввода цены лота
@add_lot_router.message(AddLot.price_lot)
async def add_price_lot_error(message: types.Message, state: FSMContext):
    await message.answer(
        "Вы ввели некорректные данные.\n\nУстановите цену лота заново:"
    )


# Обработчик для ввода города, в котором находится лот
@add_lot_router.message(AddLot.city_lot, F.text | (F.text == "."))
async def add_city_lot(message: types.Message, state: FSMContext):
    if message.text == ".":
        data = await state.get_data()
        lot_for_edit = data.get("lot_for_edit")
        if lot_for_edit is not None:
            await state.update_data(city_lot=lot_for_edit.city)
        else:
            await message.answer(
                "Вы не указали город, в котором находится лот.\n\nУкажите город, в котором находится лот заново:"
            )
    else:
        if len(message.text) > 50:
            await message.answer(
                "Вы ввели город, который превышает 50 символов.\n\nУкажите город, в котором находится лот заново не более 50 символов"
            )
            return
        await state.update_data(city_lot=message.text)
    await state.set_state(AddLot.phone_lot)
    await message.answer(
        "Укажите номер телефона для связи:",
        reply_markup=NAVIGATION_KB,
    )


# Обработчик для обработки некорректного ввода города
@add_lot_router.message(AddLot.city_lot)
async def add_city_lot_error(message: types.Message, state: FSMContext):
    await message.answer(
        "Вы ввели некорректные данные.\n\nУкажите город, в котором находится лот, заново:"
    )


# Обработчик для ввода номера телефона для связи
@add_lot_router.message(AddLot.phone_lot, F.text | (F.text == "."))
async def add_phone_lot(message: types.Message, state: FSMContext):
    if message.text == ".":
        data = await state.get_data()
        lot_for_edit = data.get("lot_for_edit")
        if lot_for_edit is not None:
            await state.update_data(phone_lot=lot_for_edit.phone)
        else:
            await message.answer(
                "Вы не указали номер телефона для связи.\n\nУкажите номер телефона для связи заново:"
            )
    else:
        if len(message.text) > 11:
            await message.answer(
                "Вы ввели номер телефона, который не равен 11 символов.\n\nУкажите номер телефона для связи заново - 11 символов"
            )
            return
        if not message.text.isdigit():
            await message.answer(
                "Вы ввели некорректные данные.\n\nУкажите номер телефона для связи заново:"
            )
            return
        await state.update_data(phone_lot=message.text)
    await state.set_state(AddLot.image_lot)
    await message.answer(
        "Загрузите изображение лота:",
        reply_markup=NAVIGATION_KB,
    )


# Обработчик для обработки некорректного ввода номера телефона
@add_lot_router.message(AddLot.phone_lot)
async def add_phone_lot_error(message: types.Message, state: FSMContext):
    await message.answer(
        "Вы ввели некорректные данные.\n\nУкажите номер телефона заново:"
    )


# Обработчик для загрузки изображения лота
@add_lot_router.message(AddLot.image_lot, F.photo | (F.text == "."))
async def add_image_lot(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    if message.text and message.text == ".":
        data = await state.get_data()
        lot_for_edit = data.get("lot_for_edit")
        if lot_for_edit is not None:
            await state.update_data(image_lot=lot_for_edit.image_id)
        else:
            await message.answer(
                "Вы не загрузили изображение лота.\n\nЗагрузите изображение лота заново:"
            )
    else:
        """Сохранение изображения лота в канал-шину"""
        photo = message.photo[-1]
        BUS_ID = os.getenv("BUS_ID")
        sent = await message.bot.send_photo(BUS_ID, photo.file_id)
        new_file_id = sent.photo[-1].file_id
        await state.update_data(image_lot=new_file_id)
    data = await state.get_data()
    data["user_id"] = message.from_user.id
    lot_for_edit = data.get("lot_for_edit")
    try:
        if lot_for_edit is not None:
            await orm_update_lot(session, lot_for_edit.id, data)
        else:
            await orm_add_lot(session, data)
        await message.answer("Лот добавлен/отредактирован", reply_markup=USER_KB)
        await state.clear()
    except Exception as e:
        await message.answer(
            f"Ошибка при добавлении лота:\n<code>{escape(str(e))}</code>\n\nОбратитесь в отдел поддержки @LotBoxSup",
            reply_markup=USER_KB,
            parse_mode="HTML",
        )
        await state.clear()


# Обработчик для обработки некорректного ввода изображения лота
@add_lot_router.message(AddLot.image_lot)
async def add_image_lot_error(message: types.Message, state: FSMContext):
    await message.answer(
        "Вы ввели некорректные данные.\n\nЗагрузите изображение заново:"
    )


# Здесь вы можете добавить код для обработки изображения
