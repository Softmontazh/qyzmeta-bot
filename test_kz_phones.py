#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование PhoneValidator с казахстанскими номерами
"""

from utils.phone_validator import validate_phone, PhoneValidator

print('🔧 Тестирование валидатора с казахстанскими номерами:')
print()

test_phones = [
    '77011234567',
    '+77011234567', 
    '87011234567',
    '8 701 123 45 67',
    '+7 (701) 123-45-67',
    '701 123 45 67',
    '+7701123-45-67',
    '7-701-123-45-67',
    '+7 778 123 45 67',  # мобильный
    '+7 727 123 45 67',  # городской Алматы
    '777-888-99-00',
    '+7 777 888 99 00',  # другой мобильный
    '+7 747 123 45 67',  # Beeline
    '+7 775 123 45 67',  # Tele2
    'неправильный номер',
    '123',
    '+7 701',
    '701123456789012',  # слишком длинный
]

print("Формат вывода: [статус] 'входной номер' → результат")
print()

for phone in test_phones:
    is_valid, formatted, error = validate_phone(phone)
    status = '✅' if is_valid else '❌'
    result = formatted if is_valid else error
    print(f'{status} "{phone}" → {result}')

print()
print("📋 Примеры поддерживаемых форматов:")
print(PhoneValidator.get_examples())
