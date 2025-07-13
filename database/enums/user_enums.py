# -*- coding: utf-8 -*-
# Этот файл с перечислениями для пользователя
# Он используется для определения ролей и языков пользователя в системе
# database/enums/user_enums.py

from enum import Enum


class UserLanguage(str, Enum):
    RU = "ru"
    KZ = "kz"


class UserRole(str, Enum):
    CREATOR = "CREATOR"
    OWNER = "OWNER"
    GUEST = "GUEST"
    USER = "USER"
    ADMIN = "ADMIN"
    SUPERADMIN = "SUPERADMIN"
    MODERATOR = "MODERATOR"
    MANAGER = "MANAGER"
    SUPPORT = "SUPPORT"
    PARTNER = "PARTNER"
    SERVICE_PROVIDER = "SERVICE_PROVIDER"

    def get_russian_name(self):
        """Возвращает русское название роли"""
        role_names = {
            "CREATOR": "Создатель",
            "OWNER": "Владелец",
            "GUEST": "Гость",
            "USER": "Резидент",
            "ADMIN": "Администратор",
            "SUPERADMIN": "Суперадминистратор",
            "MODERATOR": "Модератор",
            "MANAGER": "Менеджер",
            "SUPPORT": "Поддержка",
            "PARTNER": "Партнер",
            "SERVICE_PROVIDER": "Поставщик услуг"
        }
        return role_names.get(self.value, self.value)
