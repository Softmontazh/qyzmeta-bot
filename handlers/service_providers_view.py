"""
Модуль для просмотра поставщиков услуг в ЖК
Предоставляет функциональность просмотра сервисных компаний с навигацией
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import traceback

from database.models.orm_jk_service_provider import orm_get_service_providers_by_jk
from database.models.orm_user_jk import orm_get_user_jk_with_jk_by_id
from database.models.model_jk_service_provider import JKServiceProvider
from database.models.model_jk import JK
from database.models.model_user_jk import UserJK
from database.enums.offer_category_enum import OfferCategory


router = Router()


def escape_html(text: str) -> str:
    """Экранирует HTML символы для безопасного отображения"""
    if not text:
        return ""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))


def escape_for_button_text(text: str) -> str:
    """Экранирует текст для использования в кнопках (БЕЗ замены кавычек)"""
    if not text:
        return ""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;'))
    # НЕ заменяем кавычки - они нормально отображаются в тексте кнопок


def check_message_length(text: str, max_length: int = 4096) -> str:
    """Проверяет и обрезает сообщение если оно слишком длинное"""
    if len(text) > max_length:
        print(f"WARNING: Сообщение слишком длинное: {len(text)} символов, обрезаем до {max_length}")
        # Обрезаем с запасом, чтобы добавить предупреждение
        truncated = text[:max_length - 100]
        # Ищем последний перенос строки, чтобы не обрезать посреди слова
        last_newline = truncated.rfind('\n')
        if last_newline > max_length // 2:  # Если есть перенос строки во второй половине
            truncated = truncated[:last_newline]
        return truncated + "\n\n⚠️ <i>Сообщение обрезано из-за ограничений Telegram</i>"
    return text


async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup=None, parse_mode="HTML"):
    """Безопасное обновление сообщения с fallback на удаление и отправку нового"""
    try:
        # Проверяем длину сообщения
        text = check_message_length(text)
        
        print(f"DEBUG: Попытка safe_edit_message, длина: {len(text)}")
        await callback.message.edit_text(
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
        print(f"DEBUG: safe_edit_message успешно выполнен")
    except TelegramBadRequest as e:
        print(f"WARNING: edit_text failed: {e}, пробуем альтернативный способ")
        try:
            # Пробуем удалить старое сообщение и отправить новое
            await callback.message.delete()
            await callback.message.answer(
                text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            print(f"DEBUG: Альтернативный способ (delete + answer) успешен")
        except Exception as fallback_error:
            print(f"ERROR: Альтернативный способ тоже не сработал: {fallback_error}")
            # В крайнем случае просто отвечаем пользователю
            await callback.answer("❌ Не удалось обновить сообщение. Попробуйте еще раз.", show_alert=True)
            raise


def create_service_providers_keyboard(providers: list, current_page: int = 0, total_pages: int = 1, jk_id: int = None) -> InlineKeyboardMarkup:
    """Создает клавиатуру для просмотра поставщиков услуг"""
    keyboard = []
    
    # Кнопки с поставщиками (по 1 на строку для лучшего отображения)
    for provider in providers:
        # Создаем текст кнопки с названием и категорией
        button_text = f"🏢 {escape_for_button_text(provider.organization_name)}"
        if provider.category:
            # Получаем русское название категории
            category_names = {
                OfferCategory.DOMOFON: "Домофон",
                OfferCategory.VIDEO: "Видеонаблюдение", 
                OfferCategory.ELEKTRIKA: "Электрика",
                OfferCategory.SANTEHNIKA: "Сантехника",
                OfferCategory.BLAGOUSTROYSTVO: "Благоустройство",
                OfferCategory.REPAIR: "Ремонт",
                OfferCategory.DRUGOE: "Другое"
            }
            # Правильно обрабатываем enum
            if isinstance(provider.category, str):
                category_enum = OfferCategory.from_string(provider.category)
            else:
                category_enum = provider.category
            
            category_display = category_names.get(category_enum, category_enum.display_name)
            button_text += f" | {escape_for_button_text(category_display)}"
        
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"provider_details:{provider.id}"
            )
        ])
    
    # Кнопки навигации
    navigation_row = []
    
    if current_page > 0:
        navigation_row.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"providers_page:{jk_id}:{current_page - 1}"
            )
        )
    
    if current_page < total_pages - 1:
        navigation_row.append(
            InlineKeyboardButton(
                text="Вперед ▶️",
                callback_data=f"providers_page:{jk_id}:{current_page + 1}"
            )
        )
    
    if navigation_row:
        keyboard.append(navigation_row)
    
    # Кнопка "Назад к ЖК"
    keyboard.append([
        InlineKeyboardButton(
            text="🏠 Назад к ЖК",
            callback_data=f"back_to_jk:{jk_id}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def format_provider_details_message(provider: JKServiceProvider, jk: JK) -> str:
    """Форматирование детального сообщения о поставщике"""
    text = f"🏛️ <b>Детали сервисной компании</b>\n\n"
    
    # Основная информация
    text += f"<b>Организация:</b> {escape_html(provider.organization_name or 'Не указано')}\n"
    text += f"<b>ЖК:</b> {escape_html(jk.name)}\n"
    
    # Категория с emoji
    if provider.category:
        text += f"<b>Услуга:</b> {provider.category.display_name} {provider.category.emoji}\n"
    
    text += "\n━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Контактная информация
    text += f"📞 <b>Контакты:</b>\n"
    if provider.contact_phone:
        text += f"• Телефон: {escape_html(provider.contact_phone)}\n"
    if provider.contact_email:
        text += f"• Email: {escape_html(provider.contact_email)}\n"
    if not provider.contact_phone and not provider.contact_email:
        text += f"• Контакты не указаны\n"
    
    text += "\n"
    
    # Рабочее время
    text += f"🕒 <b>Режим работы:</b>\n"
    if provider.work_hours_start and provider.work_hours_end:
        text += f"• Время: {provider.work_hours_start} - {provider.work_hours_end}\n"
    
    if provider.work_days:
        days_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        work_days_list = []
        for i, day in enumerate(days_names):
            if provider.work_days & (1 << i):
                work_days_list.append(day)
        if work_days_list:
            text += f"• Дни: {', '.join(work_days_list)}\n"
    
    if provider.description:
        text += f"• Описание: {escape_html(provider.description)}\n"
    
    if not provider.work_hours_start and not provider.work_days and not provider.description:
        text += f"• Режим работы не указан\n"
    
    text += "\n"
    
    # Дополнительная информация
    if provider.contract_number:
        text += f"📋 <b>Договор:</b> {escape_html(provider.contract_number)}\n"
        
        if provider.contract_start_date and provider.contract_end_date:
            start_date = provider.contract_start_date.strftime("%d.%m.%Y")
            end_date = provider.contract_end_date.strftime("%d.%m.%Y")
            text += f"📅 <b>Период:</b> {start_date} - {end_date}\n"
        text += "\n"
    
    # Статус и приоритет
    text += f"⚙️ <b>Настройки:</b>\n"
    text += f"• Статус: {'🟢 Активен' if provider.is_active else '🔴 Неактивен'}\n"
    text += f"• Уведомления: {'✅ Включены' if provider.receives_notifications else '❌ Отключены'}\n"
    text += f"• Приоритет: {provider.priority}\n"
    
    text += "\n━━━━━━━━━━━━━━━━━━━━\n"
    text += f"💡 <i>Для создания заявки используйте \"Создать заявку\" в главном меню</i>"
    
    return check_message_length(text)


def get_provider_details_keyboard(provider_id: int, user_jk_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для детального просмотра поставщика"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📋 К списку поставщиков",
                callback_data=f"back_to_providers:{user_jk_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Назад к ЖК",
                callback_data=f"back_to_jk_from_provider:{user_jk_id}"
            )
        ]
    ])
    return keyboard


def create_provider_details_keyboard(provider_id: int, jk_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для детального просмотра поставщика"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📞 Связаться",
                    callback_data=f"contact_provider:{provider_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ К списку поставщиков",
                    callback_data=f"view_service_providers:{jk_id}"
                )
            ]
        ]
    )


@router.callback_query(F.data.startswith("view_service_providers:"))
async def view_service_providers_handler(callback: CallbackQuery, session: AsyncSession):
    """Обработчик просмотра поставщиков услуг для ЖК"""
    try:
        print(f"DEBUG: Начало обработки view_service_providers")
        user_jk_id = int(callback.data.split(":")[1])
        print(f"DEBUG: user_jk_id = {user_jk_id}")
        
        # Получаем информацию о связи пользователя с ЖК
        user_jk_result = await orm_get_user_jk_with_jk_by_id(session, user_jk_id)
        print(f"DEBUG: user_jk_result найден: {user_jk_result is not None}")
        
        if not user_jk_result:
            await callback.answer("❌ ЖК не найден")
            return
        
        user_jk, jk = user_jk_result
        print(f"DEBUG: ЖК найден: {escape_html(jk.name)}")
        
        # Получаем поставщиков для данного ЖК
        providers = await orm_get_service_providers_by_jk(session, jk.id)
        print(f"DEBUG: Найдено поставщиков: {len(providers)}")
        
        for i, provider in enumerate(providers):
            print(f"DEBUG: Поставщик {i+1}: {escape_html(provider.organization_name)}, категория: {provider.category}")
        
        if not providers:
            message_text = (
                f"🏢 <b>Сервисные компании</b>\n\n"
                f"🏠 <b>ЖК:</b> {escape_html(jk.name)}\n\n"
                f"📭 В данном ЖК пока нет зарегистрированных сервисных компаний.\n\n"
                f"💡 <i>Сервисные компании смогут откликаться на ваши заявки после регистрации в системе.</i>"
            )
            
            print(f"DEBUG: Нет поставщиков. Длина сообщения: {len(message_text)} символов")
            print(f"DEBUG: Текст сообщения: {message_text[:200]}...")
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🏠 Назад к ЖК",
                            callback_data=f"back_to_jk:{user_jk_id}"
                        )
                    ]
                ]
            )
            
            print(f"DEBUG: Попытка обновления сообщения (нет поставщиков)")
            await safe_edit_message(
                callback,
                message_text,
                reply_markup=keyboard
            )
            print(f"DEBUG: Сообщение успешно обновлено (нет поставщиков)")
        else:
            # Пагинация - показываем по 5 поставщиков на страницу
            page_size = 5
            total_pages = (len(providers) + page_size - 1) // page_size
            current_page = 0
            start_idx = current_page * page_size
            end_idx = start_idx + page_size
            page_providers = providers[start_idx:end_idx]
            
            message_text = (
                f"🏢 <b>Сервисные компании</b>\n\n"
                f"🏠 <b>ЖК:</b> {escape_html(jk.name)}\n"
                f"📊 <b>Всего компаний:</b> {len(providers)}\n\n"
                f"📋 <i>Выберите компанию для получения подробной информации:</i>"
            )
            
            if total_pages > 1:
                message_text += f"\n\n📄 Страница {current_page + 1} из {total_pages}"
            
            print(f"DEBUG: Есть поставщики. Длина сообщения: {len(message_text)} символов")
            print(f"DEBUG: Первые 200 символов: {message_text[:200]}")
            
            keyboard = create_service_providers_keyboard(
                page_providers, current_page, total_pages, user_jk_id
            )
            print(f"DEBUG: Клавиатура создана, кнопок: {len(keyboard.inline_keyboard)}")
            
            # Проверяем callback_data на длину
            for row in keyboard.inline_keyboard:
                for button in row:
                    if hasattr(button, 'callback_data') and button.callback_data:
                        if len(button.callback_data) > 64:
                            print(f"WARNING: callback_data слишком длинный: {len(button.callback_data)} - {button.callback_data}")
            
            print(f"DEBUG: Попытка обновления сообщения (есть поставщики)")
            await safe_edit_message(
                callback,
                message_text,
                reply_markup=keyboard
            )
            print(f"DEBUG: Сообщение успешно обновлено (есть поставщики)")
        
        await callback.answer()
        print(f"DEBUG: callback.answer() выполнен")
        
    except (ValueError, IndexError) as e:
        print(f"ERROR: Ошибка парсинга данных: {e}")
        await callback.answer("❌ Ошибка обработки запроса")
    except TelegramBadRequest as e:
        print(f"ERROR: TelegramBadRequest: {e}")
        print(f"ERROR: Тип ошибки: {type(e)}")
        print(f"ERROR: Трейсбек:\n{traceback.format_exc()}")
        await callback.answer("❌ Не удалось обновить сообщение")
    except Exception as e:
        print(f"ERROR: Общая ошибка в view_service_providers_handler: {e}")
        print(f"ERROR: Тип ошибки: {type(e)}")
        print(f"ERROR: Трейсбек:\n{traceback.format_exc()}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("providers_page:"))
async def providers_pagination_handler(callback: CallbackQuery, session: AsyncSession):
    """Обработчик пагинации поставщиков"""
    try:
        print(f"DEBUG: Начало обработки providers_page")
        _, jk_id, page = callback.data.split(":")
        jk_id = int(jk_id)
        page = int(page)
        print(f"DEBUG: jk_id = {jk_id}, page = {page}")
        
        # Получаем информацию о связи пользователя с ЖК
        user_jk_result = await orm_get_user_jk_with_jk_by_id(session, jk_id)
        if not user_jk_result:
            await callback.answer("❌ ЖК не найден")
            return
        
        user_jk, jk = user_jk_result
        print(f"DEBUG: ЖК найден для пагинации: {escape_html(jk.name)}")
        
        # Получаем поставщиков для данного ЖК
        providers = await orm_get_service_providers_by_jk(session, jk.id)
        print(f"DEBUG: Найдено поставщиков для пагинации: {len(providers)}")
        
        if not providers:
            await callback.answer("❌ Поставщики не найдены")
            return
        
        # Пагинация
        page_size = 5
        total_pages = (len(providers) + page_size - 1) // page_size
        print(f"DEBUG: total_pages = {total_pages}, запрошенная page = {page}")
        
        if page < 0 or page >= total_pages:
            await callback.answer("❌ Страница не найдена")
            return
        
        start_idx = page * page_size
        end_idx = start_idx + page_size
        page_providers = providers[start_idx:end_idx]
        print(f"DEBUG: Показываем поставщиков с {start_idx} по {end_idx}")
        
        message_text = (
            f"🏢 <b>Сервисные компании</b>\n\n"
            f"🏠 <b>ЖК:</b> {escape_html(jk.name)}\n"
            f"📊 <b>Всего компаний:</b> {len(providers)}\n\n"
            f"📋 <i>Выберите компанию для получения подробной информации:</i>"
        )
        
        if total_pages > 1:
            message_text += f"\n\n📄 Страница {page + 1} из {total_pages}"
        
        print(f"DEBUG: Длина сообщения пагинации: {len(message_text)} символов")
        
        keyboard = create_service_providers_keyboard(
            page_providers, page, total_pages, jk_id
        )
        
        print(f"DEBUG: Попытка обновления сообщения (пагинация)")
        await safe_edit_message(
            callback,
            message_text,
            reply_markup=keyboard
        )
        print(f"DEBUG: Сообщение пагинации успешно обновлено")
        
        await callback.answer()
        
    except (ValueError, IndexError) as e:
        print(f"ERROR: Ошибка парсинга в пагинации: {e}")
        await callback.answer("❌ Ошибка обработки запроса")
    except TelegramBadRequest as e:
        print(f"ERROR: TelegramBadRequest в пагинации: {e}")
        print(f"ERROR: Трейсбек пагинации:\n{traceback.format_exc()}")
        await callback.answer("❌ Не удалось обновить сообщение")
    except Exception as e:
        print(f"ERROR: Общая ошибка в providers_pagination_handler: {e}")
        print(f"ERROR: Трейсбек:\n{traceback.format_exc()}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("provider_details:"))
async def provider_details_handler(callback: CallbackQuery, session: AsyncSession):
    """Показать детальную информацию о поставщике услуг"""
    try:
        provider_id = int(callback.data.split(":")[1])
        print(f"DEBUG: Показ деталей поставщика {provider_id}")
        
        # Получаем поставщика с информацией о ЖК
        result = await session.execute(
            select(JKServiceProvider, JK)
            .join(JK, JKServiceProvider.jk_id == JK.id)
            .where(JKServiceProvider.id == provider_id)
        )
        provider_data = result.first()
        
        if not provider_data:
            await callback.answer("❌ Поставщик не найден", show_alert=True)
            return
            
        provider, jk = provider_data
        print(f"DEBUG: Найден поставщик: {provider.organization_name} в ЖК {jk.name}")
        
        # Находим user_jk_id для правильной навигации
        user_id = callback.from_user.id
        user_jk_result = await session.execute(
            select(UserJK).where(
                UserJK.user_id == user_id,
                UserJK.jk_id == jk.id
            )
        )
        user_jk = user_jk_result.scalar_one_or_none()
        
        if not user_jk:
            await callback.answer("❌ ЖК не найден в ваших подключениях", show_alert=True)
            return
        
        # Формируем детальное сообщение
        message_text = await format_provider_details_message(provider, jk)
        print(f"DEBUG: Сформировано сообщение деталей, длина: {len(message_text)}")
        
        # Клавиатура с кнопками действий
        keyboard = get_provider_details_keyboard(provider.id, user_jk.id)
        
        await safe_edit_message(
            callback,
            message_text,
            reply_markup=keyboard
        )
        await callback.answer()
        
    except (ValueError, IndexError) as e:
        print(f"ERROR: Ошибка парсинга в provider_details_handler: {e}")
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
    except Exception as e:
        print(f"ERROR: Ошибка в provider_details_handler: {e}")
        print(f"ERROR: Трейсбек:\n{traceback.format_exc()}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("back_to_providers:"))
async def back_to_providers_handler(callback: CallbackQuery, session: AsyncSession):
    """Возврат к списку поставщиков"""
    try:
        user_jk_id = int(callback.data.split(":")[1])
        print(f"DEBUG: Возврат к списку поставщиков для user_jk_id {user_jk_id}")
        
        # Получаем информацию о связи пользователя с ЖК
        user_jk_result = await orm_get_user_jk_with_jk_by_id(session, user_jk_id)
        if not user_jk_result:
            await callback.answer("❌ ЖК не найден", show_alert=True)
            return
        
        user_jk, jk = user_jk_result
        print(f"DEBUG: Найден ЖК для возврата: {jk.name}")
        
        # Получаем поставщиков для данного ЖК
        providers = await orm_get_service_providers_by_jk(session, jk.id)
        print(f"DEBUG: Найдено поставщиков для возврата: {len(providers)}")
        
        if not providers:
            message_text = (
                f"🏢 <b>Сервисные компании</b>\n\n"
                f"🏠 <b>ЖК:</b> {escape_html(jk.name)}\n\n"
                f"📭 В данном ЖК пока нет зарегистрированных сервисных компаний.\n\n"
                f"💡 <i>Сервисные компании смогут откликаться на ваши заявки после регистрации в системе.</i>"
            )
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🏠 Назад к ЖК",
                            callback_data=f"back_to_jk:{user_jk_id}"
                        )
                    ]
                ]
            )
        else:
            # Показываем первую страницу списка поставщиков
            page_size = 5
            total_pages = (len(providers) + page_size - 1) // page_size
            current_page = 0
            start_idx = current_page * page_size
            end_idx = start_idx + page_size
            page_providers = providers[start_idx:end_idx]
            
            message_text = (
                f"🏢 <b>Сервисные компании</b>\n\n"
                f"🏠 <b>ЖК:</b> {escape_html(jk.name)}\n"
                f"📊 <b>Всего компаний:</b> {len(providers)}\n\n"
                f"📋 <i>Выберите компанию для получения подробной информации:</i>"
            )
            
            if total_pages > 1:
                message_text += f"\n\n📄 Страница {current_page + 1} из {total_pages}"
            
            keyboard = create_service_providers_keyboard(
                page_providers, current_page, total_pages, user_jk_id
            )
        
        await safe_edit_message(
            callback,
            message_text,
            reply_markup=keyboard
        )
        await callback.answer()
        
    except (ValueError, IndexError) as e:
        print(f"ERROR: Ошибка парсинга в back_to_providers_handler: {e}")
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
    except Exception as e:
        print(f"ERROR: Ошибка в back_to_providers_handler: {e}")
        print(f"ERROR: Трейсбек:\n{traceback.format_exc()}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("back_to_jk_from_provider:"))
async def back_to_jk_from_provider_handler(callback: CallbackQuery, session: AsyncSession):
    """Возврат к информации о ЖК из просмотра поставщика"""
    try:
        user_jk_id = int(callback.data.split(":")[1])
        print(f"DEBUG: Возврат к ЖК для user_jk_id {user_jk_id}")
        
        # Получаем информацию о связи пользователя с ЖК
        user_jk_result = await orm_get_user_jk_with_jk_by_id(session, user_jk_id)
        if not user_jk_result:
            await callback.answer("❌ ЖК не найден", show_alert=True)
            return
        
        user_jk, jk = user_jk_result
        print(f"DEBUG: Возврат к ЖК: {jk.name}")
        
        # Формируем информацию о ЖК (как в оригинальном обработчике "Мой дом")
        from aiogram.utils.formatting import as_section
        from keyboards.inline_for_jk import unlink_keyboard
        
        # Формируем адрес
        address = f"{jk.street}, дом {jk.house}"
        if jk.block:
            address += f", {jk.block}"
        
        jk_info_text = as_section(
            f"{jk.name}\n",
            f"{jk.city}\n", 
            f"{address}\n\n",
            f"Ваша квартира: {user_jk.appartment}\n",
        ).as_html()
        
        # Возвращаем к исходному сообщению с ЖК
        await safe_edit_message(
            callback,
            jk_info_text,
            reply_markup=unlink_keyboard(user_jk.id)
        )
        await callback.answer()
        
    except (ValueError, IndexError) as e:
        print(f"ERROR: Ошибка парсинга в back_to_jk_from_provider_handler: {e}")
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
    except Exception as e:
        print(f"ERROR: Ошибка в back_to_jk_from_provider_handler: {e}")
        print(f"ERROR: Трейсбек:\n{traceback.format_exc()}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("contact_provider:"))
async def contact_provider_handler(callback: CallbackQuery, session: AsyncSession):
    """Обработчик связи с поставщиком"""
    try:
        provider_id = int(callback.data.split(":")[1])
        
        await callback.answer(
            f"📞 Функция связи с поставщиком (ID: {provider_id}) будет реализована в следующих обновлениях",
            show_alert=True
        )
        
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка обработки запроса")
    except Exception as e:
        print(f"Ошибка в contact_provider_handler: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("back_to_jk:"))
async def back_to_jk_handler(callback: CallbackQuery, session: AsyncSession):
    """Обработчик возврата к просмотру ЖК"""
    try:
        user_jk_id = int(callback.data.split(":")[1])
        print(f"DEBUG: back_to_jk для user_jk_id {user_jk_id}")
        
        # Получаем информацию о связи пользователя с ЖК
        user_jk_result = await orm_get_user_jk_with_jk_by_id(session, user_jk_id)
        if not user_jk_result:
            await callback.answer("❌ ЖК не найден", show_alert=True)
            return
        
        user_jk, jk = user_jk_result
        print(f"DEBUG: Возврат к ЖК: {jk.name}")
        
        # Формируем информацию о ЖК (как в оригинальном обработчике "Мой дом")
        from aiogram.utils.formatting import as_section
        from keyboards.inline_for_jk import unlink_keyboard
        
        # Формируем адрес
        address = f"{jk.street}, дом {jk.house}"
        if jk.block:
            address += f", {jk.block}"
        
        jk_info_text = as_section(
            f"{jk.name}\n",
            f"{jk.city}\n", 
            f"{address}\n\n",
            f"Ваша квартира: {user_jk.appartment}\n",
        ).as_html()
        
        # Возвращаем к исходному сообщению с ЖК
        await safe_edit_message(
            callback,
            jk_info_text,
            reply_markup=unlink_keyboard(user_jk.id)
        )
        await callback.answer()
        
    except (ValueError, IndexError) as e:
        print(f"ERROR: Ошибка парсинга в back_to_jk_handler: {e}")
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
    except Exception as e:
        print(f"ERROR: Ошибка в back_to_jk_handler: {e}")
        print(f"ERROR: Трейсбек:\n{traceback.format_exc()}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)
