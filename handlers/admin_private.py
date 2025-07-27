# coding: utf-8
# handlers/admin_private.py
"""
Обработчики для админов групповых чатов ЖК.
Когда жители создают группы для ЖК, админы группы получают расширенные возможности.
"""

from aiogram import F, Router, types
from aiogram.filters import Command

from filters.chat_types import ChatTypeFilter, IsAdmin
from keyboards.reply import get_keyboard, USER_KB


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


ADMIN_KB = get_keyboard(
    "🕵️‍♂️ Лоты на модерации",
    "🚨 Лоты с жалобами", 
    " Выйти из админки",
    placeholder="Админ панель ЖК",
    sizes=(
        2,
        1,
    ),
)


# Обработчик команды /admin
@admin_router.message(Command("admin"))
async def adm_chat(message: types.Message):
    """Админ панель для админов групп ЖК"""
    print(f"это админка ЖК {message.from_user.id}")
    await message.answer("Вы в админке ЖК", reply_markup=ADMIN_KB)


# Обработчик нажатия на кнопку "🚪 Выйти из админки"
@admin_router.message(F.text.lower().contains("выйти из админки"))
@admin_router.message(Command("exit_admin"))
async def exit_admin(message: types.Message):
    """Выход из админки ЖК"""
    print(f"выход из админки ЖК {message.from_user.id}")
    await message.answer("Вы вышли из админки ЖК", reply_markup=USER_KB)
    await message.delete()
    await message.answer("Вы можете вернуться в админку ЖК, через команду /admin")


# ==================== ЗДЕСЬ БУДЕТ ФУНКЦИОНАЛ ДЛЯ АДМИНОВ ГРУПП ЖК ====================

# TODO: Добавить обработчики для:
# - Модерации лотов в ЖК
# - Управления жалобами
# - Статистики по группе ЖК
# - Управления участниками группы
