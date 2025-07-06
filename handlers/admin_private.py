# coding: utf-8
# handlers/admin_private.py

from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter

from filters.chat_types import ChatTypeFilter, IsAdmin

from keyboards.reply import get_keyboard, USER_KB


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())

ADMIN_KB = get_keyboard(
    "🕵️‍♂️ Лоты на модерации",
    "🚨 Лоты с жалобами",
    "🚪 Выйти из админки",
    placeholder="Админ панель",
    sizes=(
        2,
        1,
    ),
)


# Обработчик команды /admin
@admin_router.message(Command("admin"))
async def adm_chat(message: types.Message):
    print(f"это админка {message.from_user.id}")
    await message.answer("Вы в админке", reply_markup=ADMIN_KB)


# Обработчик нажатия на кнопку "🚪 Выйти из админки"
@admin_router.message(F.text.lower().contains("выйти из админки"))
@admin_router.message(Command("exit_admin"))
async def exit_admin(message: types.Message):
    print(f"выход из админки {message.from_user.id}")
    await message.answer("Вы вышли из админки", reply_markup=USER_KB)
    await message.delete()
    await message.answer("Вы можете вернуться в админку, через команду /admin")
