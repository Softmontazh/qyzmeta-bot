# 🏢 Модель JKServiceProvider - Обслуживающие организации ЖК

> **Файл**: `database/models/model_jk_service_provider.py`  
> **Таблица**: `jk_service_providers`  
> **Назначение**: Привязка ЖК к обслуживающим организациям по категориям услуг

## 📋 **Описание**

Модель управляет привязкой жилищных комплексов к поставщикам услуг по различным категориям (домофон, электрика, сантехника и т.д.). Каждая запись представляет ответственную организацию или лицо за определенную категорию услуг в конкретном ЖК.

## 🏗️ **Структура таблицы**

### **🔑 Основные поля:**
- `id` - Первичный ключ
- `uuid` - Уникальный идентификатор для API
- `jk_id` - Ссылка на ЖК (FK to jks.id)
- `category` - Категория услуг (enum OfferCategory)
- `responsible_user_id` - Ответственное лицо (FK to users.user_id)

### **📞 Контактная информация:**
- `organization_name` - Название организации/компании
- `contact_phone` - Контактный телефон
- `contact_email` - Контактный email

### **⚙️ Настройки работы:**
- `is_active` - Активна ли привязка
- `receives_notifications` - Получает ли уведомления о заявках
- `auto_assign_offers` - Автоматически назначать заявки этой категории
- `priority` - Приоритет (1 - высший)

### **🕐 Рабочее время:**
- `work_hours_start` - Начало рабочего дня (HH:MM)
- `work_hours_end` - Конец рабочего дня (HH:MM)
- `work_days` - Рабочие дни (битовая маска: пн=1, вт=2, ср=4...)

### **📋 Дополнительная информация:**
- `description` - Описание услуг или специализации
- `contract_number` - Номер договора обслуживания
- `contract_start_date` - Дата начала договора
- `contract_end_date` - Дата окончания договора

### **🔧 Служебные поля:**
- `created_at`, `updated_at` - Временные метки
- `created_by_user_id` - Кто создал запись

## 🔗 **Связи**

- **JK (1:N)** - Один ЖК может иметь много поставщиков услуг
- **User** - Ссылка на ответственного пользователя (без жёсткой связи)

## 🎯 **Категории услуг (OfferCategory)**

- `DOMOFON` - Домофон 🔔
- `VIDEO` - Видеонаблюдение 📹
- `ELEKTRIKA` - Электрика ⚡
- `SANTEHNIKA` - Сантехника 🚿
- `BLAGOUSTROYSTVO` - Благоустройство 🌳
- `REPAIR` - Ремонт 🔧
- `DRUGOE` - Другое 📝

## 🛠️ **Методы модели**

### **Свойства:**
- `category_display_name` - Отображаемое название категории
- `category_emoji` - Эмодзи категории
- `is_contract_active` - Активен ли договор на текущую дату

### **Методы:**
- `is_working_now()` - Работает ли поставщик услуг сейчас

## 📊 **ORM функции (orm_jk_service_provider.py)**

### **Создание и получение:**
- `orm_add_service_provider()` - Добавить поставщика услуг
- `orm_get_service_provider_by_id()` - Получить по ID
- `orm_get_service_provider_by_uuid()` - Получить по UUID

### **Поиск по ЖК и категориям:**
- `orm_get_service_providers_by_jk()` - Все поставщики ЖК
- `orm_get_service_provider_by_category()` - По категории (приоритетный)
- `orm_get_service_providers_by_user()` - Услуги пользователя

### **Управление:**
- `orm_update_service_provider()` - Обновить данные
- `orm_deactivate_service_provider()` - Деактивировать (мягкое удаление)
- `orm_delete_service_provider()` - Полное удаление

### **Вспомогательные:**
- `orm_get_responsible_for_offer_category()` - Получить ответственного за категорию
- `orm_check_user_manages_category()` - Проверить права управления
- `orm_get_categories_managed_by_user()` - Категории пользователя
- `orm_get_working_providers_now()` - Работающие сейчас

## 🎯 **Примеры использования**

### **Добавление поставщика услуг:**
```python
service_data = {
    "jk_id": 1,
    "category": OfferCategory.ELEKTRIKA,
    "responsible_user_id": 123456789,
    "organization_name": "ЭлектроСервис ТОО",
    "contact_phone": "+7 701 123 45 67",
    "priority": 1,
    "work_hours_start": "09:00",
    "work_hours_end": "18:00",
    "work_days": 31  # пн-пт
}

provider = await orm_add_service_provider(session, service_data)
```

### **Поиск ответственного за заявку:**
```python
responsible_user_id = await orm_get_responsible_for_offer_category(
    session, jk_id=1, category=OfferCategory.SANTEHNIKA
)
```

### **Проверка рабочего времени:**
```python
provider = await orm_get_service_provider_by_id(session, provider_id)
if provider.is_working_now():
    # Отправить уведомление
    pass
```

## 🔄 **Интеграция с системой заявок**

Когда пользователь создаёт заявку:
1. Определяется категория заявки
2. Находится ответственный поставщик услуг для ЖК
3. Заявка автоматически назначается на него
4. Отправляется уведомление (если включено)

## 📈 **Будущие возможности**

- **SLA метрики** - время реакции и решения
- **Рейтинговая система** - оценки от жителей
- **Интеграция с CRM** - синхронизация с внешними системами
- **Геолокация** - учёт местоположения бригад
- **Календарь работ** - планирование и запись на техобслуживание

---

*Модель обеспечивает полную автоматизацию распределения заявок и управления обслуживающими организациями в ЖК.*
