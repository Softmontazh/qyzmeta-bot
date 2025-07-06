# -*- coding: utf-8 -*-


from aiogram.filters import BaseFilter
from aiogram import Bot, types


class ChatTypeFilter(BaseFilter):
    def __init__(self, chat_types: list[str]) -> None:
        self.chat_types = chat_types

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in self.chat_types


class IsAdmin(BaseFilter):
    def __init__(self):
        pass

    async def __call__(self, message: types.Message, bot: Bot) -> bool:
        print(f"сработал фильтр IsAdmin для {message.from_user.id}")
        print(f"список админов: {bot.my_admins_list}")
        return message.from_user.id in bot.my_admins_list
