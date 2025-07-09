# -*- coding: utf-8 -*-
# services/bus_service.py
"""
Сервис для работы с BUS_ID - универсальными идентификаторами файлов 
для обмена между ботами платформы Qyzmeta.
"""

import hashlib
import time
import os
from typing import Optional
from aiogram import Bot


class BUSService:
    """Сервис для создания и управления BUS_ID."""
    
    def __init__(self):
        self.bot: Optional[Bot] = None
        self.bus_channel_id: Optional[int] = None
        
    def initialize(self, bot: Bot):
        """Инициализация сервиса с ботом."""
        self.bot = bot
        self.bus_channel_id = os.getenv("BUS_ID")
        if self.bus_channel_id:
            try:
                self.bus_channel_id = int(self.bus_channel_id)
            except ValueError:
                self.bus_channel_id = None
    
    async def save_image(self, file_id: str) -> Optional[str]:
        """
        Сохраняет изображение в общий канал и возвращает BUS_ID.
        
        Args:
            file_id: Telegram file_id изображения
            
        Returns:
            Optional[str]: BUS_ID или None при ошибке
        """
        if not self.bot or not self.bus_channel_id:
            # Если нет настроек - просто генерируем BUS_ID
            return self.generate_bus_id(file_id)
            
        try:
            # Генерируем BUS_ID заранее для включения в подпись
            bus_id = self.generate_bus_id(file_id)
            
            # Отправляем фото в общий канал с информативной подписью
            message = await self.bot.send_photo(
                chat_id=self.bus_channel_id,
                photo=file_id,
                caption=f"🖼️ Qyzmeta Platform - Image Storage\n"
                       f"🆔 BUS_ID: <code>{bus_id}</code>\n"
                       f"📅 Дата: {time.strftime('%d.%m.%Y %H:%M', time.localtime())}\n"
                       f"🏢 Источник: ЖК Management System",
                parse_mode="HTML"
            )
            
            # В будущем здесь можно сохранять маппинг BUS_ID -> message_id
            return bus_id
            
        except Exception as e:
            print(f"Ошибка при сохранении изображения в BUS канал: {e}")
            # Возвращаем сгенерированный BUS_ID даже при ошибке
            return self.generate_bus_id(file_id)
    
    @staticmethod
    def generate_bus_id(file_id: str, bot_id: str = "qyzmeta_housing") -> str:
        """
        Генерирует BUS_ID на основе file_id и bot_id.
        
        Args:
            file_id: Telegram file_id
            bot_id: Идентификатор бота (по умолчанию qyzmeta_housing)
            
        Returns:
            str: Уникальный BUS_ID
        """
        # Создаем уникальный хеш на основе file_id, bot_id и времени
        timestamp = str(int(time.time()))
        source_data = f"{bot_id}:{file_id}:{timestamp}"
        hash_obj = hashlib.sha256(source_data.encode())
        
        # Берем первые 16 символов хеша и добавляем префикс
        bus_id = f"BUS_{hash_obj.hexdigest()[:16].upper()}"
        return bus_id
    
    @staticmethod
    def validate_bus_id(bus_id: str) -> bool:
        """
        Проверяет корректность формата BUS_ID.
        
        Args:
            bus_id: BUS_ID для проверки
            
        Returns:
            bool: True если формат корректен
        """
        if not bus_id or not isinstance(bus_id, str):
            return False
            
        # Проверяем формат: BUS_ + 16 символов (A-F, 0-9)
        if not bus_id.startswith("BUS_"):
            return False
            
        if len(bus_id) != 20:  # BUS_ (4) + hash (16)
            return False
            
        hash_part = bus_id[4:]
        return all(c in "0123456789ABCDEF" for c in hash_part)
    
    @staticmethod
    def create_file_mapping(file_id: str, bus_id: Optional[str] = None) -> dict:
        """
        Создает маппинг файла для обмена между ботами.
        
        Args:
            file_id: Telegram file_id
            bus_id: BUS_ID (если не указан, генерируется автоматически)
            
        Returns:
            dict: Словарь с информацией о файле
        """
        if not bus_id:
            bus_id = BUSService.generate_bus_id(file_id)
            
        return {
            "file_id": file_id,
            "bus_id": bus_id,
            "created_at": int(time.time()),
            "platform": "qyzmeta",
            "type": "image"
        }
    
    @staticmethod
    def extract_bot_id_from_bus(bus_id: str) -> Optional[str]:
        """
        Извлекает информацию о боте из BUS_ID (если возможно).
        
        Args:
            bus_id: BUS_ID
            
        Returns:
            Optional[str]: Идентификатор бота или None
        """
        if not BUSService.validate_bus_id(bus_id):
            return None
            
        # В текущей реализации bot_id не кодируется в BUS_ID
        # Это можно расширить в будущем
        return "qyzmeta_platform"


# Глобальный экземпляр сервиса
bus_service = BUSService()
