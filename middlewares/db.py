"""
Модуль middlewares.db предоставляет промежуточное ПО (middleware) для работы с асинхронными сессиями базы данных в aiogram.
Классы:
    DataBaseSession:
        Middleware для автоматического создания и передачи асинхронной сессии SQLAlchemy в обработчики событий Telegram.
        Аргументы конструктора:
            session_pool (async_sessionmaker): Пул асинхронных сессий SQLAlchemy.
        Методы:
            __call__: Создаёт новую сессию, добавляет её в словарь данных (data["session"]), затем вызывает обработчик события.
    CounterMiddleware (закомментирован):
        Пример middleware для подсчёта количества обработанных сообщений.
        Аргументы конструктора:
            Нет.
        Методы:
            __call__: Увеличивает счётчик при каждом вызове и добавляет его в словарь данных (data['counter']).
"""
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker


class DataBaseSession(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)


# class CounterMiddleware(BaseMiddleware):
#     def __init__(self) -> None:
#         self.counter = 0

#     async def __call__(
#         self,
#         handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
#         event: Message,
#         data: Dict[str, Any]
#     ) -> Any:
#         self.counter += 1
#         data['counter'] = self.counter
#         return await handler(event, data)
