"""
Обновляет сообщение с прогрессом добавления лота в чате.
Функция получает данные состояния FSM, извлекает идентификаторы чата и сообщения,
формирует текст с текущими данными лота и обновляет соответствующее сообщение в чате.
Если идентификаторы отсутствуют, функция завершает выполнение.
В случае ошибки при обновлении сообщения выводит сообщение об ошибке в консоль.
Аргументы:
    bot (Bot): Экземпляр бота Aiogram.
    state (FSMContext): Контекст состояния FSM, содержащий данные о прогрессе.
Исключения:
    Любые исключения при обновлении сообщения обрабатываются и выводятся в консоль.
"""

from aiogram import Bot
from aiogram.fsm.context import FSMContext


async def update_addlot_progress(bot: Bot, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("progress_chat_id")
    message_id = data.get("progress_message_id")
    if not chat_id or not message_id:
        return

    text = (
        "➕ Добавление лота 🏷️\n" + "_" * 24 + "\n"
        f"📌 Тип предложения: {data.get('offer_type', '—')}\n"
        f"📦 Тип лота: {data.get('type_lot', '—')}\n"
        f"📝 Название: {data.get('name_lot', '—')}\n"
        f"💰 Цена: {data.get('price', '—')}\n"
        f"🌏 Город: {data.get('city', '—')}\n"
        f"📞 Телефон: {data.get('phone', '—')}\n"
    )

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"Не удалось обновить сообщение прогресса: {e}")
