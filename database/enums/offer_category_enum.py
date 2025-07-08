# -*- coding: utf-8 -*-
# database/enums/offer_category_enum.py

from enum import Enum


class OfferCategory(Enum):
    """Категории заявок с отображением на русском языке"""
    
    DOMOFON = ("domofon", "Домофон", "🔔")
    ELEKTRIKA = ("elektrika", "Электрика", "⚡")
    SANTEHNIKA = ("santehnika", "Сантехника", "🚿")
    BLAGOUSTROYSTVO = ("blagoustroystvo", "Благоустройство", "🌳")
    REPAIR = ("repair", "Ремонт", "🔧")
    DRUGOE = ("drugoe", "Другое", "📝")
    
    def __new__(cls, value: str, display_name: str, emoji: str):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.display_name = display_name
        obj.emoji = emoji
        return obj
    
    @classmethod
    def from_string(cls, category_str: str) -> "OfferCategory":
        """Получить enum по строковому значению"""
        for category in cls:
            if category.value == category_str.lower():
                return category
        return cls.DRUGOE  # По умолчанию, если не найдено
    
    @classmethod
    def get_display_name(cls, category_str: str) -> str:
        """Получить отображаемое название по строковому значению"""
        category = cls.from_string(category_str)
        return category.display_name
    
    @classmethod
    def get_emoji(cls, category_str: str) -> str:
        """Получить эмодзи по строковому значению"""
        category = cls.from_string(category_str)
        return category.emoji
