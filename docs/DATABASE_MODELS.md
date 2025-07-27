# 📊 Модели базы данных Qyzmeta-Bot

> **Полная документация по структуре базы данных и ORM функциям**

## 🏗️ Архитектура базы данных

База данных построена на **PostgreSQL** с использованием **SQLAlchemy 2.0** асинхронного ORM. Система состоит из 7 основных таблиц, связанных через внешние ключи и оптимизированных для высокой производительности.

### Принципы проектирования
- **Нормализация** — исключение дублирования данных
- **Индексирование** — быстрый поиск по ключевым полям
- **UUID поддержка** — готовность к API и внешним интеграциям
- **Временные метки** — полная аудируемость изменений
- **Каскадные операции** — автоматическое поддержание целостности

---

## 👤 Модель: User (users)

**Назначение**: Хранение информации о пользователях системы

### Структура таблицы

| Поле | Тип | Описание | Особенности |
|------|-----|----------|-------------|
| `user_id` | BigInteger | Telegram User ID | PK, уникальный |
| `uuid` | String(36) | Уникальный UUID | Индекс, для API |
| `first_name` | String(100) | Имя пользователя | Nullable |
| `last_name` | String(100) | Фамилия | Nullable |
| `username` | String(100) | Telegram username | Nullable, индекс |
| `phone_number` | String(20) | Номер телефона | Nullable, индекс |
| `language` | UserLanguage | Язык интерфейса | Enum: RU, KZ |
| `role` | UserRole | Роль пользователя | Enum, 10 ролей |
| `created_at` | DateTime | Дата регистрации | NOT NULL |
| `updated_at` | DateTime | Последнее обновление | AUTO UPDATE |

### Роли пользователей (UserRole)

| Роль | Значение | Описание | Уровень доступа |
|------|----------|----------|-----------------|
| `USER` | 1 | Обычный житель | Базовый |
| `VIP_USER` | 2 | VIP житель | Расширенный |
| `MODERATOR` | 3 | Модератор | Модерация |
| `ADMIN_JK` | 4 | Админ ЖК (ОСИ) | Управление ЖК |
| `UK` | 5 | Управляющая компания | Управление |
| `SERVICE_PROVIDER` | 6 | Поставщик услуг | Исполнение |
| `ADMIN` | 7 | Администратор | Полный доступ |
| `SUPER_ADMIN` | 8 | Супер админ | Системный |
| `CREATOR` | 9 | Создатель | Максимальный |
| `SYSTEM` | 10 | Системная роль | Служебная |

### ORM функции

```python
# Создание пользователя
user = await orm_add_user(session, user_data)

# Получение по Telegram ID
user = await orm_get_user_by_id(session, user_id)

# Обновление роли
await orm_update_user_role(session, user_id, UserRole.SERVICE_PROVIDER)

# Поиск по номеру телефона
user = await orm_get_user_by_phone(session, "+77011234567")
```

---

## 🏢 Модель: JK (jks) 

**Назначение**: Хранение информации о жилищных комплексах

### Структура таблицы

| Поле | Тип | Описание | Особенности |
|------|-----|----------|-------------|
| `id` | Integer | Внутренний ID | PK, автоинкремент |
| `uuid` | String(36) | Уникальный UUID | Индекс, для API |
| `name` | String(100) | Название ЖК | Индекс |
| `city` | String(50) | Город | Nullable |
| `street` | String(100) | Улица | Nullable |
| `house` | String(20) | Номер дома | Nullable |
| `block` | String(20) | Блок/корпус | Nullable |
| `channel_id` | BigInteger | ID Telegram канала | Nullable, индекс |
| `group_id` | BigInteger | ID Telegram группы | Nullable, индекс |
| `id_uk` | BigInteger | ID управляющей компании | Nullable, индекс |
| `image_id` | String(100) | ID изображения Telegram | Nullable |
| `bus_image_id` | String(100) | BUS_ID изображения | Nullable |
| `creator_id` | BigInteger | Кто создал ЖК | Nullable |
| `created_at` | DateTime | Дата создания | NOT NULL |
| `updated_at` | DateTime | Дата обновления | AUTO UPDATE |

### Свойства модели

```python
@property
def full_address(self) -> str:
    """Полный адрес ЖК"""
    parts = [self.city, self.street, f"д. {self.house}"]
    if self.block:
        parts.append(f"корп. {self.block}")
    return ", ".join(filter(None, parts))
```

### ORM функции

```python
# Создание ЖК
jk = await orm_add_jk(session, jk_data)

# Получение всех ЖК
jks = await orm_get_all_jks(session)

# Получение по ID
jk = await orm_get_jk_by_id(session, jk_id)

# Обновление данных
await orm_update_jk(session, jk_id, update_data)

# Удаление
await orm_delete_jk(session, jk_id)
```

### BUS_ID система

Уникальная технология для обмена файлами между ботами платформы:

```python
# Генерация BUS_ID
bus_id = bus_service.generate_bus_id(file_id)
# Результат: "BUS_A1B2C3D4E5F6G7H8"

# Отправка в BUS канал
sent = await bot.send_photo(BUS_CHANNEL_ID, file_id, caption=f"BUS_ID: {bus_id}")
bus_file_id = sent.photo[-1].file_id

# Сохранение двух ID
jk.image_id = original_file_id      # Локальный file_id
jk.bus_image_id = bus_id           # Уникальный BUS_ID
```

---

## 🔗 Модель: UserJK (user_jk)

**Назначение**: Связь пользователей с жилищными комплексами (Many-to-Many)

### Структура таблицы

| Поле | Тип | Описание | Особенности |
|------|-----|----------|-------------|
| `id` | Integer | Внутренний ID | PK, автоинкремент |
| `user_id` | BigInteger | Telegram User ID | FK, индекс |
| `jk_id` | Integer | ID ЖК | FK to jks.id, индекс |
| `appartment` | String(20) | Номер квартиры | NOT NULL, default="" |
| `is_resident` | Boolean | Является резидентом | Default=True |
| `is_admin` | Boolean | Админ ЖК (ОСИ) | Default=False |
| `is_uk` | Boolean | Представитель УК | Default=False |
| `is_service` | Boolean | Служба ЖК | Default=False |
| `created_at` | DateTime | Дата создания | NOT NULL |
| `updated_at` | DateTime | Дата обновления | AUTO UPDATE |

### Ограничения
- **Уникальность** пары `(user_id, jk_id)` — исключает дублирование
- **Каскадное удаление** при удалении ЖК (опционально)

### ORM функции

```python
# Привязка пользователя к ЖК
user_jk = await orm_add_user_jk(session, user_id, jk_id, "123")

# Получение ЖК пользователя
jks = await orm_get_jks_by_user_id(session, user_id)

# Получение жителей ЖК
users = await orm_get_users_by_jk_id(session, jk_id)

# Назначение администратором
await orm_set_admin_status(session, user_id, jk_id, True)

# Удаление связи
await orm_delete_user_jk(session, user_id, jk_id)
```

---

## 📝 Модель: Offer (offers)

**Назначение**: Заявки и обращения жителей

### Структура таблицы

| Поле | Тип | Описание | Особенности |
|------|-----|----------|-------------|
| `id` | Integer | ID заявки | PK, автоинкремент |
| `uuid` | String(36) | Уникальный UUID | Индекс, для API |
| `title` | String(200) | Заголовок заявки | NOT NULL |
| `body` | Text | Описание проблемы | NOT NULL |
| `category` | OfferCategory | Категория заявки | Enum, индекс |
| `media_id` | String(100) | ID медиафайла | Nullable |
| `media_type` | String(20) | Тип медиа | photo/video |
| `user_jk_id` | Integer | ID связи с ЖК | FK to user_jk.id |
| `status` | OfferStatus | Статус заявки | Enum, default=ACTIVE |
| `created_at` | DateTime | Дата создания | NOT NULL |
| `updated_at` | DateTime | Дата обновления | AUTO UPDATE |

### Категории заявок (OfferCategory)

| Категория | Эмодзи | Описание |
|-----------|--------|----------|
| `DOMOFON` | 🔔 | Домофон и связь |
| `VIDEO` | 📹 | Видеонаблюдение |
| `ELEKTRIKA` | ⚡ | Электрика |
| `SANTEHNIKA` | 🚿 | Сантехника |
| `BLAGOUSTROYSTVO` | 🌳 | Благоустройство |
| `REPAIR` | 🔧 | Ремонт и обслуживание |
| `DRUGOE` | 📝 | Другие вопросы |

### Статусы заявок (OfferStatus)

| Статус | Описание | Следующие статусы |
|--------|----------|-------------------|
| `ACTIVE` | Новая заявка | IN_PROGRESS, CANCELLED |
| `IN_PROGRESS` | В работе | COMPLETED, CANCELLED |
| `COMPLETED` | Выполнена | - |
| `CANCELLED` | Отменена | ACTIVE |
| `ON_HOLD` | Приостановлена | IN_PROGRESS, CANCELLED |

### ORM функции

```python
# Создание заявки
offer = await orm_add_offer(session, offer_data)

# Получение заявок пользователя
offers = await orm_get_offers_by_user(session, user_id)

# Обновление статуса
await orm_update_offer_status(session, offer_id, OfferStatus.IN_PROGRESS)

# Поиск по категории
offers = await orm_get_offers_by_category(session, jk_id, OfferCategory.ELEKTRIKA)

# Получение активных заявок
active_offers = await orm_get_active_offers(session, jk_id)
```

---

## 🏗️ Модель: JKServiceProvider (jk_service_providers)

**Назначение**: Привязка ЖК к поставщикам услуг по категориям

### Структура таблицы

| Поле | Тип | Описание | Особенности |
|------|-----|----------|-------------|
| `id` | Integer | ID записи | PK, автоинкремент |
| `uuid` | String(36) | Уникальный UUID | Индекс, для API |
| `jk_id` | Integer | ID ЖК | FK to jks.id, индекс |
| `category` | OfferCategory | Категория услуг | Enum, индекс |
| `responsible_user_id` | BigInteger | Ответственное лицо | FK to users.user_id |
| `organization_name` | String(200) | Название организации | Nullable |
| `contact_phone` | String(50) | Контактный телефон | Nullable, индекс |
| `contact_email` | String(100) | Email | Nullable |
| `is_active` | Boolean | Активна ли привязка | Default=False, индекс |
| `receives_notifications` | Boolean | Получает уведомления | Default=True |
| `auto_assign_offers` | Boolean | Автоназначение заявок | Default=True |
| `priority` | Integer | Приоритет (1-высший) | Default=1 |
| `work_hours_start` | String(5) | Начало работы (HH:MM) | Nullable |
| `work_hours_end` | String(5) | Конец работы (HH:MM) | Nullable |
| `work_days` | Integer | Рабочие дни (битмаска) | Default=31 (пн-пт) |
| `description` | String(500) | Описание услуг | Nullable |
| `contract_number` | String(100) | Номер договора | Nullable |
| `contract_start_date` | DateTime | Начало договора | Nullable |
| `contract_end_date` | DateTime | Конец договора | Nullable |
| `created_at` | DateTime | Дата создания | NOT NULL |
| `updated_at` | DateTime | Дата обновления | AUTO UPDATE |
| `created_by_user_id` | BigInteger | Кто создал запись | Nullable |

### Система заявок и одобрения

Поставщики услуг проходят процесс заявки и одобрения:

1. **Подача заявки** — `is_active=False`, роль остается `USER`
2. **Рассмотрение администратором** — просмотр деталей заявки
3. **Одобрение** — `is_active=True`, роль меняется на `SERVICE_PROVIDER`
4. **Отклонение** — запись удаляется, роль остается `USER`

### Методы модели

```python
@property
def category_display_name(self) -> str:
    """Отображаемое название категории"""
    return self.category.display_name

@property
def category_emoji(self) -> str:
    """Эмодзи категории"""
    return self.category.emoji

@property
def is_contract_active(self) -> bool:
    """Активен ли договор на текущую дату"""
    if not self.contract_start_date or not self.contract_end_date:
        return True
    now = datetime.utcnow()
    return self.contract_start_date <= now <= self.contract_end_date

def is_working_now(self) -> bool:
    """Работает ли поставщик сейчас"""
    # Проверка рабочих дней и времени
    # Полная реализация в модели
```

### ORM функции

```python
# Создание заявки поставщика (БЕЗ изменения роли)
provider = await orm_add_service_provider(session, service_data)

# Получение поставщиков ЖК
providers = await orm_get_service_providers_by_jk(session, jk_id)

# Поиск по категории (с приоритетом)
provider = await orm_get_service_provider_by_category(session, jk_id, category)

# Активация заявки (с изменением роли)
success = await orm_activate_service_provider_request(session, provider_id, admin_id)

# Отклонение заявки
success = await orm_reject_service_provider_request(session, provider_id, admin_id)

# Получение заявок на рассмотрении
pending = await orm_get_pending_service_provider_requests(session)
```

### Рабочие дни (битовая маска)

```python
# Дни недели как степени двойки
MONDAY = 1     # 2^0
TUESDAY = 2    # 2^1
WEDNESDAY = 4  # 2^2
THURSDAY = 8   # 2^3
FRIDAY = 16    # 2^4
SATURDAY = 32  # 2^5
SUNDAY = 64    # 2^6

# Пн-Пт = 1+2+4+8+16 = 31
# Пн-Сб = 1+2+4+8+16+32 = 63
# Каждый день = 1+2+4+8+16+32+64 = 127
```

---

## 📢 Модель: Lot (lots)

**Назначение**: Система объявлений и лотов

### Структура таблицы

| Поле | Тип | Описание | Особенности |
|------|-----|----------|-------------|
| `id` | Integer | ID лота | PK, автоинкремент |
| `uuid` | String(36) | Уникальный UUID | Индекс, для API |
| `user_id` | BigInteger | Автор лота | FK to users.user_id |
| `title` | String(200) | Заголовок | NOT NULL |
| `description` | Text | Описание | NOT NULL |
| `offer_type` | LotOfferType | Тип предложения | Enum |
| `price` | Decimal(10,2) | Цена | Nullable |
| `currency` | String(3) | Валюта | Default='KZT' |
| `media_id` | String(100) | ID медиафайла | Nullable |
| `contact_info` | String(200) | Контакты | Nullable |
| `location` | String(200) | Локация | Nullable |
| `status` | LotStatus | Статус лота | Enum, default=ACTIVE |
| `visibility` | LotVisibility | Видимость | Enum, default=PUBLIC |
| `expires_at` | DateTime | Дата истечения | Nullable |
| `created_at` | DateTime | Дата создания | NOT NULL |
| `updated_at` | DateTime | Дата обновления | AUTO UPDATE |

### Типы предложений (LotOfferType)

| Тип | Описание | Пример |
|-----|----------|--------|
| `SELL` | Продажа | Продам мебель |
| `BUY` | Покупка | Куплю холодильник |
| `RENT` | Аренда | Сдам парковочное место |
| `SERVICE` | Услуги | Ремонт техники |
| `EXCHANGE` | Обмен | Поменяю книги |
| `GIFT` | Дарю | Отдам даром |
| `FIND` | Поиск | Ищу репетитора |
| `OTHER` | Другое | Прочие объявления |

---

## 🎛️ Модель: LotLimit (lot_limits)

**Назначение**: Лимиты создания лотов для разных ролей

### Структура таблицы

| Поле | Тип | Описание | Особенности |
|------|-----|----------|-------------|
| `id` | Integer | ID записи | PK, автоинкремент |
| `role` | UserRole | Роль пользователя | Enum, уникальный |
| `daily_limit` | Integer | Лимит в день | Default=5 |
| `monthly_limit` | Integer | Лимит в месяц | Default=50 |
| `max_media_size_mb` | Integer | Размер медиа (МБ) | Default=10 |
| `can_pin` | Boolean | Может закреплять | Default=False |
| `can_highlight` | Boolean | Может выделять | Default=False |

### Примеры лимитов

```python
# USER: 3 лота в день, 20 в месяц
# VIP_USER: 10 лотов в день, 100 в месяц, может выделять
# ADMIN: Безлимитно, может закреплять
```

---

## 🔧 Технические особенности

### Индексы базы данных

```sql
-- Пользователи
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_users_role ON users(role);

-- ЖК
CREATE INDEX idx_jk_name ON jks(name);
CREATE INDEX idx_jk_city ON jks(city);

-- Связи пользователь-ЖК
CREATE INDEX idx_user_jk_user_id ON user_jk(user_id);
CREATE INDEX idx_user_jk_jk_id ON user_jk(jk_id);

-- Заявки
CREATE INDEX idx_offers_category ON offers(category);
CREATE INDEX idx_offers_status ON offers(status);
CREATE INDEX idx_offers_created_at ON offers(created_at);

-- Поставщики услуг
CREATE INDEX idx_jk_providers_jk_category ON jk_service_providers(jk_id, category);
CREATE INDEX idx_jk_providers_active ON jk_service_providers(is_active);
CREATE INDEX idx_jk_providers_responsible ON jk_service_providers(responsible_user_id);
```

### Enum типы

```python
# Языки
class UserLanguage(str, Enum):
    RU = "RU"  # Русский
    KZ = "KZ"  # Казахский

# Роли (иерархические)
class UserRole(IntEnum):
    USER = 1                # Обычный пользователь
    VIP_USER = 2           # VIP пользователь
    MODERATOR = 3          # Модератор
    ADMIN_JK = 4           # Администратор ЖК
    UK = 5                 # Управляющая компания
    SERVICE_PROVIDER = 6   # Поставщик услуг
    ADMIN = 7              # Администратор
    SUPER_ADMIN = 8        # Супер администратор
    CREATOR = 9            # Создатель
    SYSTEM = 10            # Системная роль

# Статусы заявок
class OfferStatus(str, Enum):
    ACTIVE = "active"         # Активная
    IN_PROGRESS = "progress"  # В работе
    COMPLETED = "completed"   # Выполнена
    CANCELLED = "cancelled"   # Отменена
    ON_HOLD = "on_hold"      # Приостановлена

# Категории услуг
class OfferCategory(str, Enum):
    DOMOFON = "domofon"              # Домофон 🔔
    VIDEO = "video"                  # Видеонаблюдение 📹
    ELEKTRIKA = "elektrika"          # Электрика ⚡
    SANTEHNIKA = "santehnika"        # Сантехника 🚿
    BLAGOUSTROYSTVO = "blagoustroystvo"  # Благоустройство 🌳
    REPAIR = "repair"                # Ремонт 🔧
    DRUGOE = "drugoe"               # Другое 📝
```

### Каскадные операции

```python
# При удалении User
user.lots.delete()  # Удаляются все лоты пользователя

# При удалении JK
jk.user_jks.delete()  # Связи остаются для истории
jk.service_providers.delete()  # Поставщики удаляются

# При удалении UserJK
user_jk.offers.delete()  # Связанные заявки удаляются
```

### Полнотекстовый поиск

```sql
-- Поиск по заявкам
SELECT * FROM offers 
WHERE to_tsvector('russian', title || ' ' || body) 
      @@ plainto_tsquery('russian', 'протечка водопровод');

-- Поиск по ЖК
SELECT * FROM jks 
WHERE to_tsvector('russian', name || ' ' || COALESCE(city, '') || ' ' || COALESCE(street, ''))
      @@ plainto_tsquery('russian', 'жастар алматы');
```

---

## 🚀 Производительность и оптимизация

### Асинхронные операции

Все ORM функции используют `async/await` для высокой производительности:

```python
# Множественные запросы выполняются параллельно
async def get_dashboard_data(session, user_id):
    user, jks, offers = await asyncio.gather(
        orm_get_user_by_id(session, user_id),
        orm_get_jks_by_user_id(session, user_id),
        orm_get_active_offers_by_user(session, user_id)
    )
    return user, jks, offers
```

### Eager Loading

```python
# Загрузка связанных данных одним запросом
providers = await session.execute(
    select(JKServiceProvider)
    .options(selectinload(JKServiceProvider.jk))
    .where(JKServiceProvider.is_active == True)
)
```

### Пагинация

```python
# Пагинация для больших списков
async def orm_get_offers_paginated(session, jk_id, page=1, per_page=20):
    offset = (page - 1) * per_page
    
    stmt = (select(Offer)
            .join(UserJK)
            .where(UserJK.jk_id == jk_id)
            .order_by(Offer.created_at.desc())
            .offset(offset)
            .limit(per_page))
    
    result = await session.execute(stmt)
    return result.scalars().all()
```

### Кэширование

```python
# Redis кэширование для часто запрашиваемых данных
@cached(ttl=300)  # 5 минут
async def get_jk_statistics(jk_id: int):
    # Тяжелые вычисления статистики
    pass
```

---

## 📝 Примеры использования

### Создание заявки с автоназначением

```python
async def create_offer_with_auto_assign(session, offer_data):
    # 1. Создаем заявку
    offer = await orm_add_offer(session, offer_data)
    
    # 2. Находим ответственного поставщика
    responsible_id = await orm_get_responsible_for_offer_category(
        session, offer.user_jk.jk_id, offer.category
    )
    
    # 3. Отправляем уведомление
    if responsible_id:
        await send_notification(responsible_id, offer)
    
    return offer
```

### Система одобрения поставщиков

```python
async def approve_service_provider(session, provider_id, admin_id):
    # 1. Активируем поставщика
    success = await orm_activate_service_provider_request(
        session, provider_id, admin_id
    )
    
    if success:
        # 2. Получаем данные поставщика
        provider = await orm_get_service_provider_by_id(session, provider_id)
        
        # 3. Уведомляем пользователя
        await send_approval_notification(provider.responsible_user_id, provider)
        
        # 4. Логируем действие
        await log_admin_action(admin_id, f"Approved provider #{provider_id}")
    
    return success
```

### Статистика по ЖК

```python
async def get_jk_dashboard_stats(session, jk_id):
    # Параллельные запросы для статистики
    total_residents, active_offers, providers_count, completion_rate = await asyncio.gather(
        orm_count_jk_residents(session, jk_id),
        orm_count_active_offers(session, jk_id),
        orm_count_service_providers(session, jk_id),
        orm_get_offers_completion_rate(session, jk_id)
    )
    
    return {
        "residents": total_residents,
        "active_offers": active_offers,
        "service_providers": providers_count,
        "completion_rate": completion_rate
    }
```

---

## 🤝 Модель: PartnerApplication (partner_applications)

**Назначение**: Хранение заявок на партнерство с системой модерации

### Структура таблицы

| Поле | Тип | Описание | Особенности |
|------|-----|----------|-------------|
| `id` | Integer | Внутренний ID | PK, автоинкремент |
| `user_id` | BigInteger | Telegram User ID | FK к users, индекс |
| `requested_role` | UserRole | Запрашиваемая роль | Enum, по умолчанию PARTNER |
| `full_name` | String(150) | ФИО заявителя | NOT NULL |
| `company` | String(200) | Название компании | NOT NULL |
| `purpose` | Text | Цель получения роли | NOT NULL |
| `phone` | String(20) | Контактный телефон | NOT NULL |
| `status` | ApplicationStatus | Статус заявки | Enum, по умолчанию PENDING |
| `created_at` | DateTime | Дата подачи | NOT NULL |
| `updated_at` | DateTime | Дата обновления | AUTO UPDATE |

### Статусы заявок (ApplicationStatus)

| Статус | Значение | Описание | Действие |
|--------|----------|----------|----------|
| `PENDING` | 1 | ⏳ Ожидает рассмотрения | Заявка подана |
| `APPROVED` | 2 | ✅ Одобрена | Роль назначена |
| `REJECTED` | 3 | ❌ Отклонена | Заявка отклонена |
| `EDIT_REQUEST` | 4 | ✏️ Запрос на редактирование | Партнер запросил изменения |
| `DELETE_REQUEST` | 5 | 🗑️ Запрос на удаление | Партнер запросил удаление |

### Связи

- **user_id** → `users.user_id` (Many-to-One)
- Одобренная заявка дает доступ к партнерской панели
- При одобрении может обновляться роль в таблице `users`

### ORM функции

```python
# Создание заявки
application = await orm_create_partner_application(
    session, user_id, UserRole.PARTNER, 
    "Иванов Иван Иванович", "ООО Ромашка", 
    "Управление ЖК", "+77011234567"
)

# Получение заявки пользователя
application = await orm_get_partner_application_by_user_id(session, user_id)

# Получение всех заявок с фильтром
applications = await orm_get_partner_applications(session, status=ApplicationStatus.PENDING)

# Обновление статуса
await orm_update_partner_application_status(session, application_id, ApplicationStatus.APPROVED)

# Поиск одобренных партнеров
partners = await orm_get_approved_partners(session)
```

### Индексы

- `user_id` — быстрый поиск заявок пользователя
- `status` — фильтрация по статусу
- `created_at` — сортировка по дате
- Составной индекс `(user_id, status)` — оптимизация частых запросов

### Особенности реализации

- **Валидация** — проверка данных на уровне модели
- **Аудит** — автоматические временные метки
- **Уникальность** — один пользователь может иметь несколько заявок
- **Каскады** — при удалении пользователя удаляются заявки
- **Локализация** — русские названия статусов через метод `get_russian_name()`

---

## 🔮 Будущие возможности

### Расширения схемы

1. **Уведомления** — таблица для истории уведомлений
2. **Файлы** — централизованное хранение медиафайлов
3. **Платежи** — интеграция платежных систем
4. **Рейтинги** — оценки поставщиков услуг
5. **Чаты** — система внутренних сообщений

### API интеграции

1. **REST API** — полный CRUD доступ
2. **GraphQL** — гибкие запросы данных
3. **WebHooks** — уведомления внешних систем
4. **SSE/WebSocket** — реальное время

### Аналитика

1. **Временные ряды** — анализ трендов
2. **Машинное обучение** — предиктивная аналитика
3. **Business Intelligence** — дашборды
4. **Экспорт данных** — отчеты в Excel/PDF

---

## 💰 Модель: UserSubscription (user_subscriptions)

**Назначение**: Система управления подписками и тарифными планами пользователей

### Структура таблицы

| Поле | Тип | Описание | Особенности |
|------|-----|----------|-------------|
| `id` | Integer | ID подписки | PK, автоинкремент |
| `user_id` | BigInteger | Telegram User ID | FK to users.user_id, индекс |
| `tier` | SubscriptionTier | Тарифный план | Enum: FREE, BASIC, PREMIUM, VIP |
| `status` | SubscriptionStatus | Статус подписки | Enum: ACTIVE, EXPIRED, CANCELLED |
| `max_addresses` | Integer | Лимит адресов | NOT NULL |
| `started_at` | DateTime | Дата начала | NOT NULL |
| `expires_at` | DateTime | Дата окончания | Nullable для бессрочных |
| `payment_info` | Text | Информация об оплате | Nullable |
| `notes` | Text | Заметки администратора | Nullable |
| `created_at` | DateTime | Дата создания | NOT NULL |
| `updated_at` | DateTime | Дата обновления | AUTO UPDATE |

### Тарифные планы (SubscriptionTier)

| Тариф | Лимит адресов | Особенности |
|-------|---------------|-------------|
| `FREE` | 1 | Базовая функциональность |
| `BASIC` | 3 | Приоритетные уведомления, поддержка |
| `PREMIUM` | 10 | Эксклюзивные предложения, персональный менеджер |
| `VIP` | 999 | VIP статус, персональный консультант |

### Статусы подписок (SubscriptionStatus)

| Статус | Описание |
|--------|----------|
| `ACTIVE` | Активная подписка |
| `EXPIRED` | Истекшая подписка |
| `CANCELLED` | Отмененная подписка |

### Методы модели

```python
@property
def is_expiring_soon(self) -> bool:
    """Истекает ли подписка в ближайшие 7 дней"""
    if not self.expires_at:
        return False
    return (self.expires_at - datetime.now(timezone.utc)).days <= 7

@property
def days_left(self) -> int:
    """Количество дней до истечения"""
    if not self.expires_at:
        return -1
    delta = self.expires_at - datetime.now(timezone.utc)
    return max(0, delta.days)

def get_tier_display(self) -> str:
    """Отображаемое название тарифа"""
    return self.tier.get_russian_name()

def get_status_display(self) -> str:
    """Отображаемое название статуса"""
    return self.status.get_russian_name()
```

### ORM функции

```python
# Получение подписки пользователя
subscription = await orm_get_user_subscription(session, user_id)

# Создание подписки
subscription = await orm_create_user_subscription(session, subscription_data)

# Проверка лимита адресов
current_count, max_allowed = await orm_check_address_limit(session, user_id)

# Обновление тарифа
await orm_update_subscription_tier(session, user_id, new_tier, duration_days=30)

# Получение статистики
stats = await orm_get_subscription_statistics(session)

# Истечение просроченных подписок
expired_count = await orm_expire_overdue_subscriptions(session)
```

### Индексы

```sql
CREATE INDEX idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX idx_user_subscriptions_status ON user_subscriptions(status);
CREATE INDEX idx_user_subscriptions_tier ON user_subscriptions(tier);
CREATE INDEX idx_user_subscriptions_expires_at ON user_subscriptions(expires_at);
CREATE INDEX idx_user_subscriptions_user_status_active ON user_subscriptions(user_id, status) WHERE status = 'ACTIVE';
```

---

## 💎 Модель: SubscriptionPrice (subscription_prices)

**Назначение**: Система динамического ценообразования с полной историей изменений

### Структура таблицы

| Поле | Тип | Описание | Особенности |
|------|-----|----------|-------------|
| `id` | Integer | ID записи | PK, автоинкремент |
| `tier` | String(20) | Тарифный план | FREE, BASIC, PREMIUM, VIP |
| `price` | Integer | Цена в тенге | NOT NULL |
| `is_active` | Boolean | Активная цена | Default=True, индекс |
| `created_at` | DateTime | Дата создания | NOT NULL |
| `updated_at` | DateTime | Дата обновления | AUTO UPDATE |
| `created_by` | Integer | ID администратора | Nullable |
| `notes` | Text | Комментарий к изменению | Nullable |

### Особенности

- **История изменений** — каждое изменение цены создает новую запись
- **Активная цена** — только одна запись на тариф может быть активной
- **Валидация** — цены от 0 до 100,000 ₸
- **Аудит** — полная трассировка кто и когда изменил цену

### Методы модели

```python
@property
def formatted_price(self) -> str:
    """Форматированная цена для отображения"""
    return f"{self.price:,} ₸" if self.price > 0 else "Бесплатно"

@property
def tier_display_name(self) -> str:
    """Отображаемое название тарифа"""
    tier_names = {
        "FREE": "🆓 Бесплатный",
        "BASIC": "⭐ Базовый", 
        "PREMIUM": "💎 Премиум",
        "VIP": "👑 VIP"
    }
    return tier_names.get(self.tier, self.tier)
```

### ORM функции

```python
# Получение текущих цен
prices = await orm_get_active_prices(session)

# Получение цены тарифа
price_obj = await orm_get_price_by_tier(session, tier)

# Обновление цены (создание новой записи)
await orm_update_price(session, tier, new_price, admin_id, notes)

# Инициализация цен по умолчанию
await orm_initialize_default_prices(session, admin_id)

# Получение истории изменений
history = await orm_get_price_history(session, limit=10)
```

### Индексы

```sql
CREATE INDEX ix_subscription_prices_id ON subscription_prices(id);
CREATE INDEX ix_subscription_prices_tier ON subscription_prices(tier);
CREATE INDEX ix_subscription_prices_is_active ON subscription_prices(is_active);
CREATE INDEX ix_subscription_prices_created_at ON subscription_prices(created_at);
```

### Система валидации

```python
def validate_price_input(price_text: str) -> Tuple[bool, int, str]:
    """Валидация ввода цены"""
    try:
        price = int(price_text.strip())
        
        if price < 0:
            return False, 0, "Цена не может быть отрицательной"
        
        if price > 100000:
            return False, 0, "Цена не может превышать 100,000 ₸"
        
        return True, price, ""
        
    except ValueError:
        return False, 0, "Введите корректное число"
```

---

## 🚀 Сервисы подписок

### PriceManagementService

Основной сервис для управления ценами:

```python
class PriceManagementService:
    @staticmethod
    async def get_current_prices(session: AsyncSession) -> Dict
    
    @staticmethod
    async def update_tier_price(session: AsyncSession, tier: SubscriptionTier, 
                               new_price: int, updated_by: int, notes: str = None) -> Dict
    
    @staticmethod
    async def get_price_history(session: AsyncSession, limit: int = 50) -> List[Dict]
    
    @staticmethod
    async def get_management_summary(session: AsyncSession) -> Dict
    
    @staticmethod
    def validate_price_input(price_text: str) -> Tuple[bool, int, str]
    
    @staticmethod
    def format_price_change_message(tier, old_price, new_price, updated_by) -> str
```

### SubscriptionService

Сервис для работы с подписками:

```python
class SubscriptionService:
    @staticmethod
    async def get_user_subscription_info(session: AsyncSession, user_id: int) -> Dict
    
    @staticmethod
    async def check_can_register_address(session: AsyncSession, user_id: int) -> Tuple[bool, Dict]
    
    @staticmethod
    async def upgrade_user_subscription(session: AsyncSession, user_id: int, 
                                       new_tier: SubscriptionTier, duration_days: int = 30) -> Dict
    
    @staticmethod
    async def get_subscription_analytics(session: AsyncSession) -> Dict
    
    @staticmethod
    async def get_admin_statistics(session: AsyncSession) -> Dict
```

---

## 📊 Аналитика подписок

### Ключевые метрики

1. **Общее количество пользователей** — подсчет всех записей в таблице users
2. **Активные подписки** — количество платных подписок (исключая FREE)
3. **Конверсия** — процент пользователей с платными подписками
4. **ARPU** — средний доход на пользователя
5. **Месячная выручка** — общий доход от всех подписок

### Формат данных аналитики

```python
{
    'total_users': 150,           # Общее количество пользователей
    'active_subscriptions': 45,   # Активные платные подписки
    'by_tier': [                  # Разбивка по тарифам
        {
            'tier': 'FREE',
            'tier_display': '🆓 Бесплатный',
            'count': 105,
            'percentage': 70.0,
            'revenue': 0
        },
        {
            'tier': 'BASIC',
            'tier_display': '⭐ Базовый',
            'count': 30,
            'percentage': 20.0,
            'revenue': 89700
        }
    ],
    'revenue': 447500,            # Общая месячная выручка
    'free_users': 105,            # Бесплатные пользователи
    'conversion_rate': 30.0       # Коэффициент конверсии в %
}
```

---

## 🔧 Миграции и обновления

### Создание таблиц подписок

```sql
-- Создание enum типов
CREATE TYPE subscription_tier AS ENUM ('FREE', 'BASIC', 'PREMIUM', 'VIP');
CREATE TYPE subscription_status AS ENUM ('ACTIVE', 'EXPIRED', 'CANCELLED');

-- Таблица подписок
CREATE TABLE user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    tier subscription_tier NOT NULL DEFAULT 'FREE',
    status subscription_status NOT NULL DEFAULT 'ACTIVE',
    max_addresses INTEGER NOT NULL DEFAULT 1,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    expires_at TIMESTAMP WITH TIME ZONE,
    payment_info TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Таблица цен
CREATE TABLE subscription_prices (
    id SERIAL PRIMARY KEY,
    tier VARCHAR(20) NOT NULL,
    price INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_by INTEGER,
    notes TEXT
);
```

### Инициализация данных

```python
# Создание цен по умолчанию
default_prices = [
    {"tier": "FREE", "price": 0},
    {"tier": "BASIC", "price": 2990},
    {"tier": "PREMIUM", "price": 4990},
    {"tier": "VIP", "price": 9990}
]

for price_data in default_prices:
    await orm_update_price(
        session, 
        price_data["tier"], 
        price_data["price"], 
        admin_id=0, 
        notes="Инициализация системы ценообразования"
    )
```

---

*Документация обновлена: 27 июля 2025 г.*  
*Версия схемы БД: 2.3.0 — Добавлена система подписок и динамического ценообразования*  
*Добавлена таблица partner_applications с системой управления партнерами*
