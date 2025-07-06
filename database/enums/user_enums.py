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
