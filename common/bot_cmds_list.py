from aiogram.types import BotCommand


cmds_list = [
    BotCommand(command="settings", description="Настройки бота"),
    BotCommand(command="help", description="Помощь"),
    BotCommand(command="start", description="Перезагрузить бота"),
    BotCommand(command="policy", description="Политика конфиденциальности"),
    BotCommand(command="support", description="Поддержка бота"),
    BotCommand(command="is_service", description="Я сервисник"),
]
