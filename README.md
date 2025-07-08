
# 🏢 Qyzmeta-Bot — Цифровая экосистема для ЖКХ Казахстана

<div align="center">

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Aiogram](https://img.shields.io/badge/aiogram-3.20.0-green.svg)
![SQLAlchemy](https://img.shields.io/badge/sqlalchemy-2.0.41-orange.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-latest-blue.svg)
![License](https://img.shields.io/badge/license-Proprietary-red.svg)

**Современное решение для цифровизации жилищно-коммунального хозяйства**

[Особенности](#-особенности) • [Установка](#-установка) • [Использование](#-использование) • [API](#-архитектура) • [Контакты](#-контакты)

</div>

---

## 📋 О проекте

**Qyzmeta-Bot** — это передовая Telegram-платформа, разработанная специально для цифровизации сферы ЖКХ в Казахстане. Проект создан на базе платформы **LotBox** и представляет собой облегченную, но мощную версию для эффективного взаимодействия жителей с управляющими компаниями и сервисными организациями.

### 🎯 Цель проекта
Упростить и автоматизировать процессы управления жилищным фондом, обеспечить прозрачное взаимодействие между всеми участниками процесса и создать единую цифровую экосистему для ЖКХ.

### 🏗️ Архитектурная концепция
Проект строится на принципах масштабируемости с возможностью интеграции:
- 🌐 **REST API** для внешних систем
- 📱 **Web приложения** для расширенного функционала  
- 🔗 **Web3.0** технологий для создания цифровых следов
- 🆔 **UUID-индентификация** для каждой значимой сущности

---

## ✨ Особенности

### 🏠 Управление недвижимостью
- **Регистрация ЖК** — добавление новых жилых комплексов
- **Привязка жителей** — регистрация пользователей к конкретным квартирам
- **Ролевая модель** — разграничение прав доступа

### 📋 Система заявок
- **Категоризация** — домофон, электрика, сантехника, благоустройство
- **Мультимедиа** — прикрепление фото и видео к заявкам
- **Отслеживание статуса** — контроль выполнения заявок
- **История обращений** — полная база данных взаимодействий

### 👥 Ролевая система
- 🏠 **Житель** — подача заявок, просмотр информации
- 🏢 **УК (Управляющая компания)** — обработка заявок, управление
- 🔧 **Сервисная компания** — выполнение технических работ  
- 👨‍💼 **ОСИ/КСК** — административное управление ЖК
- 👤 **CREATOR** — системные администраторы

### 🔧 Техническая экосистема
- **FSM-состояния** для пошаговых сценариев
- **Асинхронная обработка** для высокой производительности
- **Модульная архитектура** для легкого расширения
- **PostgreSQL** для надежного хранения данных

---

## 🚀 Технологический стек

<table>
<tr>
<td valign="top" width="33%">

### Backend
- 🐍 **Python 3.11+**
- ⚡ **Aiogram 3.20.0** — Async Telegram Bot API
- �️ **SQLAlchemy 2.0.41** — Modern ORM
- 🐘 **PostgreSQL** — Production Database
- � **AsyncPG** — Async PostgreSQL driver

</td>
<td valign="top" width="33%">

### Архитектура
- 🏗️ **FSM (Finite State Machine)**
- � **Middleware & Filters**
- 📦 **Модульная структура**
- 🎯 **Clean Architecture**
- 🔐 **Role-based Access Control**

</td>
<td valign="top" width="34%">

### DevOps
- 🐳 **Docker ready**
- ☁️ **VPS deployment**
- 🔗 **Webhook support**
- � **Logging & Monitoring**
- 🔧 **Environment management**

</td>
</tr>
</table>

---

## 📂 Структура проекта

```
qyzmeta-bot/
├── 📄 app.py                    # Главный файл приложения
├── 📁 common/                   # Общие компоненты
│   ├── bot_cmds_list.py        # Команды бота
│   └── callbacks.py            # Callback-функции
├── 📁 database/                 # База данных
│   ├── engine.py               # Конфигурация БД
│   ├── 📁 models/              # Модели данных
│   │   ├── model_base.py       # Базовая модель
│   │   ├── model_user.py       # Пользователи LotBox
│   │   ├── model_jk.py         # Жилые комплексы
│   │   ├── model_user_jk.py    # Привязка пользователей к ЖК
│   │   ├── model_offer.py      # Заявки от жителей
│   │   └── orm_*.py            # ORM-операции
│   └── 📁 enums/               # Перечисления
├── 📁 handlers/                 # Обработчики событий
│   ├── user_private.py         # Личные сообщения
│   ├── user_group.py           # Групповые чаты
│   ├── admin_private.py        # Админ-панель
│   └── 📁 fsm/                 # Конечные автоматы
│       ├── add_jk_fsm.py       # Добавление ЖК
│       ├── add_offer_fsm.py    # Создание заявок
│       └── user_to_jk_fsm.py   # Регистрация в ЖК
├── 📁 keyboards/                # Клавиатуры
├── 📁 middlewares/              # Промежуточные обработчики
├── 📁 services/                 # Бизнес-логика
├── 📁 static/                   # Статические данные
└── 📁 utils/                    # Утилиты
```

---

## 🛠️ Установка

### Предварительные требования
- Python 3.11+
- PostgreSQL 12+
- Git

### 1️⃣ Клонирование репозитория
```bash
git clone https://github.com/Softmontazh/qyzmeta-bot.git
cd qyzmeta-bot
```

### 2️⃣ Создание виртуального окружения
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

### 3️⃣ Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4️⃣ Настройка окружения
Создайте файл `.env` в корне проекта:
```env
# Telegram Bot
TOKEN=your_telegram_bot_token

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=qyzmeta_db
DB_USER=your_db_user
DB_PASS=your_db_password
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db

# Permissions
CREATOR_ID=your_telegram_id,another_id

# Media Storage
BUS_ID=your_media_channel_id
```

### 5️⃣ Инициализация базы данных
```bash
python app.py
```

---

## 🎮 Использование

### Запуск бота
```bash
python app.py
```

### Основные команды для пользователей
- `/start` — Начало работы и регистрация
- `/add_my_jk` — Привязка к жилому комплексу
- `/create_offer` — Создание новой заявки
- `/my_profile` — Просмотр профиля
- `/help` — Справочная информация

### Команды для администраторов
- `/add_jk` — Добавление нового ЖК (только CREATOR)
- `/admin` — Панель администратора

---

## 🏛️ Архитектура

### Модель данных

```mermaid
erDiagram
    User ||--o{ UserJK : "привязка"
    JK ||--o{ UserJK : "принадлежность"
    UserJK ||--o{ Offer : "заявки"
    
    User {
        int id PK
        bigint user_id UK
        string first_name
        string last_name
        string username
        enum role
        string phone
        string email
        datetime created_at
    }
    
    JK {
        int id PK
        string uuid UK
        string name
        string city
        string street
        string house
        string block
        bigint creator_id
        datetime created_at
    }
    
    UserJK {
        int id PK
        bigint user_id FK
        int jk_id FK
        string appartment
        bool is_resident
        bool is_admin
        bool is_uk
        bool is_service
    }
    
    Offer {
        int id PK
        string uuid UK
        string category
        string title
        text description
        string media_id
        bigint user_id
        int user_jk_id FK
        datetime created_at
    }
```

### Роли пользователей
- **GUEST** — Гость (ограниченный доступ)
- **USER** — Зарегистрированный пользователь
- **ADMIN** — Администратор ЖК
- **SUPERADMIN** — Супер-администратор
- **CREATOR** — Создатель системы
- **OWNER** — Владелец
- **MANAGER** — Менеджер
- **PARTNER** — Партнер

---

## 📊 Roadmap

### 🚧 MVP (v0.1.0-dev) — В разработке
- [x] ✅ Регистрация и управление ЖК
- [x] ✅ Привязка пользователей к квартирам
- [x] ✅ Система заявок по категориям
- [x] ⏳ Ролевая модель доступа
- [ ] 🔲 Интеграция с группами/каналами
- [ ] 🔲 Уведомления и статусы заявок

### 🎯 v1.0.0 — Production Ready
- [ ] 🔲 REST API для внешних интеграций
- [ ] 🔲 Web-интерфейс администратора
- [ ] 🔲 Мобильное приложение
- [ ] 🔲 Интеграция с платежными системами
- [ ] 🔲 Аналитика и отчетность

### 🚀 v2.0.0 — Advanced Features
- [ ] 🔲 AI-ассистент для обработки заявок
- [ ] 🔲 IoT интеграция (умный дом)
- [ ] 🔲 Web3.0 и блокчейн интеграция
- [ ] 🔲 Многоязычная поддержка

---

## 🤝 Команда разработки

Проект находится в активной разработке командой **ТОО "СОФТМОНТАЖ"**. 

### Внутренние процессы:
- 🐛 Багтрекинг через внутренние системы
- 💡 Предложения по улучшению от команды
- 📖 Внутренняя документация и стандарты
- 🧪 Непрерывное тестирование и QA

### Для внешних партнеров:
Заинтересованы в сотрудничестве? Свяжитесь с нами:
- 📧 **Коммерческие вопросы**: info@softmontazh.kz
- 💬 **Техническое партнерство**: [@bySpecialist](https://t.me/bySpecialist)

---

## 📄 Лицензия

**Проприетарная лицензия** — Все права защищены

```
Copyright (c) 2025, ТОО "СОФТМОНТАЖ" (LLP Softmontazh)

Данное программное обеспечение является конфиденциальной 
и частной собственностью автора. Запрещается использование,
копирование, модификация или распространение без письменного
разрешения правообладателя.
```

Для получения лицензии обращайтесь: **info@softmontazh.kz**

---

## 👨‍� Автор и команда

<div align="center">

### **Александр Хван**
*Ведущий разработчик и архитектор*

[![Telegram](https://img.shields.io/badge/Telegram-@bySpecialist-blue.svg)](https://t.me/bySpecialist)
[![Email](https://img.shields.io/badge/Email-info@softmontazh.kz-red.svg)](mailto:info@softmontazh.kz)

**ТОО "СОФТМОНТАЖ"** | **LLP Softmontazh**

*Инновационные решения для цифровизации бизнеса*

</div>

---

## 📞 Контакты и поддержка

- 📧 **Email**: info@softmontazh.kz
- 💬 **Telegram**: [@bySpecialist](https://t.me/bySpecialist)
- 🌐 **Веб-сайт**: *В разработке*
- 📍 **Местоположение**: Казахстан

### Техническая поддержка и разработка
- 🆘 **Поддержка**: [@LotBoxSup](https://t.me/LotBoxSup)
- 📋 **Issues**: Внутренний трекер (приватный доступ)
- 🔧 **Разработка**: Команда ТОО "СОФТМОНТАЖ"

---

<div align="center">

**🔒 Приватный репозиторий ТОО "СОФТМОНТАЖ"**

*Сделано с ❤️ в Казахстане для цифровизации ЖКХ*

---

**Статус проекта**: 🚧 **В активной разработке** | **MVP готов к тестированию**

</div>
