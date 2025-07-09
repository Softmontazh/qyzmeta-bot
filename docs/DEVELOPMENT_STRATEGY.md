# 🛠️ Стратегия разработки LotBox Platform

## 📂 Управление репозиториями

### 🎯 Рекомендуемый подход: **Мультирепозиторий с общим модулем**

#### Структура:
```
GitHub Organization: LotBox-Platform (или Softmontazh)
├── 📦 lotbox-platform-shared     # Общий модуль
├── 🔨 lotbox-bot                # Основная платформа
├── 🏠 qyzmeta-bot              # ЖКХ (текущий)
└── 💼 microfirm-kz             # CRM
```

## 🔄 Workflow разработки

### 1️⃣ **Этап 1: Создание shared модуля**
```bash
# Создаем новый репозиторий
git clone https://github.com/Softmontazh/lotbox-platform-shared.git
cd lotbox-platform-shared

# Структура shared модуля
mkdir -p shared/{database/{models,services,migrations},utils,config}
```

### 2️⃣ **Этап 2: Подключение shared к проектам**
```bash
# В каждом проекте (qyzmeta-bot, lotbox-bot, microfirm-kz)
git submodule add https://github.com/Softmontazh/lotbox-platform-shared.git shared

# Или как pip package (рекомендуется для продакшн)
pip install git+https://github.com/Softmontazh/lotbox-platform-shared.git
```

### 3️⃣ **Этап 3: Миграция текущего проекта**

#### Из qyzmeta-bot в shared переносим:
- `database/models/model_base.py` → `shared/database/models/base.py`
- `database/models/model_user.py` → `shared/database/models/user.py`
- `database/models/model_jk.py` → `shared/database/models/jk.py`
- `services/bus_service.py` → `shared/services/bus_service.py`

#### В qyzmeta-bot оставляем:
- Специфичные обработчики для ЖКХ
- FSM для жителей
- Клавиатуры для ЖКХ

## 🗄️ Стратегия базы данных

### Единая БД с префиксами:
```sql
-- LotBox основные таблицы
lotbox_lots
lotbox_projects
lotbox_marketplace

-- Qyzmeta таблицы (ЖКХ)
qyzmeta_offers (наследует от lotbox_lots)
qyzmeta_user_jk

-- MicrofirmKZ таблицы
microfirm_companies
microfirm_templates

-- Общие таблицы
platform_users
platform_jk
platform_bindings
```

## 📋 План поэтапной миграции

### Неделя 1: Подготовка
- [ ] Создать `lotbox-platform-shared` репозиторий
- [ ] Определить общие модели
- [ ] Создать базовую структуру shared

### Неделя 2: Миграция общих компонентов
- [ ] Перенести модели в shared
- [ ] Обновить импорты в qyzmeta-bot
- [ ] Протестировать работоспособность

### Неделя 3: Интеграция с LotBox
- [ ] Создать модель Lot в shared
- [ ] Адаптировать Offer как наследник Lot
- [ ] Реализовать UUID связи

### Неделя 4: Автоматические привязки
- [ ] Создать сервис привязок
- [ ] Реализовать уведомления между проектами
- [ ] Интеграция с MicrofirmKZ

## 🔧 Технические детали

### requirements.txt в каждом проекте:
```
# Общий модуль
-e git+https://github.com/Softmontazh/lotbox-platform-shared.git#egg=lotbox-shared

# Специфичные зависимости проекта
aiogram==3.20.0  # для ботов
fastapi==0.104.1  # для microfirm-kz
```

### .env конфигурация:
```env
# Общие настройки платформы
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/lotbox_platform
PLATFORM_SECRET_KEY=your_secret_key

# Проект-специфичные настройки
PROJECT_NAME=qyzmeta-bot
BOT_TOKEN=your_bot_token
```

## 🚀 Команды для разработчика

### Начало работы с любым проектом:
```bash
# 1. Клонируем проект
git clone https://github.com/Softmontazh/qyzmeta-bot.git
cd qyzmeta-bot

# 2. Инициализируем submodules
git submodule update --init --recursive

# 3. Устанавливаем зависимости
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 4. Читаем манифест платформы
cat docs/LOTBOX_PLATFORM_MANIFEST.md
```

### Обновление shared модуля:
```bash
# В shared репозитории
git commit -m "feat: добавлена новая модель"
git push

# В проектах
git submodule update --remote shared
git commit -m "update: обновлен shared модуль"
```

## 📊 Мониторинг и синхронизация

### GitHub Actions для автосинхронизации:
```yaml
# .github/workflows/sync-shared.yml
name: Sync Shared Module
on:
  repository_dispatch:
    types: [shared-updated]
jobs:
  update-shared:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Update submodule
        run: git submodule update --remote shared
```

## 🎯 Рекомендация для СЕЙЧАС

### Вариант A: Быстрый старт (рекомендую)
1. **Продолжаем в qyzmeta-bot** развивать MVP
2. **Создаем shared** параллельно по мере необходимости
3. **Переносим общее** когда будет готово к интеграции

### Вариант B: Полная реструктуризация
1. Останавливаем разработку
2. Создаем всю структуру сразу
3. Переносим все проекты

**Что выбираете?** 

Я рекомендую **Вариант A** - продолжаем в текущем проекте, а shared создаем по мере готовности компонентов.
