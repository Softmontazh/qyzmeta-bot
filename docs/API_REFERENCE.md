# 🔧 API Справочник Qyzmeta-Bot

> **Полное руководство по функциям, методам и API системы**

## 📑 Содержание

1. [ORM Функции](#-orm-функции)
2. [FSM Обработчики](#-fsm-обработчики)
3. [Сервисы](#-сервисы)
4. [Утилиты](#-утилиты)
5. [Middleware](#-middleware)
6. [Клавиатуры](#-клавиатуры)
7. [Enum и константы](#-enum-и-константы)

---

## 🗄️ ORM Функции

### 👤 Модель User (orm_user.py)

#### Основные операции

```python
async def orm_add_user(session: AsyncSession, user_data: dict) -> User:
    """Создание нового пользователя"""
    
async def orm_get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Получение пользователя по Telegram ID"""
    
async def orm_update_user_role(session: AsyncSession, user_id: int, role: UserRole) -> bool:
    """Изменение роли пользователя"""
    
async def orm_get_user_by_phone(session: AsyncSession, phone: str) -> User | None:
    """Поиск пользователя по номеру телефона"""
    
async def orm_get_users_by_role(session: AsyncSession, role: UserRole) -> List[User]:
    """Получение всех пользователей с определенной ролью"""
```

#### Продвинутые функции

```python
async def orm_update_user_profile(session: AsyncSession, user_id: int, profile_data: dict) -> bool:
    """Обновление профиля пользователя"""
    
async def orm_get_user_statistics(session: AsyncSession, user_id: int) -> Dict[str, Any]:
    """Получение статистики пользователя"""
    
async def orm_check_user_permissions(session: AsyncSession, user_id: int, permission: str) -> bool:
    """Проверка прав пользователя"""
```

### 🏢 Модель JK (orm_jk.py)

#### CRUD операции

```python
async def orm_add_jk(session: AsyncSession, jk_data: dict) -> JK:
    """Создание нового ЖК"""
    
async def orm_get_all_jks(session: AsyncSession) -> List[JK]:
    """Получение всех ЖК"""
    
async def orm_get_jk_by_id(session: AsyncSession, jk_id: int) -> JK | None:
    """Получение ЖК по ID"""
    
async def orm_update_jk(session: AsyncSession, jk_id: int, update_data: dict) -> bool:
    """Обновление данных ЖК"""
    
async def orm_delete_jk(session: AsyncSession, jk_id: int) -> bool:
    """Удаление ЖК"""
```

#### Поиск и фильтрация

```python
async def orm_search_jks(session: AsyncSession, query: str) -> List[JK]:
    """Поиск ЖК по названию, адресу"""
    
async def orm_get_jks_by_city(session: AsyncSession, city: str) -> List[JK]:
    """ЖК в определенном городе"""
    
async def orm_get_jks_by_creator(session: AsyncSession, creator_id: int) -> List[JK]:
    """ЖК созданные определенным пользователем"""
```

### 🔗 Модель UserJK (orm_user_jk.py)

#### Управление связями

```python
async def orm_add_user_jk(session: AsyncSession, user_id: int, jk_id: int, appartment: str) -> UserJK:
    """Привязка пользователя к ЖК"""
    
async def orm_get_jks_by_user_id(session: AsyncSession, user_id: int) -> List[Tuple[JK, UserJK]]:
    """ЖК пользователя"""
    
async def orm_get_users_by_jk_id(session: AsyncSession, jk_id: int) -> List[User]:
    """Жители ЖК"""
    
async def orm_delete_user_jk(session: AsyncSession, user_id: int, jk_id: int) -> bool:
    """Отвязка пользователя от ЖК"""
```

#### Роли в ЖК

```python
async def orm_get_admins_by_jk_id(session: AsyncSession, jk_id: int) -> List[User]:
    """Администраторы ЖК"""
    
async def orm_get_jks_by_user_admin(session: AsyncSession, user_id: int) -> List[JK]:
    """ЖК где пользователь - администратор"""
    
async def orm_set_admin_status(session: AsyncSession, user_id: int, jk_id: int, is_admin: bool) -> bool:
    """Назначение/снятие админа ЖК"""
    
async def orm_get_uk_by_jk_id(session: AsyncSession, jk_id: int) -> User | None:
    """Получение УК для ЖК"""
```

### 📝 Модель Offer (orm_offer.py)

#### Основные операции

```python
async def orm_add_offer(session: AsyncSession, offer_data: dict) -> Offer:
    """Создание новой заявки"""
    
async def orm_get_offer(session: AsyncSession, offer_id: int) -> Offer | None:
    """Получение заявки по ID"""
    
async def orm_get_offers_by_user(session: AsyncSession, user_id: int) -> List[Offer]:
    """Заявки пользователя"""
    
async def orm_update_offer_status(session: AsyncSession, offer_id: int, status: OfferStatus) -> bool:
    """Изменение статуса заявки"""
    
async def orm_delete_offer(session: AsyncSession, offer_id: int) -> bool:
    """Удаление заявки"""
```

#### Фильтрация и поиск

```python
async def orm_get_offers_by_category(session: AsyncSession, jk_id: int, category: OfferCategory) -> List[Offer]:
    """Заявки по категории"""
    
async def orm_get_active_offers(session: AsyncSession, jk_id: int) -> List[Offer]:
    """Активные заявки ЖК"""
    
async def orm_get_offers_by_status(session: AsyncSession, jk_id: int, status: OfferStatus) -> List[Offer]:
    """Заявки по статусу"""
    
async def orm_get_offers_paginated(session: AsyncSession, jk_id: int, page: int = 1, per_page: int = 20) -> List[Offer]:
    """Заявки с пагинацией"""
```

#### Статистика

```python
async def orm_get_offer_statistics(session: AsyncSession, jk_id: int) -> Dict[str, Any]:
    """Статистика заявок по ЖК"""
    
async def orm_get_completion_rate(session: AsyncSession, jk_id: int) -> float:
    """Процент выполненных заявок"""
    
async def orm_get_average_response_time(session: AsyncSession, jk_id: int) -> float:
    """Среднее время ответа на заявки"""
```

### 🏗️ Модель JKServiceProvider (orm_jk_service_provider.py)

#### Основные операции

```python
async def orm_add_service_provider(session: AsyncSession, service_data: dict) -> JKServiceProvider:
    """Создание заявки поставщика услуг (БЕЗ изменения роли)"""
    
async def orm_get_service_provider_by_id(session: AsyncSession, provider_id: int) -> JKServiceProvider | None:
    """Получение поставщика по ID"""
    
async def orm_get_service_providers_by_jk(session: AsyncSession, jk_id: int, active_only: bool = True) -> List[JKServiceProvider]:
    """Поставщики услуг ЖК"""
    
async def orm_update_service_provider(session: AsyncSession, provider_id: int, update_data: dict) -> JKServiceProvider | None:
    """Обновление данных поставщика"""
```

#### Поиск по категориям

```python
async def orm_get_service_provider_by_category(session: AsyncSession, jk_id: int, category: OfferCategory) -> JKServiceProvider | None:
    """Получить поставщика для категории (приоритетный)"""
    
async def orm_get_service_providers_by_user(session: AsyncSession, user_id: int) -> List[JKServiceProvider]:
    """Услуги где пользователь - ответственный"""
    
async def orm_get_responsible_for_offer_category(session: AsyncSession, jk_id: int, category: OfferCategory) -> int | None:
    """ID ответственного за категорию"""
```

#### Система заявок

```python
async def orm_create_service_provider_request(session: AsyncSession, jk_id: int, category: str, responsible_user_id: int, **kwargs) -> int:
    """Создать заявку на статус поставщика (БЕЗ изменения роли)"""
    
async def orm_activate_service_provider_request(session: AsyncSession, provider_id: int, activated_by_user_id: int) -> bool:
    """Активировать заявку поставщика (С изменением роли)"""
    
async def orm_reject_service_provider_request(session: AsyncSession, provider_id: int, rejected_by_user_id: int) -> bool:
    """Отклонить заявку поставщика"""
    
async def orm_get_pending_service_provider_requests(session: AsyncSession, jk_id: int = None) -> List[JKServiceProvider]:
    """Получить заявки на рассмотрении"""
```

#### Управление и проверки

```python
async def orm_check_user_manages_category(session: AsyncSession, user_id: int, jk_id: int, category: OfferCategory) -> bool:
    """Проверить права управления категорией"""
    
async def orm_get_categories_managed_by_user(session: AsyncSession, user_id: int, jk_id: int) -> List[OfferCategory]:
    """Категории под управлением пользователя"""
    
async def orm_get_working_providers_now(session: AsyncSession, jk_id: int) -> List[JKServiceProvider]:
    """Поставщики работающие сейчас"""
    
async def orm_deactivate_service_provider(session: AsyncSession, provider_id: int) -> bool:
    """Деактивировать поставщика (мягкое удаление)"""
```

### 📢 Модель Lot (orm_lot.py)

#### CRUD операции

```python
async def orm_add_lot(session: AsyncSession, lot_data: dict) -> Lot:
    """Создание нового лота"""
    
async def orm_get_lot(session: AsyncSession, lot_id: int) -> Lot | None:
    """Получение лота по ID"""
    
async def orm_get_lots_by_user(session: AsyncSession, user_id: int) -> List[Lot]:
    """Лоты пользователя"""
    
async def orm_update_lot(session: AsyncSession, lot_id: int, update_data: dict) -> bool:
    """Обновление лота"""
    
async def orm_delete_lot(session: AsyncSession, lot_id: int) -> bool:
    """Удаление лота"""
```

#### Поиск и фильтрация

```python
async def orm_get_lots_by_type(session: AsyncSession, offer_type: LotOfferType) -> List[Lot]:
    """Лоты по типу предложения"""
    
async def orm_search_lots(session: AsyncSession, query: str) -> List[Lot]:
    """Поиск лотов по тексту"""
    
async def orm_get_active_lots(session: AsyncSession, limit: int = 50) -> List[Lot]:
    """Активные лоты"""
```

---

## 🤖 FSM Обработчики

### 📝 Создание заявок (add_offer_fsm.py)

#### Состояния FSM

```python
class AddOfferStates(StatesGroup):
    input_title = State()      # Ввод заголовка
    select_category = State()  # Выбор категории
    input_body = State()       # Описание проблемы
    input_media = State()      # Загрузка медиа
    confirm = State()          # Подтверждение
```

#### Основные обработчики

```python
@router.message(Command("create_offer"))
async def cmd_create_offer(message: Message, state: FSMContext, session: AsyncSession):
    """Команда создания заявки"""

@router.message(AddOfferStates.input_title)
async def handle_title_input(message: Message, state: FSMContext):
    """Обработка ввода заголовка"""

@router.callback_query(F.data.startswith("category:"))
async def handle_category_selection(callback: CallbackQuery, state: FSMContext):
    """Выбор категории заявки"""

@router.message(AddOfferStates.input_media)
async def handle_media_upload(message: Message, state: FSMContext):
    """Загрузка фото/видео"""
```

### 🏗️ Заявки поставщиков (become_service_provider_fsm.py)

#### Состояния FSM

```python
class BecomeServiceProviderStates(StatesGroup):
    select_jk = State()          # Выбор ЖК
    select_category = State()    # Выбор категории
    input_organization = State() # Название организации
    input_phone = State()        # Контактный телефон  
    input_email = State()        # Email (опционально)
    input_description = State()  # Описание услуг
    confirm_request = State()    # Подтверждение заявки
```

#### Ключевые функции

```python
async def start_become_service_provider(message: Message, state: FSMContext, session: AsyncSession):
    """Начало процесса подачи заявки"""

async def confirm_service_request(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Подтверждение и создание заявки поставщика"""
```

### 🔧 Управление поставщиками (manage_service_providers_fsm.py)

#### Состояния FSM

```python
class ManageServiceProviderStates(StatesGroup):
    select_jk_for_add = State()   # Выбор ЖК для добавления
    select_category = State()     # Выбор категории
    input_user_id = State()       # Ввод User ID ответственного
    input_org_info = State()      # Информация об организации
    input_phone = State()         # Контактный телефон
    input_work_schedule = State() # Рабочее время
    confirm_provider = State()    # Подтверждение создания
```

#### Административные функции

```python
async def handle_pending_requests_button(message: Message, state: FSMContext, session: AsyncSession):
    """Показать заявки на рассмотрении"""

async def approve_service_request(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Одобрить заявку поставщика"""

async def reject_service_request(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Отклонить заявку поставщика"""
```

### 🏢 Управление ЖК (manage_jk_fsm.py)

#### Состояния и функции

```python
class ManageJKStates(StatesGroup):
    select_jk = State()       # Выбор ЖК для редактирования
    edit_field = State()      # Выбор поля для изменения
    input_new_value = State() # Ввод нового значения
    confirm_changes = State() # Подтверждение изменений

async def cmd_manage_jk(message: Message, state: FSMContext, session: AsyncSession):
    """Команда управления ЖК (только для создателей)"""

async def handle_jk_selection(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка выбора ЖК для редактирования"""
```

---

## 🔧 Сервисы

### 🚌 BUS Service (bus_service.py)

#### Основные функции

```python
def generate_bus_id(file_id: str) -> str:
    """Генерация уникального BUS_ID для файла"""
    # Формат: BUS_XXXXXXXXXXXXXX (16 символов)

async def send_to_bus_channel(bot: Bot, file_id: str, bus_id: str) -> str:
    """Отправка файла в BUS канал и получение нового file_id"""

def validate_bus_id(bus_id: str) -> bool:
    """Валидация формата BUS_ID"""

async def get_file_by_bus_id(session: AsyncSession, bus_id: str) -> str | None:
    """Получение file_id по BUS_ID"""
```

#### Использование

```python
# Создание BUS_ID для изображения ЖК
bus_id = bus_service.generate_bus_id(original_file_id)
bus_file_id = await bus_service.send_to_bus_channel(bot, original_file_id, bus_id)

# Сохранение в БД
jk_data = {
    "image_id": original_file_id,  # Локальный file_id
    "bus_image_id": bus_id,        # Уникальный BUS_ID
    # ... другие поля
}
```

### 🔐 Service Provider Service (service_provider_service.py)

#### Проверки доступа

```python
async def check_service_management_access(user_id: int, session: AsyncSession, jk_id: int = None) -> Tuple[bool, str]:
    """Проверка прав на управление поставщиками услуг"""

async def validate_responsible_user(user_id: int, session: AsyncSession) -> Tuple[bool, str, Dict]:
    """Валидация ответственного пользователя"""

def validate_organization_name(name: str) -> Tuple[bool, str]:
    """Валидация названия организации"""

def validate_work_schedule(schedule: str) -> Tuple[bool, str]:
    """Валидация рабочего времени"""
```

### 👤 User Service (user_service.py)

#### Управление пользователями

```python
async def get_user_profile(session: AsyncSession, user_id: int) -> Dict[str, Any]:
    """Получение полного профиля пользователя"""

async def update_user_language(session: AsyncSession, user_id: int, language: UserLanguage) -> bool:
    """Изменение языка интерфейса"""

async def check_user_registration(session: AsyncSession, user_id: int) -> bool:
    """Проверка регистрации пользователя"""

async def get_user_permissions(session: AsyncSession, user_id: int) -> List[str]:
    """Получение списка разрешений пользователя"""
```

### 📢 Lot Service (lot_service.py)

#### Управление лотами

```python
async def create_lot_with_validation(session: AsyncSession, user_id: int, lot_data: dict) -> Tuple[bool, str, Lot | None]:
    """Создание лота с проверкой лимитов"""

async def check_daily_limit(session: AsyncSession, user_id: int) -> Tuple[bool, int, int]:
    """Проверка дневного лимита"""

async def get_lot_statistics(session: AsyncSession, user_id: int) -> Dict[str, Any]:
    """Статистика лотов пользователя"""
```

### 📱 Notification Service (notification_service.py)

#### Система уведомлений

```python
async def send_offer_notification(bot: Bot, user_id: int, offer: Offer) -> bool:
    """Отправка уведомления о новой заявке"""

async def send_status_update(bot: Bot, user_id: int, offer: Offer, old_status: OfferStatus, new_status: OfferStatus) -> bool:
    """Уведомление об изменении статуса"""

async def send_service_provider_notification(bot: Bot, user_id: int, provider: JKServiceProvider, action: str) -> bool:
    """Уведомления для поставщиков услуг"""

async def notify_admins_about_new_request(session: AsyncSession, bot: Bot, provider_id: int) -> bool:
    """Уведомление админов о новой заявке поставщика"""
```

---

## 🛠️ Утилиты

### 📞 Phone Validator (phone_validator.py)

#### Класс PhoneValidator

```python
class PhoneValidator:
    @staticmethod
    def validate_and_format(phone: str) -> Tuple[bool, str | None, str]:
        """Валидация и форматирование номера телефона"""
        # Возвращает: (is_valid, formatted_phone, error_message)
    
    @staticmethod
    def is_kazakhstan_number(phone: str) -> bool:
        """Проверка на казахстанский номер"""
    
    @staticmethod
    def format_display(phone: str) -> str:
        """Форматирование для отображения"""
        # +7 (701) 123-45-67
```

#### Примеры использования

```python
# Валидация пользовательского ввода
is_valid, formatted, error = PhoneValidator.validate_and_format("+77011234567")

if is_valid:
    user.phone_number = formatted
else:
    await message.answer(f"❌ {error}")

# Проверка казахстанского номера
if PhoneValidator.is_kazakhstan_number(phone):
    # Специальная обработка для КЗ номеров
    pass
```

### ✅ Registration Check (registration_check.py)

#### Функции проверки

```python
async def check_user_registration(session: AsyncSession, user_id: int) -> bool:
    """Проверка регистрации пользователя в системе"""

async def ensure_user_registered(session: AsyncSession, user: types.User) -> User:
    """Обеспечивает регистрацию пользователя (создает если нет)"""

async def get_or_create_user(session: AsyncSession, telegram_user: types.User) -> Tuple[User, bool]:
    """Получить или создать пользователя. Возвращает (user, created)"""
```

---

## 🔄 Middleware

### 🗄️ Database Middleware (db.py)

#### DbSessionMiddleware

```python
class DbSessionMiddleware(BaseMiddleware):
    """Middleware для автоматического предоставления сессии БД"""
    
    async def __call__(self, handler, event, data):
        async with async_session_maker() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
```

#### Использование

```python
# В обработчиках автоматически доступна сессия
@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession):
    user = await orm_get_user_by_id(session, message.from_user.id)
    # session автоматически коммитится или откатывается
```

---

## ⌨️ Клавиатуры

### 🔘 Inline Keyboards

#### Service Provider Keyboards (service_provider_keyboards.py)

```python
def get_category_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора категории услуг"""

def get_jk_selection_keyboard(jks: List[JK], page: int = 0) -> InlineKeyboardMarkup:
    """Клавиатура выбора ЖК с пагинацией"""

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""

def get_phone_input_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой 'Пропустить' для ввода телефона"""
```

#### JK Management Keyboards (inline_for_jk.py)

```python
def get_btns_control_jk(user_jk_id: int) -> InlineKeyboardMarkup:
    """Кнопки управления ЖК для жителей"""

def unlink_keyboard(user_jk_id: int) -> InlineKeyboardMarkup:
    """Кнопка отвязки от ЖК"""

def get_jk_admin_keyboard(jk_id: int) -> InlineKeyboardMarkup:
    """Административные кнопки для ЖК"""
```

#### Offer Management (inline_for_lot.py)

```python
def get_btns_control_lots(user_id: int) -> InlineKeyboardMarkup:
    """Кнопки управления лотами пользователя"""

def get_offer_status_keyboard(offer_id: int) -> InlineKeyboardMarkup:
    """Кнопки изменения статуса заявки"""
```

### 📱 Reply Keyboards (reply.py)

#### Основные клавиатуры

```python
# Главная клавиатура для жителей
MAIN_KB = ReplyKeyboardMarkup(...)

# Клавиатура админа ЖК
ADMIN_JK_KB = ReplyKeyboardMarkup(...)

# Клавиатура поставщика услуг  
SERVICE_PROVIDER_KB = ReplyKeyboardMarkup(...)

# Клавиатура управления поставщиками
CONTROL_SERVICE_PROVIDER_KB = ReplyKeyboardMarkup(...)

def get_keyboard(user_role: UserRole) -> ReplyKeyboardMarkup:
    """Получение клавиатуры по роли пользователя"""
```

---

## 📊 Enum и константы

### 👤 User Enums (user_enums.py)

```python
class UserLanguage(str, Enum):
    RU = "RU"  # Русский
    KZ = "KZ"  # Казахский

class UserRole(IntEnum):
    USER = 1                # Житель
    VIP_USER = 2           # VIP житель  
    MODERATOR = 3          # Модератор
    ADMIN_JK = 4           # Админ ЖК (ОСИ)
    UK = 5                 # Управляющая компания
    SERVICE_PROVIDER = 6   # Поставщик услуг
    ADMIN = 7              # Администратор
    SUPER_ADMIN = 8        # Супер админ
    CREATOR = 9            # Создатель
    SYSTEM = 10            # Системная роль
```

### 📝 Offer Enums (offer_enums.py)

```python
class OfferStatus(str, Enum):
    ACTIVE = "active"         # Новая заявка
    IN_PROGRESS = "progress"  # В работе
    COMPLETED = "completed"   # Выполнена
    CANCELLED = "cancelled"   # Отменена
    ON_HOLD = "on_hold"      # Приостановлена

class OfferCategory(str, Enum):
    DOMOFON = "domofon"              # Домофон 🔔
    VIDEO = "video"                  # Видеонаблюдение 📹
    ELEKTRIKA = "elektrika"          # Электрика ⚡
    SANTEHNIKA = "santehnika"        # Сантехника 🚿
    BLAGOUSTROYSTVO = "blagoustroystvo"  # Благоустройство 🌳
    REPAIR = "repair"                # Ремонт 🔧
    DRUGOE = "drugoe"               # Другое 📝
    
    @property
    def display_name(self) -> str:
        """Отображаемое название"""
    
    @property  
    def emoji(self) -> str:
        """Эмодзи категории"""
    
    @classmethod
    def from_string(cls, value: str) -> "OfferCategory":
        """Создание из строки"""
```

### 📢 Lot Enums (lot_enums.py)

```python
class LotOfferType(str, Enum):
    SELL = "sell"         # Продажа
    BUY = "buy"           # Покупка  
    RENT = "rent"         # Аренда
    SERVICE = "service"   # Услуги
    EXCHANGE = "exchange" # Обмен
    GIFT = "gift"         # Дарю
    FIND = "find"         # Поиск
    OTHER = "other"       # Другое

class LotStatus(str, Enum):
    ACTIVE = "active"       # Активный
    SOLD = "sold"           # Продан
    EXPIRED = "expired"     # Истек
    CANCELLED = "cancelled" # Отменен
    ARCHIVED = "archived"   # Архивный

class LotVisibility(str, Enum):
    PUBLIC = "public"     # Публичный
    JK_ONLY = "jk_only"   # Только ЖК
    PRIVATE = "private"   # Приватный
```

---

## 🔧 Фильтры

### 💬 Chat Types (chat_types.py)

```python
class ChatTypeFilter(BaseFilter):
    """Фильтр по типу чата"""
    
    def __init__(self, chat_types: Union[str, List[str]]):
        self.chat_types = chat_types

class IsAdmin(BaseFilter):
    """Фильтр для проверки роли администратора"""
    
    async def __call__(self, message: Message, session: AsyncSession) -> bool:
        user = await orm_get_user_by_id(session, message.from_user.id)
        return user and user.role >= UserRole.ADMIN_JK
```

---

## 📱 Константы и настройки

### 🎨 Эмодзи и символы

```python
# Категории услуг
CATEGORY_EMOJIS = {
    "domofon": "🔔",
    "video": "📹", 
    "elektrika": "⚡",
    "santehnika": "🚿",
    "blagoustroystvo": "🌳",
    "repair": "🔧",
    "drugoe": "📝"
}

# Статусы заявок
STATUS_EMOJIS = {
    "active": "🟡",
    "progress": "🔵", 
    "completed": "🟢",
    "cancelled": "🔴",
    "on_hold": "🟠"
}

# Роли пользователей
ROLE_EMOJIS = {
    UserRole.USER: "👤",
    UserRole.ADMIN_JK: "👨‍💼",
    UserRole.SERVICE_PROVIDER: "🔧",
    UserRole.ADMIN: "👨‍💻"
}
```

### 📏 Лимиты и ограничения

```python
# Лимиты файлов
MAX_PHOTO_SIZE_MB = 10
MAX_VIDEO_SIZE_MB = 50
ALLOWED_PHOTO_FORMATS = ["jpg", "jpeg", "png", "webp"]
ALLOWED_VIDEO_FORMATS = ["mp4", "mov", "avi"]

# Лимиты текста
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000
MAX_ORGANIZATION_NAME_LENGTH = 200

# Лимиты лотов по ролям
LOT_LIMITS = {
    UserRole.USER: {"daily": 3, "monthly": 20},
    UserRole.VIP_USER: {"daily": 10, "monthly": 100},
    UserRole.ADMIN_JK: {"daily": 20, "monthly": 500},
}

# Пагинация
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
```

---

## 🚀 Примеры интеграции

### Создание кастомного обработчика

```python
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.orm_user import orm_get_user_by_id
from database.enums.user_enums import UserRole

custom_router = Router()

@custom_router.message(F.text == "Моя функция")
async def my_custom_handler(message: Message, session: AsyncSession):
    # Получаем пользователя
    user = await orm_get_user_by_id(session, message.from_user.id)
    
    # Проверяем права
    if user.role < UserRole.ADMIN_JK:
        await message.answer("❌ Недостаточно прав")
        return
    
    # Выполняем логику
    await message.answer("✅ Функция выполнена")
```

### Создание сервиса

```python
# services/my_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

async def get_custom_statistics(session: AsyncSession, jk_id: int) -> Dict[str, Any]:
    """Кастомная статистика для ЖК"""
    
    # Запросы к БД
    total_users = await orm_count_users_by_jk(session, jk_id)
    active_offers = await orm_count_active_offers(session, jk_id)
    
    return {
        "total_users": total_users,
        "active_offers": active_offers,
        "calculated_at": datetime.utcnow()
    }

# Использование в обработчике
from services.my_service import get_custom_statistics

@router.message(F.text == "Статистика")
async def show_statistics(message: Message, session: AsyncSession):
    stats = await get_custom_statistics(session, jk_id)
    await message.answer(f"📊 Статистика: {stats}")
```

---

*Справочник обновлен: 14 июля 2025 г.*  
*Версия API: 2.1.0*
