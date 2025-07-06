# coding: utf-8
import logging
from aiogram import F, Bot, types, Router
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.inline_for_lot import get_btns_lots
from keyboards.reply import USER_KB, get_keyboard
from services.lot_service import search_lots

CANCEL_SEARCH_KB = get_keyboard(
    "🔄 Сбросить фильтр 🔠",
    "🚪 Выйти из поиска 🔍",
    placeholder="поиск лотов",
    sizes=(1,),
)

SEARCH_KB = get_btns_lots(
    btns={
        "Пропустить шаг ▶️": "skip_step:skip_step",
    },
    row_sizes=[1],
)

# Настройка логгера
logger = logging.getLogger(__name__)


class SearchLot(StatesGroup):
    waiting_for_name = State()
    waiting_for_city = State()


search_lot_router = Router()


async def safe_delete_message(bot, chat_id: int, message_id: int):
    """Безопасное удаление сообщения с обработкой ошибок"""
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.debug(f"Не удалось удалить сообщение {message_id}: {e}")


async def send_search_prompt(message: Message, state: FSMContext) -> Message:
    """Отправка стандартного сообщения с инструкциями для поиска"""
    msg = await message.answer(
        "Введите ключевые слова для поиска...\n\n"
        "<i>Например: видеокамера, модель, услуги и т.д.</i>",
        reply_markup=SEARCH_KB,
        parse_mode=ParseMode.HTML,
    )
    await state.update_data(msg_status_id=msg.message_id)
    return msg


async def execute_search(message: Message, state: FSMContext):
    """Выполняет поиск на основе текущих фильтров"""
    data = await state.get_data()
    # Здесь должна быть логика поиска из вашего обработчика filter_city
    # ...
    await message.answer("Выполняю поиск...")


@search_lot_router.message(Command("search_lots"))
@search_lot_router.message(F.text.lower().contains("поиск лотов"))
async def search_lots_cmd(message: Message, session: AsyncSession, state: FSMContext):
    await state.clear()

    # Отправка заголовка
    header_msg = await message.answer(
        "<b>ПОИСК ЛОТА:</b>\n" + "_" * 20,
        reply_markup=CANCEL_SEARCH_KB,
        parse_mode=ParseMode.HTML,
    )

    # Сохраняем данные
    await state.update_data(
        {
            "msg_fsm_search_lot": header_msg.message_id,
            "search_header_id": header_msg.message_id,
        }
    )

    await send_search_prompt(message, state)
    await state.set_state(SearchLot.waiting_for_name)


@search_lot_router.message(StateFilter("*"), Command("exit_search"))
@search_lot_router.message(StateFilter("*"), F.text.lower().contains("выйти из поиска"))
async def exit_search(message: Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    bot = message.bot

    # Удаляем все служебные сообщения
    for msg_key in ["msg_fsm_search_lot", "msg_status_id", "search_header_id"]:
        if msg_id := data.get(msg_key):
            await safe_delete_message(bot, message.chat.id, msg_id)

    await message.answer("Поиск завершен", reply_markup=USER_KB)
    await state.clear()


@search_lot_router.callback_query(F.data == "skip_step:skip_step")
async def skip_step_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик пропуска текущего шага поиска"""
    try:
        data = await state.get_data()
        current_state = await state.get_state()

        # Удаляем предыдущее служебное сообщение
        msg_id = data.get("msg_status_id")
        if msg_id and msg_id != callback.message.message_id:
            # Если ID сообщения совпадает с текущим, удаляем его
            await safe_delete_message(callback.bot, callback.message.chat.id, msg_id)

        # Определяем следующий шаг в зависимости от текущего состояния
        if current_state == SearchLot.waiting_for_name.state:
            # Пропускаем ввод названия, переходим к городу
            await state.set_state(SearchLot.waiting_for_city)
            await callback.message.edit_text(
                "🔍 Пропущен шаг названия\n" "В каком городе искать лот?",
                reply_markup=SEARCH_KB,
            )
            await state.update_data(
                {
                    "msg_status_id": callback.message.message_id,
                    "name_skipped": True,  # Флаг что название пропущено
                }
            )

        elif current_state == SearchLot.waiting_for_city.state:
            # Пропускаем ввод города, выполняем поиск только по названию
            await state.update_data(city_skipped=True)
            await callback.message.edit_text(
                "🔍 Пропущен шаг города\n" "Будет выполнен поиск только по названию",
                reply_markup=SEARCH_KB,
            )

            # Автоматически запускаем поиск
            await execute_search(callback.message, state)

        else:
            await callback.answer("Нет активного шага для пропуска", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка в skip_step_callback: {e}")
        await callback.answer("⚠️ Произошла ошибка при пропуске шага", show_alert=True)
        await state.set_state(None)


@search_lot_router.message(SearchLot.waiting_for_name)
async def filter_name(message: Message, state: FSMContext):
    data = await state.get_data()
    if msg_id := data.get("msg_status_id"):
        await safe_delete_message(message.bot, message.chat.id, msg_id)

    if not message.text:
        msg = await message.answer("Пожалуйста, введите текстовый запрос")
        await state.update_data(msg_status_id=msg.message_id)
        return

    await state.update_data(name=message.text)
    msg = await message.answer("В каком городе искать лот?")
    await state.update_data(msg_status_id=msg.message_id)
    await state.set_state(SearchLot.waiting_for_city)


@search_lot_router.message(SearchLot.waiting_for_city)
async def filter_city(message: Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    bot = message.bot

    # Удаляем предыдущее служебное сообщение
    if msg_id := data.get("msg_status_id"):
        await safe_delete_message(bot, message.chat.id, msg_id)

    # Проверяем введенные данные
    if not message.text:
        msg = await message.answer("Пожалуйста, укажите город текстом")
        await state.update_data(msg_status_id=msg.message_id)
        return

    # Обновляем данные в состоянии
    await state.update_data(city=message.text.strip())
    filters = await state.get_data()

    try:
        # Поиск лотов с обработкой возможных ошибок БД
        lots = await search_lots(session=session, filters=filters)

        if not lots:
            # Если ничего не найдено - предлагаем начать новый поиск
            msg = await message.answer(
                "😕 По вашему запросу ничего не найдено.\n\n"
                "Попробуйте изменить параметры поиска:",
            )
            await state.update_data(msg_status_id=msg.message_id)
        else:
            # Отправка найденных лотов с пагинацией
            for i, lot in enumerate(lots[:10]):  # Ограничиваем вывод 10 лотами
                try:
                    await message.answer_photo(
                        photo=lot.image_id,
                        caption=(
                            f"<b>#{i+1} {lot.name}</b>\n"
                            f"📍 Город: {lot.city}\n"
                            f"🏷 Категория: {lot.type_lot}\n"
                            f"📝 Описание: {lot.description[:100]}...\n\n"
                            f"🆔 ID: {lot.id}"
                        ),
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [
                                    InlineKeyboardButton(
                                        text="🔍 Подробнее",
                                        callback_data=f"lot_detail_{lot.id}",
                                    ),
                                    InlineKeyboardButton(
                                        text="💬 Написать продавцу",
                                        callback_data=f"contact_seller_{lot.owner_id}",
                                    ),
                                ]
                            ]
                        ),
                        parse_mode=ParseMode.HTML,
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке лота {lot.id}: {e}")
                    await message.answer(
                        f"Не удалось загрузить лот #{lot.id}\n" f"Название: {lot.name}"
                    )

            # Предложение продолжить поиск
            msg = await message.answer(
                f"🔍 Найдено лотов: {len(lots)}\n" "Хотите уточнить поиск?",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="✨ Новый поиск", callback_data="new_search"
                            ),
                            InlineKeyboardButton(
                                text="⚡️ Изменить фильтры",
                                callback_data="change_filters",
                            ),
                        ]
                    ]
                ),
            )
    except Exception as e:
        logger.error(f"Ошибка при поиске лотов: {e}")
        msg = await message.answer(
            "⚠️ Произошла ошибка при поиске. Попробуйте позже", reply_markup=USER_KB
        )
        await state.clear()
        return

    # Возвращаем в начальное состояние поиска
    await send_search_prompt(message, state)
    await state.set_state(SearchLot.waiting_for_name)
