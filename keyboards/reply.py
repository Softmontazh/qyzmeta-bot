# Coding: utf-8
# keyboards/reply.py

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_keyboard(
    *btns: str,  # Кнопки клавиатуры
    placeholder: str = None,  # Плейсхолдер для ввода
    request_contact: int = None,  # Индекс кнопки, запрашивающей контакт
    request_location: int = None,  # Индекс кнопки, запрашивающей местоположение
    sizes: tuple[int] = (2,),  # Размеры кнопок (количество кнопок в строке)
):
    """Генерация клавиатуры с кнопками."""
    keyboard = ReplyKeyboardBuilder()

    for index, text in enumerate(btns, start=0):
        if request_contact is not None and request_contact == index:
            keyboard.add(KeyboardButton(text=text, request_contact=True))
        elif request_location is not None and request_location == index:
            keyboard.add(KeyboardButton(text=text, request_location=True))
        else:
            keyboard.add(KeyboardButton(text=text))

    return keyboard.adjust(*sizes).as_markup(
        resize_keyboard=True, input_field_placeholder=placeholder
    )


# Пользовательская клавиатура
USER_KB = get_keyboard(
    "🔎 Поиск лотов 🏷️",
    "➕ Добавить лот 🏷️",
    "📋 Мои лоты 🏷️",
    placeholder="Панель пользователя",
    sizes=(1, 2),
)

MAIN_KB = get_keyboard(
    "Создать заявку 📝",
    "Мои заявки 📝",
    "Мой профиль 👤",
    "Мой дом 🏢",
    placeholder="Основное меню",
    sizes=(1, 2, 1),
)


CONTROL_SERVICE_PROVIDER_KB = get_keyboard(
    "Список поставщиков услуг",
    "Добавить поставщика услуг",
    "Заявки на поставку услуг",
    "Заявки на партнерство",
    "Управление ЖК",
    "Главное меню",
    placeholder="Управление поставщиками услуг",
    sizes=(1, 1, 1, 1, 1, 1),
)

MANAGE_OFFER_STATUS_KB = get_keyboard(
    "Управление заявками 📋",
    "Мои сервисы в ЖК 📝",
    "Моя статистика 📊",
    "Выход из режима сервисника",
    placeholder="Управление заявками",
    sizes=(1, 1, 1, 1, 1),
)
