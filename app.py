import asyncio
import os

from aiogram import Bot, Dispatcher, types

import dotenv

dotenv.load_dotenv(dotenv.find_dotenv())

from middlewares.db import DataBaseSession

from database.engine import create_db, drop_db, session_maker

from handlers.user_private import user_private_router
from handlers.user_group import user_group_router
from handlers.admin_private import admin_router
from handlers.fsm.manage_jk_fsm import manage_jk_router
from handlers.fsm.manage_service_providers_fsm import manage_service_providers_router
from handlers.control_service_provider_kb import control_service_provider_router
from handlers.fsm.manage_offer_status_fsm import manage_offer_status_router
from handlers.offer_status_handlers import offer_status_router
from handlers.service_providers_view import router as service_providers_view_router
from handlers.service_provider_panel import service_provider_panel_router
from handlers.fsm.become_service_provider_fsm import become_service_provider_router
from handlers.offer_media_handlers import offer_media_router
from handlers.business_models import business_models_router
from handlers.subscription_management import subscription_management_router

# Импорт роутеров системы ролей
from handlers.platform_roles.admin_role_handler import router as admin_role_router
from handlers.platform_roles.partner_role_handler import router as partner_role_router
from handlers.platform_roles.moderator_role_handler import (
    router as moderator_role_router,
)
from handlers.fsm.role_application_fsm import router as role_application_router
from handlers.creator_moderation import router as creator_moderation_router
from services.bus_service import bus_service

from common.bot_cmds_list import cmds_list

token = os.getenv("TOKEN")
if token is None:
    raise ValueError("Environment variable 'TOKEN' is not set")
bot = Bot(token=token)

# Инициализируем bus_service
bus_service.initialize(bot)
my_admins_list = []  # список администраторов бота, будет заполняться при запуске

dp = Dispatcher()
# Подключаем роутеры
dp.include_router(
    user_private_router
)  # для личных сообщений от пользователей (включает add_offer_router)
dp.include_router(manage_jk_router)  # для управления ЖК (должен быть до user_group)
dp.include_router(manage_service_providers_router)  # для управления поставщиками услуг
dp.include_router(control_service_provider_router)  # для кнопок управления поставщиками
dp.include_router(service_providers_view_router)  # для просмотра поставщиков услуг
dp.include_router(
    become_service_provider_router
)  # для подачи заявок на статус поставщика услуг
dp.include_router(
    manage_offer_status_router
)  # для управления статусами заявок (до панели поставщика)
dp.include_router(
    service_provider_panel_router
)  # для панели управления поставщиков услуг
dp.include_router(offer_status_router)  # для управления статусами через кнопки
dp.include_router(offer_media_router)  # для работы с медиафайлами заявок через BUS
dp.include_router(
    business_models_router
)  # для управления бизнес-моделями (только создатели)
dp.include_router(subscription_management_router)  # для управления подписками и ценами

# Подключаем роутеры системы ролей
dp.include_router(admin_role_router)  # команда /is_admin
dp.include_router(partner_role_router)  # команда /is_partner
dp.include_router(moderator_role_router)  # команда /is_moderator
dp.include_router(role_application_router)  # FSM подачи заявок на роли
dp.include_router(creator_moderation_router)  # модерация заявок создателем

# Подключаем партнерскую панель
from handlers.partner_panel import partner_router

dp.include_router(partner_router)  # партнерская панель

dp.include_router(user_group_router)  # для групповых чатов
dp.include_router(admin_router)  # для личных сообщений от администраторов


async def on_startup():
    """Функция, которая выполняется при запуске бота"""
    """Создание базы данных и подключение к ней"""
    print("Бот запущен")
    print("Создание базы данных...")
    # Параметр для сброса базы данных
    # Если нужно сбросить базу данных, то установите run_param в True
    run_param = False  # Отключаем сброс, будем использовать другой подход
    if run_param:  # если нужно сбросить базу данных
        print("Сброс базы данных...")
        await drop_db()  # сброс базы данных
    await create_db()  # создание базы данных

    # Инициализируем цены подписок по умолчанию
    try:
        from database.migrations.init_default_prices import (
            initialize_default_subscription_prices,
        )

        async with session_maker() as session:
            await initialize_default_subscription_prices(session, created_by=0)
        print("✅ Инициализация цен подписок завершена")
    except Exception as e:
        print(f"⚠️ Предупреждение при инициализации цен: {e}")


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
