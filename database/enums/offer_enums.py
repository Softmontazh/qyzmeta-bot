# -*- coding: utf-8 -*-
# database/enums/offer_enums.py

from enum import Enum


class OfferStatus(Enum):
    """Статусы заявок"""
    ACTIVE = "active"           # Активная
    IN_PROGRESS = "in_progress" # В работе
    COMPLETED = "completed"     # Выполнена
    ARCHIVED = "archived"       # Архивная
    CANCELLED = "cancelled"     # Отменена

    @property
    def display_name(self) -> str:
        """Возвращает название статуса на русском языке"""
        names = {
            self.ACTIVE: "Активная",
            self.IN_PROGRESS: "В работе",
            self.COMPLETED: "Выполнена",
            self.ARCHIVED: "Архивная",
            self.CANCELLED: "Отменена"
        }
        return names.get(self, "Неизвестный статус")

    @property
    def emoji(self) -> str:
        """Возвращает эмодзи для статуса"""
        emojis = {
            self.ACTIVE: "🔔",
            self.IN_PROGRESS: "⏳",
            self.COMPLETED: "✅",
            self.ARCHIVED: "📦",
            self.CANCELLED: "❌"
        }
        return emojis.get(self, "📝")

    @classmethod
    def get_display_name(cls, status_value) -> str:
        """Получить отображаемое название по значению статуса"""
        if status_value is None:
            return "Не указан"
        
        if isinstance(status_value, cls):
            return status_value.display_name
        
        # Если передана строка, пытаемся найти соответствующий enum
        for status in cls:
            if status.value == status_value:
                return status.display_name
        
        return "Неизвестный статус"


class OfferCategory(Enum):
    """Категории заявок с русскими названиями"""
    DOMOFON = "domofon"
    ELECTRIKA = "electrika"
    SANTECHNIKA = "santechnika"
    BLAGOUSTROYSTVO = "blagoustroystvo"
    DRUGOE = "drugoe"

    @property
    def display_name(self) -> str:
        """Возвращает название категории на русском языке"""
        names = {
            self.DOMOFON: "Домофон",
            self.ELECTRIKA: "Электрика", 
            self.SANTECHNIKA: "Сантехника",
            self.BLAGOUSTROYSTVO: "Благоустройство",
            self.DRUGOE: "Другое"
        }
        return names.get(self, "Неизвестная категория")

    @property
    def emoji(self) -> str:
        """Возвращает эмодзи для категории"""
        emojis = {
            self.DOMOFON: "🔔",
            self.ELECTRIKA: "⚡",
            self.SANTECHNIKA: "🚿",
            self.BLAGOUSTROYSTVO: "🌳",
            self.DRUGOE: "🔧"
        }
        return emojis.get(self, "📝")

    @classmethod
    def from_string(cls, category_str: str):
        """Создаёт enum из строки"""
        for cat in cls:
            if cat.value == category_str.lower():
                return cat
        return cls.DRUGOE  # По умолчанию
