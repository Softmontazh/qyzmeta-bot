# code: utf-8
# database/enums/lot_enums.py
"""Енумации для лотов (предложений) в базе данных."""

import enum


class LotOfferType(enum.Enum):
    """Типы предложений для лотов в системе."""

    BUY = "buy"  # Купить
    SELL = "sell"  # Продать
    EXCHANGE = "exchange"  # Обмен
    GIVEAWAY = "giveaway"  # Отдам даром
    RENT = "rent"  # Арендую
    RENTOUT = "rentout"  # Сдам в аренду
    REQUEST = "request"  # Запрос
    SUGGEST = "suggest"  # Предложение


class LotStatus(enum.Enum):
    """Статусы лотов в системе."""

    ACTIVE = "active"  # Активный
    ARCHIVED = "archived"  # Архивный
    MODERATION = "moderation"  # На модерации
    REJECTED = "rejected"  # Отклоненный
    COMPLAINT = "complaint"  # С жалобой


class LotVisibility(enum.Enum):
    """Видимость лотов в системе."""

    PUBLIC = "public"  # Публичный
    PRIVATE = "private"  # Приватный
    GROUP = "group"  # Групповой
