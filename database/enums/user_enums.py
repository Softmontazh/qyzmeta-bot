# -*- coding: utf-8 -*-
# Этот файл с перечислениями для пользователя
# Он используется для определения ролей и языков пользователя в системе
# database/enums/user_enums.py

from enum import Enum


class UserLanguage(str, Enum):
    RU = "ru"
    KZ = "kz"


class UserRole(str, Enum):
    CREATOR = "creator"
    OWNER = "owner"
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"
    MODERATOR = "moderator"
    MANAGER = "manager"
    SUPPORT = "support"
    PARTNER = "partner"

    def get_russian_name(self):
        """Возвращает русское название роли"""
        role_names = {
            "creator": "Создатель",
            "owner": "Владелец",
            "guest": "Гость",
            "user": "Резидент",
            "admin": "Администратор",
            "superadmin": "Суперадминистратор",
            "moderator": "Модератор",
            "manager": "Менеджер",
            "support": "Поддержка",
            "partner": "Партнер"
        }
        return role_names.get(self.value, self.value)
