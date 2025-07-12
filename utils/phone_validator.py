# -*- coding: utf-8 -*-
# utils/phone_validator.py
"""
Утилита для валидации и форматирования телефонных номеров
Поддерживает различные форматы ввода и приводит к единому стандарту
"""

import re
from typing import Optional, Tuple


class PhoneValidator:
    """Класс для валидации и форматирования телефонных номеров"""
    
    # Регулярные выражения для разных форматов номеров
    PHONE_PATTERNS = [
        # Казахстанские номера
        r'^(\+7|8|7)?[\s\-\(\)]?(\d{3})[\s\-\(\)]?(\d{3})[\s\-\(\)]?(\d{2})[\s\-\(\)]?(\d{2})$',  # +7 701 123 45 67
        r'^(\+7|8|7)?[\s\-\(\)]?(\d{3})[\s\-\(\)]?(\d{3})[\s\-\(\)]?(\d{4})$',  # +7 701 123 4567
        r'^(\+7|8|7)?[\s\-\(\)]?(\d{10})$',  # 77011234567
        
        # Российские номера  
        r'^(\+7|8|7)?[\s\-\(\)]?(\d{3})[\s\-\(\)]?(\d{3})[\s\-\(\)]?(\d{2})[\s\-\(\)]?(\d{2})$',  # +7 911 123 45 67
        
        # Международные номера (упрощенный формат)
        r'^(\+\d{1,3})[\s\-\(\)]?(\d{3,4})[\s\-\(\)]?(\d{3,4})[\s\-\(\)]?(\d{2,4})$',  # +1 234 567 8901
        
        # Просто цифры (10-15 символов)
        r'^(\d{10,15})$',  # 77011234567
    ]
    
    @classmethod
    def clean_phone(cls, phone: str) -> str:
        """Очистить номер от всех символов кроме цифр и +"""
        if not phone:
            return ""
        
        # Убираем все символы кроме цифр и +
        cleaned = re.sub(r'[^\d+]', '', phone.strip())
        
        return cleaned
    
    @classmethod
    def validate_and_format(cls, phone: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Валидация и форматирование номера телефона
        
        Args:
            phone: Входящий номер в любом формате
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (is_valid, formatted_phone, error_message)
        """
        if not phone or not phone.strip():
            return False, None, "Номер телефона не может быть пустым"
        
        # Очищаем номер
        cleaned = cls.clean_phone(phone)
        
        if not cleaned:
            return False, None, "Номер должен содержать цифры"
        
        # Проверяем минимальную длину
        if len(cleaned) < 10:
            return False, None, "Номер слишком короткий (минимум 10 цифр)"
        
        if len(cleaned) > 15:
            return False, None, "Номер слишком длинный (максимум 15 цифр)"
        
        # Пытаемся распознать и отформатировать номер
        formatted = cls._format_phone(cleaned)
        
        if formatted:
            return True, formatted, None
        else:
            return False, None, "Неверный формат номера телефона"
    
    @classmethod
    def _format_phone(cls, cleaned_phone: str) -> Optional[str]:
        """Форматирование очищенного номера"""
        
        # Обрабатываем номера с кодом страны
        if cleaned_phone.startswith('+7') or cleaned_phone.startswith('87') or cleaned_phone.startswith('77'):
            return cls._format_kz_ru_phone(cleaned_phone)
        elif cleaned_phone.startswith('8') and len(cleaned_phone) == 11:
            return cls._format_kz_ru_phone(cleaned_phone)
        elif cleaned_phone.startswith('+'):
            return cls._format_international_phone(cleaned_phone)
        elif len(cleaned_phone) == 10:
            # Возможно казахстанский номер без кода страны
            return cls._format_kz_ru_phone('7' + cleaned_phone)
        elif len(cleaned_phone) == 11 and cleaned_phone.startswith('7'):
            return cls._format_kz_ru_phone(cleaned_phone)
        else:
            # Пытаемся как международный
            return cls._format_international_phone('+' + cleaned_phone)
    
    @classmethod
    def _format_kz_ru_phone(cls, phone: str) -> str:
        """Форматирование казахстанских/российских номеров"""
        # Убираем + если есть
        if phone.startswith('+'):
            phone = phone[1:]
        
        # Заменяем 8 на 7 в начале
        if phone.startswith('8'):
            phone = '7' + phone[1:]
        
        # Добавляем 7 если номер начинается не с 7
        if not phone.startswith('7'):
            phone = '7' + phone
        
        # Форматируем как +7 XXX XXX XX XX
        if len(phone) == 11:
            return f"+{phone[0]} {phone[1:4]} {phone[4:7]} {phone[7:9]} {phone[9:11]}"
        
        return f"+{phone}"
    
    @classmethod
    def _format_international_phone(cls, phone: str) -> str:
        """Форматирование международных номеров"""
        if not phone.startswith('+'):
            phone = '+' + phone
        
        # Простое форматирование для международных номеров
        digits = phone[1:]  # Убираем +
        
        if len(digits) >= 10:
            # Стандартное форматирование
            return f"+{digits[:2]} {digits[2:5]} {digits[5:8]} {digits[8:]}"
        
        return phone
    
    @classmethod
    def is_valid_phone(cls, phone: str) -> bool:
        """Быстрая проверка валидности номера"""
        is_valid, _, _ = cls.validate_and_format(phone)
        return is_valid
    
    @classmethod
    def format_phone(cls, phone: str) -> Optional[str]:
        """Получить отформатированный номер или None"""
        is_valid, formatted, _ = cls.validate_and_format(phone)
        return formatted if is_valid else None
    
    @classmethod
    def get_examples(cls) -> list[str]:
        """Получить примеры корректных форматов"""
        return [
            "+7 701 123 45 67",
            "+7 777 123 45 67", 
            "+7 (701) 123-45-67",
            "8 701 123 45 67",
            "77011234567",
            "+1 234 567 8901"
        ]


# Функции-хелперы для удобства использования
def validate_phone(phone: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Валидация номера телефона"""
    return PhoneValidator.validate_and_format(phone)


def format_phone(phone: str) -> Optional[str]:
    """Форматирование номера телефона"""
    return PhoneValidator.format_phone(phone)


def is_valid_phone(phone: str) -> bool:
    """Проверка валидности номера"""
    return PhoneValidator.is_valid_phone(phone)


# Тестирование модуля
if __name__ == "__main__":
    test_phones = [
        "+7 701 123 45 67",
        "8 701 123 45 67", 
        "77011234567",
        "7 (701) 123-45-67",
        "+7(701)123-45-67",
        "701 123 45 67",
        "87011234567",
        "+1 234 567 8901",
        "invalid phone",
        "123",
        "+7 701 123 45 67 890",  # слишком длинный
    ]
    
    print("🔧 Тестирование PhoneValidator:")
    print()
    
    for phone in test_phones:
        is_valid, formatted, error = PhoneValidator.validate_and_format(phone)
        status = "✅" if is_valid else "❌"
        result = formatted if is_valid else error
        print(f"{status} '{phone}' → {result}")
