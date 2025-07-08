# -*- coding: utf-8 -*-


from aiogram.filters import BaseFilter
from aiogram import Bot, types
import os


class ChatTypeFilter(BaseFilter):
    def __init__(self, chat_types: list[str]) -> None:
        self.chat_types = chat_types

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in self.chat_types


class IsAdmin(BaseFilter):
    def __init__(self):
        # Получаем список админов из переменных окружения
        owner_ids = os.getenv('OWNER_ID', '').split(',')
        creator_ids = os.getenv('CREATOR_ID', '').split(',')
        
        # Объединяем списки и конвертируем в int, убираем пустые строки
        admin_ids = []
        for id_str in owner_ids + creator_ids:
            if id_str.strip():
                try:
                    admin_ids.append(int(id_str.strip()))
                except ValueError:
                    continue
        
        self.admin_ids = list(set(admin_ids))  # Убираем дубликаты

    async def __call__(self, message: types.Message, bot: Bot) -> bool:
        print(f"сработал фильтр IsAdmin для {message.from_user.id}")
        print(f"список админов: {self.admin_ids}")
        return message.from_user.id in self.admin_ids
