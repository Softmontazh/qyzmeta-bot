"""
Модуль для создания inline-клавиатур с помощью aiogram.
Функции:
---------
get_callback_btns(*, btns: dict[str, str], sizes: tuple[int] = (2,))
    Создаёт inline-клавиатуру, где каждая кнопка отправляет callback_data.
    Аргументы:
        btns: Словарь, где ключ — текст кнопки, значение — callback_data.
        sizes: Кортеж, определяющий количество кнопок в строке (по умолчанию 2).
    Возвращает:
        Объект InlineKeyboardMarkup.
get_url_btns(*, btns: dict[str, str], sizes: tuple[int] = (2,))
    Создаёт inline-клавиатуру, где каждая кнопка содержит ссылку (url).
    Аргументы:
        btns: Словарь, где ключ — текст кнопки, значение — url.
        sizes: Кортеж, определяющий количество кнопок в строке (по умолчанию 2).
    Возвращает:
        Объект InlineKeyboardMarkup.
get_inlineMix_btns(*, btns: dict[str, str], sizes: tuple[int] = (2,))
    Создаёт inline-клавиатуру, где кнопки могут быть как с callback_data, так и с url.
    Если значение содержит '://', кнопка будет url-кнопкой, иначе — callback-кнопкой.
    Аргументы:
        btns: Словарь, где ключ — текст кнопки, значение — url или callback_data.
        sizes: Кортеж, определяющий количество кнопок в строке (по умолчанию 2).
    Возвращает:
        Объект InlineKeyboardMarkup.
"""
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_callback_btns(
    *,
    btns: dict[str, str],
    sizes: tuple[int] = (2,)):

    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()


def get_url_btns(
    *,
    btns: dict[str, str],
    sizes: tuple[int] = (2,)):

    keyboard = InlineKeyboardBuilder()

    for text, url in btns.items():
        
        keyboard.add(InlineKeyboardButton(text=text, url=url))

    return keyboard.adjust(*sizes).as_markup()


#Создать микс из CallBack и URL кнопок
def get_inlineMix_btns(
    *,
    btns: dict[str, str],
    sizes: tuple[int] = (2,)):

    keyboard = InlineKeyboardBuilder()

    for text, value in btns.items():
        if '://' in value:
            keyboard.add(InlineKeyboardButton(text=text, url=value))
        else:
            keyboard.add(InlineKeyboardButton(text=text, callback_data=value))

    return keyboard.adjust(*sizes).as_markup()