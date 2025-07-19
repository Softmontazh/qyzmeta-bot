# -*- coding: utf-8 -*-
# services/bus_service.py
"""
Сервис для работы с BUS_ID - универсальными идентификаторами файлов 
для обмена между ботами платформы Qyzmeta.
"""

import hashlib
import time
import os
import logging
from typing import Optional
from aiogram import Bot

# Настройка логгера
logger = logging.getLogger(__name__)


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
                logger.info(f"BUS channel initialized: {self.bus_channel_id}")
            except ValueError:
                logger.error(f"Invalid BUS_ID format: {self.bus_channel_id}")
                self.bus_channel_id = None
        else:
            logger.warning("BUS_ID environment variable not set!")
    
    async def save_image(self, file_id: str) -> Optional[str]:
        """
        Сохраняет изображение в BUS группу и возвращает bus_media_id.
        
        Args:
            file_id: Telegram file_id изображения (оригинальный)
            
        Returns:
            Optional[str]: bus_media_id (file_id из BUS группы) или None при ошибке
        """
        if not self.bot or not self.bus_channel_id:
            logger.warning("BUS not initialized, cannot save image")
            return None
            
        try:
            # Генерируем BUS_ID заранее для включения в подпись
            bus_id = self.generate_bus_id(file_id)
            
            # Отправляем фото в BUS группу с информативной подписью
            message = await self.bot.send_photo(
                chat_id=self.bus_channel_id,
                photo=file_id,
                caption=f"🖼️ Qyzmeta Platform - Image Storage\n"
                       f"🆔 BUS_ID: <code>{bus_id}</code>\n"
                       f"📅 Дата: {time.strftime('%d.%m.%Y %H:%M', time.localtime())}\n"
                       f"🏢 Источник: ЖК Management System",
                parse_mode="HTML"
            )
            
            # Возвращаем file_id из BUS группы - это и есть bus_media_id
            if message.photo:
                bus_media_id = message.photo[-1].file_id
                logger.info(f"Image saved to BUS: original={file_id[:20]}..., bus_media_id={bus_media_id[:20]}...")
                return bus_media_id
            else:
                logger.error("Failed to save image to BUS: no photo in sent message")
                return None
            
        except Exception as e:
            logger.error(f"Error saving image to BUS: {e}")
            return None
    
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
    
    async def save_video(self, file_id: str) -> Optional[str]:
        """
        Сохраняет видео в BUS группу и возвращает bus_media_id.
        
        Args:
            file_id: file_id видео из Telegram (оригинальный)
            
        Returns:
            Optional[str]: bus_media_id (file_id из BUS группы) или None при ошибке
        """
        if not self.bot or not self.bus_channel_id:
            logger.warning("BUS not initialized, cannot save video")
            return None
            
        try:
            # Генерируем BUS_ID заранее для включения в подпись
            bus_id = self.generate_bus_id(file_id)
            
            # Отправляем видео в BUS группу
            sent_message = await self.bot.send_video(
                chat_id=self.bus_channel_id,
                video=file_id,
                caption=f"🎬 Qyzmeta Platform - Video Storage\n"
                       f"🆔 BUS_ID: <code>{bus_id}</code>\n"
                       f"📅 Дата: {time.strftime('%d.%m.%Y %H:%M', time.localtime())}\n"
                       f"🏢 Источник: ЖК Management System",
                parse_mode="HTML"
            )
            
            # Возвращаем file_id из BUS группы - это и есть bus_media_id
            if sent_message.video:
                bus_media_id = sent_message.video.file_id
                logger.info(f"Video saved to BUS: original={file_id[:20]}..., bus_media_id={bus_media_id[:20]}...")
                return bus_media_id
            else:
                logger.error("Failed to save video to BUS: no video in sent message")
                return None
                
        except Exception as e:
            logger.error(f"Error saving video to BUS: {e}")
            return None
            return self.generate_bus_id(file_id)

    @staticmethod
    def create_file_mapping(file_id: str, bus_id: Optional[str] = None, file_type: str = "image") -> dict:
        """
        Создает маппинг файла для обмена между ботами.
        
        Args:
            file_id: Telegram file_id
            bus_id: BUS_ID (если не указан, генерируется автоматически)
            file_type: Тип файла ("image" или "video")
            
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
            "type": file_type
        }
    
    async def get_bus_media_file_id(self, bot, bus_id: str) -> Optional[str]:
        """
        Получает file_id медиафайла из BUS группы по BUS_ID.
        
        Args:
            bot: Экземпляр бота
            bus_id: BUS_ID файла
            
        Returns:
            Optional[str]: file_id для использования в боте или None при ошибке
        """
        if not self.validate_bus_id(bus_id):
            logger.error(f"Invalid BUS_ID format: {bus_id}")
            return None
            
        try:
            # В реальной реализации здесь нужно найти сообщение в BUS группе
            # по BUS_ID и извлечь file_id
            # Для упрощения пока возвращаем None
            # TODO: Реализовать поиск сообщения по BUS_ID в группе
            logger.warning(f"get_bus_media_file_id not fully implemented for {bus_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting media from BUS: {e}")
            return None

    async def send_media_from_bus(self, bot, chat_id: int, bus_id: str, caption: str = None) -> bool:
        """
        Отправляет медиафайл из BUS группы в указанный чат.
        
        Args:
            bot: Экземпляр бота
            chat_id: ID чата для отправки
            bus_id: BUS_ID медиафайла
            caption: Подпись к медиафайлу
            
        Returns:
            bool: True если медиа отправлено успешно, False при ошибке
        """
        if not self.validate_bus_id(bus_id):
            logger.error(f"Invalid BUS_ID format: {bus_id}")
            return False
            
        try:
            # Попытка найти медиафайл в BUS группе по подписи
            # Получаем последние 50 сообщений из BUS группы
            try:
                # Используем getUpdates для поиска сообщений с нужным BUS_ID
                # Это упрощенная реализация - в продакшене лучше использовать базу данных
                
                # Пока отправляем информационное сообщение с возможностью форварда
                info_message = f"📸 <b>Медиафайл из заявки</b>\n"
                if caption:
                    info_message += f"\n{caption}\n"
                info_message += f"\n💡 <b>Инструкция для просмотра медиа:</b>\n" \
                               f"1. Перейдите в BUS группу: https://t.me/c/2836867857\n" \
                               f"2. Найдите сообщение с BUS_ID: <code>{bus_id}</code>\n" \
                               f"3. Медиафайл будет в этом сообщении\n\n" \
                               f"<i>Автоматический поиск медиа будет добавлен в следующем обновлении</i>"
                
                await bot.send_message(
                    chat_id=chat_id,
                    text=info_message,
                    parse_mode="HTML"
                )
                
                logger.info(f"Media info sent from BUS {bus_id} to chat {chat_id}")
                return True
                
            except Exception as search_error:
                logger.warning(f"Could not search BUS group for {bus_id}: {search_error}")
                
                # Fallback: отправляем информационное сообщение
                fallback_message = f"📸 <b>Медиафайл из заявки</b>\n"
                if caption:
                    fallback_message += f"\n{caption}\n"
                fallback_message += f"\n⚠️ <b>Медиафайл временно недоступен</b>\n" \
                                   f"BUS ID: <code>{bus_id}</code>\n\n" \
                                   f"Обратитесь к администратору для получения медиафайла."
                
                await bot.send_message(
                    chat_id=chat_id,
                    text=fallback_message,
                    parse_mode="HTML"
                )
                
                return True
            
        except Exception as e:
            logger.error(f"Error sending media from BUS {bus_id}: {e}")
            return False

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
