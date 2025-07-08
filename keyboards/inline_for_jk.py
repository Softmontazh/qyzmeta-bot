from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import case

from common.callbacks import JKActions


# Функция для генерации Inline-клавиатуры с кнопками для управления жилищным комплексом (ЖК)
def get_btns_control_jk(
    jk_id: int, is_resident: bool, is_admin: bool, is_uk: bool, is_service: bool
) -> InlineKeyboardMarkup:

    buttons = []

    if is_resident:
        buttons.append(
            InlineKeyboardButton(
                "Отменить регистрацию в ЖК",
                callback_data=f"{JKActions.CANCEL_REGISTRATION}:{jk_id}",
            ),
            InlineKeyboardButton(
                "Информация о ЖК", callback_data=f"{JKActions.INFO}:{jk_id}"
            ),
        )
    elif is_admin:
        buttons.append(
            InlineKeyboardButton(
                "Управление ЖК", callback_data=f"{JKActions.MANAGE}:{jk_id}"
            ),
        )
    elif is_uk:
        buttons.append(
            InlineKeyboardButton(
                "Управление ЖК", callback_data=f"{JKActions.MANAGE}:{jk_id}"
            ),
        )
    elif is_service:
        buttons.append(
            InlineKeyboardButton(
                "Управление ЖК", callback_data=f"{JKActions.MANAGE}:{jk_id}"
            ),
        )
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    return keyboard


""" Функция для создания Inline-клавиатуры с кнопкой для отмены регистрации в ЖК """


def unlink_keyboard(id_user_jk: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Отменить регистрацию", callback_data=f"unlink:{id_user_jk}"
                )
            ]
        ]
    )


""" Функция для создания клавиатуры управления ЖК """


def get_jk_management_keyboard(jk_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать", 
                    callback_data=f"edit_jk:{jk_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑️ Удалить", 
                    callback_data=f"delete_jk:{jk_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад", 
                    callback_data="back_to_jk_list"
                )
            ]
        ]
    )
