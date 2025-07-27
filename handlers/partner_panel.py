# -*- coding: utf-8 -*-
# handlers/partner_panel.py
"""
Обработчики панели партнера.
"""

from datetime import datetime
from aiogram import F, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.model_partner_application import PartnerApplication
from database.models.orm_user import orm_get_user_by_id, orm_update_user_role
from database.enums.user_enums import ApplicationStatus, UserRole
from keyboards.reply import MAIN_KB, PARTNER_PANEL_KB

partner_router = Router()


async def is_approved_partner(session: AsyncSession, user_id: int) -> bool:
    """Проверяет, является ли пользователь одобренным партнером"""
    stmt = select(PartnerApplication).where(
        PartnerApplication.user_id == user_id,
        PartnerApplication.status == ApplicationStatus.APPROVED
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def get_partner_application(session: AsyncSession, user_id: int) -> PartnerApplication:
    """Получает одобренную заявку партнера"""
    stmt = select(PartnerApplication).where(
        PartnerApplication.user_id == user_id,
        PartnerApplication.status == ApplicationStatus.APPROVED
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def partner_access_required(func):
    """Декоратор для проверки доступа к партнерским функциям"""
    async def wrapper(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
        if not await is_approved_partner(session, message.from_user.id):
            await message.answer(
                "❌ У вас нет доступа к партнерской панели.\n"
                "Используйте команду /is_partner для подачи заявки.",
                reply_markup=MAIN_KB
            )
            return
        return await func(message, state, session, **kwargs)
    return wrapper


@partner_router.message(F.text == "ЖК под управлением")
@partner_access_required
async def jk_management_handler(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    """Обработчик кнопки 'ЖК под управлением'"""
    await message.answer(
        "🏗️ <b>ЖК под управлением</b>\n\n"
        "⚠️ Данный раздел находится в разработке.\n\n"
        "В этом разделе вы сможете:\n"
        "• Просматривать ЖК под вашим управлением\n"
        "• Управлять поставщиками услуг\n"
        "• Контролировать заявки резидентов\n"
        "• Настраивать параметры ЖК",
        parse_mode="HTML",
        reply_markup=PARTNER_PANEL_KB
    )


@partner_router.message(F.text == "Аналитика")
@partner_access_required
async def analytics_handler(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    """Обработчик кнопки 'Аналитика'"""
    await message.answer(
        "📊 <b>Аналитика</b>\n\n"
        "⚠️ Данный раздел находится в разработке.\n\n"
        "В этом разделе вы сможете просматривать:\n"
        "• Статистику заявок по ЖК\n"
        "• Активность резидентов\n"
        "• Эффективность поставщиков услуг\n"
        "• Финансовую отчетность\n"
        "• Графики и диаграммы",
        parse_mode="HTML",
        reply_markup=PARTNER_PANEL_KB
    )


@partner_router.message(F.text == "Кабинет партнера")
@partner_access_required
async def partner_cabinet_handler(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    """Обработчик кнопки 'Кабинет партнера'"""
    user_id = message.from_user.id
    application = await get_partner_application(session, user_id)
    
    if not application:
        await message.answer(
            "❌ Заявка партнера не найдена.",
            reply_markup=PARTNER_PANEL_KB
        )
        return
    
    # Формируем информационное сообщение
    info_text = (
        f"👤 <b>Кабинет партнера</b>\n\n"
        f"<b>Статус:</b> {application.status.get_russian_name()}\n"
        f"<b>ФИО:</b> {application.full_name}\n"
        f"<b>Компания:</b> {application.company}\n"
        f"<b>Телефон:</b> {application.phone}\n"
        f"<b>Цель партнерства:</b>\n{application.purpose}\n\n"
        f"<b>Дата подачи:</b> {application.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"<b>Последнее обновление:</b> {application.updated_at.strftime('%d.%m.%Y %H:%M')}"
    )
    
    # Создаем инлайн-клавиатуру
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать данные",
                    callback_data=f"edit_partner_data:{application.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑️ Удалить партнерство",
                    callback_data=f"delete_partner_data:{application.id}"
                )
            ]
        ]
    )
    
    await message.answer(
        info_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@partner_router.message(F.text == "Поддержка")
@partner_access_required
async def support_handler(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    """Обработчик кнопки 'Поддержка'"""
    await message.answer(
        "🆘 <b>Поддержка партнеров</b>\n\n"
        "Если у вас возникли вопросы или проблемы, обратитесь в службу поддержки:\n\n"
        "📞 <b>Контакты поддержки:</b>\n"
        "• Telegram: @lotboxsup\n\n"
        "⏰ <b>Время работы:</b>\n"
        "Понедельник - Пятница: 09:00 - 18:00\n"
        "Суббота - Воскресенье: 10:00 - 16:00\n\n"
        "💬 <b>Среднее время ответа:</b> 30 минут",
        parse_mode="HTML",
        reply_markup=PARTNER_PANEL_KB
    )


@partner_router.message(F.text == "Выйти из режима партнера")
@partner_access_required
async def exit_partner_mode_handler(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    """Обработчик кнопки 'Выйти из режима партнера'"""
    await message.answer(
        "👋 Вы вышли из режима партнера.\n\n"
        "Для возврата в партнерскую панель используйте команду /is_partner",
        reply_markup=MAIN_KB
    )


@partner_router.callback_query(F.data.startswith("edit_partner_data:"))
async def edit_partner_data_callback(callback, session: AsyncSession):
    """Обработчик запроса на редактирование данных партнера"""
    try:
        application_id = int(callback.data.split(":")[1])
        
        # Получаем заявку
        stmt = select(PartnerApplication).where(PartnerApplication.id == application_id)
        result = await session.execute(stmt)
        application = result.scalar_one_or_none()
        
        if not application:
            await callback.answer("❌ Заявка не найдена")
            return
            
        # Проверяем, что это заявка текущего пользователя
        if application.user_id != callback.from_user.id:
            await callback.answer("❌ У вас нет доступа к этой заявке")
            return
        
        # Устанавливаем статус запроса на редактирование
        application.status = ApplicationStatus.EDIT_REQUEST
        application.updated_at = datetime.utcnow()
        await session.commit()
        
        await callback.message.edit_text(
            "✏️ <b>Запрос на редактирование отправлен</b>\n\n"
            "Ваш запрос на редактирование данных партнера отправлен администрации.\n"
            "Ожидайте рассмотрения и дальнейших инструкций.\n\n"
            "📧 Вам будет отправлено уведомление о результате рассмотрения.",
            parse_mode="HTML",
            reply_markup=PARTNER_PANEL_KB
        )
        
        await callback.answer("✅ Запрос отправлен")
        
    except Exception as e:
        await callback.answer("❌ Произошла ошибка")
        print(f"Ошибка в edit_partner_data_callback: {e}")


@partner_router.callback_query(F.data.startswith("delete_partner_data:"))
async def delete_partner_data_callback(callback, session: AsyncSession):
    """Обработчик запроса на удаление партнерства"""
    try:
        application_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id
        
        # Получаем заявку
        stmt = select(PartnerApplication).where(PartnerApplication.id == application_id)
        result = await session.execute(stmt)
        application = result.scalar_one_or_none()
        
        if not application:
            await callback.answer("❌ Заявка не найдена")
            return
            
        # Проверяем, что это заявка текущего пользователя
        if application.user_id != user_id:
            await callback.answer("❌ У вас нет доступа к этой заявке")
            return
        
        # Удаляем заявку из базы данных
        await session.delete(application)
        
        # Изменяем роль пользователя на USER
        user = await orm_get_user_by_id(session, user_id)
        if user:
            await orm_update_user_role(session, user_id, UserRole.USER)
        
        await session.commit()
        
        # TODO: Здесь должно быть уведомление создателя о самостоятельном удалении партнерства
        
        await callback.message.edit_text(
            "🗑️ <b>Партнерство удалено</b>\n\n"
            "Ваше партнерство было успешно удалено.\n"
            "Роль изменена на \"Резидент\".\n\n"
            "Спасибо за сотрудничество! 🤝\n\n"
            "При необходимости вы можете подать новую заявку через команду /is_partner",
            parse_mode="HTML",
            reply_markup=MAIN_KB
        )
        
        await callback.answer("✅ Партнерство удалено")
        
    except Exception as e:
        await callback.answer("❌ Произошла ошибка")
        print(f"Ошибка в delete_partner_data_callback: {e}")
