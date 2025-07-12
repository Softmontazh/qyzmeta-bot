# 📊 Документация по моделям базы данных Qyzmeta-Bot

> **Проект**: Qyzmeta-Bot - Telegram бот для цифровизации ЖКХ Казахстана  
> **База данных**: PostgreSQL  
> **ORM**: SQLAlchemy 2.0  
> **Дата**: 12 июля 2025 г.

## 🏗️ Архитектура базы данных

База данных состоит из 6 основных таблиц и нескольких enum типов:

### Основные таблицы:
1. **users** - Пользователи системы
2. **jks** - Жилищные комплексы (ЖК) 
3. **user_jk** - Связка пользователей с ЖК
4. **offers** - Заявки/обращения жителей
5. **lots** - Объявления/лоты
6. **lot_limits** - Лимиты объявлений по ролям

---

## 👤 Модель: User (users)

**Назначение**: Хранение информации о пользователях Telegram бота

### Поля:

| Поле | Тип | Описание | Особенности |
|------|-----|----------|-------------|
| `id` | Integer | Внутренний ID записи | PK, автоинкремент |
| `user_id` | BigInteger | Telegram User ID | Unique, Index |
| `first_name` | String(50) | Имя пользователя | NOT NULL |
| `last_name` | String(50) | Фамилия | Nullable |
| `username` | String(50) | Telegram username | Nullable, Index |
| `user_language` | UserLanguage | Язык интерфейса | Enum: RU/KZ, default=RU |
| `is_bot` | Boolean | Является ли ботом | Default=False |
| `is_premium` | Boolean | Telegram Premium | Default=False, Index |
| `is_business` | Boolean | Telegram Business | Default=False, Index |
| `role` | UserRole | Роль в системе | Enum, default=GUEST, Index |
| `phone` | String(50) | Номер телефона | Nullable, Index |
| `email` | String(50) | Email адрес | Nullable, Index |
| `city` | String(100) | Город | Nullable, Index |
| `is_banned` | Boolean | Заблокирован | Default=False |
| `is_blocked` | Boolean | Заблокирован пользователем | Default=False |
| `is_blocked_by_admin` | Boolean | Заблокирован админом | Default=False |
| `is_subscribed_to_channel` | Boolean | Подписан на канал | Default=False, Index |
| `is_subscribed_to_group` | Boolean | Подписан на группу | Default=False, Index |
| `subscription_expires_at` | DateTime | Истечение подписки | Nullable |
| `last_active` | DateTime | Последняя активность | Nullable |
| `wants_notifications` | Boolean | Хочет уведомления | Default=True |
| `invited_by_id` | Integer | Кто пригласил (реферал) | FK to users.id, Nullable |
| `created_at` | DateTime | Дата создания | NOT NULL |
| `updated_at` | DateTime | Дата обновления | NOT NULL |

### Роли пользователей (UserRole):
- `CREATOR` - Создатель (лимит лотов: 1,000,000)
- `OWNER` - Владелец (лимит лотов: 1,000,000)
- `GUEST` - Гость (лимит лотов: 0)
- `USER` - Пользователь/Резидент (лимит лотов: 10)
- `ADMIN` - Администратор (лимит лотов: 100)
- `SUPERADMIN` - Суперадминистратор (лимит лотов: 100)
- `MODERATOR` - Модератор (лимит лотов: 100)
- `MANAGER` - Менеджер (лимит лотов: 1,000)
- `SUPPORT` - Поддержка (лимит лотов: 100)
- `PARTNER` - Партнер (лимит лотов: 10,000)

### Связи:
- `lots` - OneToMany с Lot (каскадное удаление)

### Методы:
- `get_lot_limit(session)` - Получить лимит лотов для роли пользователя

---

## 🏢 Модель: JK (jks)

**Назначение**: Хранение информации о жилищных комплексах

### Поля:

| Поле | Тип | Описание | Особенности |
|------|-----|----------|-------------|
| `id` | Integer | Внутренний ID | PK, автоинкремент |
| `uuid` | String(36) | UUID для API | Unique, Index, автогенерация |
| `name` | String(100) | Название ЖК | Nullable, Index |
| `city` | String(50) | Город | Nullable |
| `street` | String(100) | Улица | Nullable |
| `house` | String(20) | Номер дома | Nullable |
| `block` | String(20) | Номер блока/корпуса | Nullable |
| `channel_id` | BigInteger | ID Telegram канала ЖК | Nullable, Index |
| `group_id` | BigInteger | ID Telegram группы ЖК | Nullable, Index |
| `id_uk` | BigInteger | ID управляющей компании | Nullable, Index |
| `image_id` | String(100) | ID изображения в Telegram | Nullable |
| `bus_image_id` | String(100) | ID изображения для платформы | Nullable |
| `creator_id` | BigInteger | Кто создал ЖК | Nullable |
| `created_at` | DateTime | Дата создания | NOT NULL |
| `updated_at` | DateTime | Дата обновления | NOT NULL |

### Связи:
- `user_jks` - OneToMany с UserJK

### Свойства:
- `full_address` - Полный адрес (city, street, house, block)

---

## 🔗 Модель: UserJK (user_jk)

**Назначение**: Связь пользователей с жилищными комплексами (промежуточная таблица)

### Поля:

| Поле | Тип | Описание | Особенности |
|------|-----|----------|-------------|
| `id` | Integer | Внутренний ID | PK, автоинкремент |
| `user_id` | BigInteger | Telegram User ID | NOT NULL, Index |
| `jk_id` | Integer | ID жилищного комплекса | FK to jks.id, Index |
| `appartment` | String(20) | Номер квартиры | NOT NULL, default="" |
| `is_resident` | Boolean | Является резидентом | Default=True |
| `is_admin` | Boolean | Админ ЖК (ОСИ) | Default=False |
| `is_uk` | Boolean | Представитель УК | Default=False |
| `is_service` | Boolean | Служба ЖК | Default=False |
| `created_at` | DateTime | Дата создания | NOT NULL |
| `updated_at` | DateTime | Дата обновления | NOT NULL |

### Ограничения:
- Уникальная пара `(user_id, jk_id)` - один пользователь не может дважды привязаться к одному ЖК

### Связи:
- `jk` - ManyToOne с JK
- `offers` - OneToMany с Offer

---

## 📝 Модель: Offer (offers)

**Назначение**: Заявки и обращения жителей ЖК

### Поля:

| Поле | Тип | Описание | Особенности |
|------|-----|----------|-------------|
| `id` | Integer | Внутренний ID | PK, автоинкремент |
| `uuid` | String(36) | UUID для API | автогенерация |
| `category` | String(50) | Категория заявки | NOT NULL, Index |
| `title` | String(200) | Заголовок заявки | NOT NULL |
| `description` | Text | Описание заявки | Nullable |
| `media_id` | String(200) | ID медиа в Telegram | Nullable |
| `user_id` | BigInteger | ID автора заявки | NOT NULL |
| `user_jk_id` | Integer | ID связи с ЖК | FK to user_jk.id, NOT NULL |
| `status` | OfferStatus | Статус заявки | Enum, default=ACTIVE, Index |
| `created_at` | DateTime | Дата создания | NOT NULL |
| `updated_at` | DateTime | Дата обновления | NOT NULL |

### Статусы заявок (OfferStatus):
- `ACTIVE` - Активная 🔔
- `IN_PROGRESS` - В работе ⏳
- `COMPLETED` - Выполнена ✅
- `ARCHIVED` - Архивная 📦
- `CANCELLED` - Отменена ❌

### Связи:
- `user_jk` - ManyToOne с UserJK

---

## 💰 Модель: Lot (lots)

**Назначение**: Объявления и лоты пользователей

### Поля:

| Поле | Тип | Описание | Особенности |
|------|-----|----------|-------------|
| `id` | Integer | Внутренний ID | PK, автоинкремент, Index |
| `offer_type` | LotOfferType | Тип предложения | Enum, NOT NULL, Index |
| `type_lot` | String(50) | Тип лота | NOT NULL, Index |
| `name` | String(100) | Название | NOT NULL |
| `description` | Text | Описание | NOT NULL |
| `price` | Float | Цена | Index |
| `city` | String(100) | Город | Nullable, Index |
| `phone` | String(50) | Контактный телефон | Nullable, Index |
| `image_id` | String(150) | ID изображения | Nullable |
| `owner_id` | BigInteger | ID владельца | FK to users.user_id, Index |
| `status` | LotStatus | Статус лота | Enum, default=ACTIVE, Index |
| `visibility` | LotVisibility | Видимость лота | Enum, default=PUBLIC, Index |
| `expires_at` | DateTime(TZ) | Дата истечения | NOT NULL, default=+30 дней, Index |
| `created_at` | DateTime | Дата создания | NOT NULL |
| `updated_at` | DateTime | Дата обновления | NOT NULL |

### Типы предложений (LotOfferType):
- `BUY` - Купить
- `SELL` - Продать
- `EXCHANGE` - Обмен
- `GIVEAWAY` - Отдам даром
- `RENT` - Арендую
- `RENTOUT` - Сдам в аренду
- `REQUEST` - Запрос
- `SUGGEST` - Предложение

### Статусы лотов (LotStatus):
- `ACTIVE` - Активный
- `ARCHIVED` - Архивный
- `MODERATION` - На модерации
- `REJECTED` - Отклоненный
- `COMPLAINT` - С жалобой

### Видимость лотов (LotVisibility):
- `PUBLIC` - Публичный
- `PRIVATE` - Приватный
- `GROUP` - Групповой

### Связи:
- `owner` - ManyToOne с User

---

## 📊 Модель: LotLimit (lot_limits)

**Назначение**: Лимиты на количество лотов для разных ролей пользователей

### Поля:

| Поле | Тип | Описание | Особенности |
|------|-----|----------|-------------|
| `id` | Integer | Внутренний ID | PK, автоинкремент |
| `role` | UserRole | Роль пользователя | Enum, Unique, Index |
| `limit` | Integer | Лимит лотов | NOT NULL, default=0 |
| `created_at` | DateTime | Дата создания | NOT NULL |
| `updated_at` | DateTime | Дата обновления | NOT NULL |

### Рекомендуемые лимиты:
- CREATOR: 1,000,000
- OWNER: 1,000,000
- GUEST: 0
- USER: 10
- ADMIN: 100
- SUPERADMIN: 100
- MODERATOR: 100
- MANAGER: 1,000
- SUPPORT: 100
- PARTNER: 10,000

---

## 🔧 Технические особенности

### Индексы:
- Все ID поля проиндексированы для быстрого поиска
- Telegram user_id и channel_id проиндексированы
- Поля для фильтрации (статусы, роли, языки) проиндексированы
- Временные поля (expires_at, created_at) проиндексированы

### Связи:
```
User 1:N Lot (owner_id -> user_id)
User 1:N UserJK (через user_id)
JK 1:N UserJK (jk_id -> id)
UserJK 1:N Offer (user_jk_id -> id)
User 1:N User (реферальная система через invited_by_id)
```

### Enum типы:
- `UserLanguage`: RU, KZ
- `UserRole`: 10 ролей с иерархией доступа
- `OfferStatus`: 5 статусов жизненного цикла заявок
- `LotOfferType`: 8 типов объявлений
- `LotStatus`: 5 статусов лотов
- `LotVisibility`: 3 уровня видимости

### Каскадные операции:
- При удалении User удаляются все его Lot
- При удалении JK связи UserJK остаются (для истории)
- При удалении UserJK удаляются связанные Offer

---

## 🚀 Примеры использования

### Получить пользователя по Telegram ID:
```python
user = await session.get(User, {"user_id": telegram_user_id})
```

### Получить все ЖК пользователя:
```python
user_jks = await session.execute(
    select(UserJK).where(UserJK.user_id == telegram_user_id)
)
```

### Создать заявку:
```python
offer = Offer(
    category="водопровод",
    title="Нет горячей воды",
    description="Уже 3 дня нет горячей воды в квартире",
    user_id=telegram_user_id,
    user_jk_id=user_jk_relation_id
)
```

### Проверить лимит лотов:
```python
limit = await user.get_lot_limit(session)
current_lots = len(user.lots)
can_create = current_lots < limit
```

---

## 🏗️ Миграции и расширения

### При добавлении новых полей:
1. Добавить поле в модель
2. Создать миграцию Alembic
3. Обновить документацию
4. Обновить API endpoints

### При изменении enum:
1. Добавить новое значение в enum
2. Создать миграцию с ALTER TYPE
3. Обновить логику обработки

### Рекомендации по производительности:
- Использовать selectin loading для связанных объектов
- Добавлять составные индексы для частых запросов
- Кешировать часто запрашиваемые данные
- Использовать пагинацию для больших выборок

---

*Документация актуальна на 12 июля 2025 г.*
*Для вопросов по базе данных обращайтесь к разработчикам проекта Qyzmeta-Bot*
