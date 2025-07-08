import asyncio
import os

from aiogram import Bot, Dispatcher, types

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

from middlewares.db import DataBaseSession

from database.engine import create_db, drop_db, session_maker

from handlers.user_private import user_private_router
from handlers.user_group import user_group_router
from handlers.admin_private import admin_router

from common.bot_cmds_list import cmds_list

token = os.getenv("TOKEN")
if token is None:
    raise ValueError("Environment variable 'TOKEN' is not set")
bot = Bot(token=token)
my_admins_list = []  # список администраторов бота, будет заполняться при запуске

dp = Dispatcher()

# Подключаем роутеры
dp.include_router(user_private_router)  # для личных сообщений от пользователей
dp.include_router(user_group_router)  # для групповых чатов
dp.include_router(admin_router)  # для личных сообщений от администраторов


async def on_startup():
    """Функция, которая выполняется при запуске бота"""
    """Создание базы данных и подключение к ней"""
    print("Бот запущен")
    print("Создание базы данных...")
    # Параметр для сброса базы данных
    # Если нужно сбросить базу данных, то установите run_param в True
    run_param = False
    if run_param:  # если нужно сбросить базу данных
        print("Сброс базы данных...")
        await drop_db()  # сброс базы данных
    await create_db()  # создание базы данных


"""Создание базы данных завершено"""
print("База данных создана и подключена")


async def on_shutdown(dispatcher: Dispatcher):
    print("Бот умер")


async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    await bot.delete_webhook(drop_pending_updates=True)
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    await bot.set_my_commands(
        commands=cmds_list, scope=types.BotCommandScopeAllPrivateChats()
    )
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


asyncio.run(main())
