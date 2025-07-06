from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.enums.lot_enums import LotStatus
from common.callbacks import LotActions
from database.enums.user_enums import UserRole


# Функция для генерации Inline-клавиатуры с кнопками для добавления или поиска лотов
def get_btns_lots(
    btns: dict[str, str], row_sizes: list[int] = None, default_row_size: int = 2
) -> InlineKeyboardMarkup:
    """
    Генерирует Inline-клавиатуру с кнопками для добавления лота."""
    buttons = [
        InlineKeyboardButton(text=text, callback_data=data)
        for text, data in btns.items()
    ]
    keyboard = []
    idx = 0
    if row_sizes:
        for size in row_sizes:
            keyboard.append(buttons[idx : idx + size])
            idx += size
        if idx < len(buttons):
            keyboard.append(buttons[idx:])
    else:
        keyboard = [
            buttons[i : i + default_row_size]
            for i in range(0, len(buttons), default_row_size)
        ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Функция для генерации Inline-клавиатуры с кнопками для управления лотом
def get_btns_control_lots(
    lot_id: int, status: LotStatus, user_role: UserRole
) -> InlineKeyboardMarkup:
    """
    Генерирует Inline-клавиатуру с кнопками для управления лотом.
    Функция принимает идентификатор лота, статус лота, роль пользователя и идентификатор владельца лота.
    Возвращает объект InlineKeyboardMarkup с кнопками для управления лотом.

    :param lot_id: ID лота
    :param status: Статус лота
    :param user_role: Роль пользователя
    :return: InlineKeyboardMarkup с кнопками
    """

    buttons = []

    # Базовые кнопки (всегда видны)
    buttons.append(
        [
            InlineKeyboardButton(
                text="🗨️ Отзывы", callback_data=f"{LotActions.FEEDBACK}:{lot_id}"
            ),
        ]
    )

    # Кнопки для владельца лота
    if user_role == UserRole.USER:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="✏️ Изменить", callback_data=f"{LotActions.EDIT}:{lot_id}"
                ),
                InlineKeyboardButton(
                    text="🗑️ Удалить", callback_data=f"{LotActions.DELETE}:{lot_id}"
                ),
            ]
        )
        if status == LotStatus.ACTIVE:
            """
            Кнопки для активного лота, доступные владельцу.
            """
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="🚫 В архив",
                        callback_data=f"{LotActions.ARCHIVE}:{lot_id}",
                    ),  # должно быть archive_lot_123
                    InlineKeyboardButton(
                        text="🔁 Продлить", callback_data=f"{LotActions.RENEW}:{lot_id}"
                    ),
                ]
            )
            print(f"ARCHIVE BUTTON: {LotActions.ARCHIVE}{lot_id}")
        elif status == LotStatus.ARCHIVED:
            """
            Кнопки для архивного лота, доступные владельцу.
            """
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="✅ Активировать",
                        callback_data=f"{LotActions.ACTIVATE}:{lot_id}",
                    )
                ]
            )
        elif status == LotStatus.REJECTED:
            """
            Кнопки для отклоненного лота, доступные владельцу.
            """
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="✅ Подать снова",
                        callback_data=f"{LotActions.RESUBMIT}:{lot_id}",
                    )
                ]
            )

    # Кнопки модерации доступны для модераторов и администраторов
    elif user_role in (UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPERADMIN):
        """
        Кнопки модеррации и администрирования лота.
        """
        if status == LotStatus.MODERATION:
            # Кнопки для модерации лота
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="✅ Одобрить",
                        callback_data=f"{LotActions.APPROVE}:{lot_id}",
                    ),
                    InlineKeyboardButton(
                        text="❌ Отклонить",
                        callback_data=f"{LotActions.REJECT}:{lot_id}",
                    ),
                ]
            )
        elif status == LotStatus.COMPLAINT:
            # Кнопки для обработки жалобы
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="❌ Заблокировать",
                        callback_data=f"{LotActions.BLOCKING}:{lot_id}",
                    ),
                    InlineKeyboardButton(
                        text="✅ Разблокировать",
                        callback_data=f"{LotActions.UNBLOCKING}:{lot_id}",
                    ),
                ]
            )
        else:
            print("Неизвестный статус лота для администратора:", status)

    # Кнопки для пользователей, которые не являются владельцами лота
    else:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="📩 Написать владельцу",
                    callback_data=f"{LotActions.WRITE_TO_OWNER}:{lot_id}",
                ),
                InlineKeyboardButton(
                    text="⚠️ Пожаловаться", callback_data=f"{LotActions.REPORT}:{lot_id}"
                ),
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)
