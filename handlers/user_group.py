# -*- coding: utf-8 -*-
# handlers/user_group.py

import asyncio
from asyncio.log import logger
import re
from string import punctuation

from aiogram import F, Bot, types, Router
from aiogram.filters import Command

from filters.chat_types import ChatTypeFilter
from static.restricted_words import restricted_words

user_group_router = Router()
user_group_router.message.filter(ChatTypeFilter(chat_types=["group", "supergroup"]))
user_group_router.edited_message.filter(
    ChatTypeFilter(chat_types=["group", "supergroup"])
)

"""Обработчик команды /start для групповых чатов"""


@user_group_router.message(Command("admin"))
async def get_admins(message: types.Message, bot: Bot):
    """
    Обработчик команды /admin для получения списка администраторов группы
    """
    chat_id = message.chat.id
    admins_list = await bot.get_chat_administrators(chat_id)
    # Получаем список администраторов чата
    print(f"Админы чата {chat_id}: {admins_list}")
    # Код для форматирования списка администраторов
    admins_list = [
        member.user.id
        for member in admins_list
        if member.status == "administrator" or member.status == "creator"
    ]
    bot.my_admins_list = admins_list
    if message.from_user.id in admins_list:
        await message.delete()
        await message.answer(
            "Список администраторов группы обновлен. Теперь я знаю, кто здесь главный! 😉"
        )


"""Обработчик для очистки сообщений от запрещенных слов и знаков препинания"""


@user_group_router.edited_message()
@user_group_router.message()
async def cleaner(message: types.Message):
    """
    Обработчик для очистки сообщений от запрещенных слов и знаков препинания
    """
    if not message.text:
        return

    # Проверяем, есть ли в сообщении запрещенные слова
    # Приводим текст сообщения к нижнему регистру для нечувствительности к регистру
    lower_text = message.text.lower()
    found_bad_words = [
        word
        for word in restricted_words
        if re.search(rf"(?i){re.escape(word)}", lower_text)
    ]

    if found_bad_words:
        try:
            await message.delete()
            warning_msg = await message.answer(
                f"@{message.from_user.username if message.from_user.username else message.from_user.first_name}, "
                f"сообщение удалено. Обнаружены запрещённые слова: {', '.join(found_bad_words)}\n\n"
                "📌 Правила чата:\n"
                "1. Без нецензурной лексики\n"
                "2. Без оскорблений\n"
                "3. Без спама\n\n"
                "Повторные нарушения могут привести к бану."
            )
            # Удаляем предупреждение через 30 секунд
            await asyncio.sleep(30)
            await warning_msg.delete()

            # Логируем действие
            logger.info(
                f"Удалено сообщение от {message.from_user.id}. "
                f"Найденные слова: {found_bad_words}. "
                f"Текст: {message.text[:100]}..."
            )

        except Exception as e:
            logger.error(f"Ошибка модерации: {e}")
