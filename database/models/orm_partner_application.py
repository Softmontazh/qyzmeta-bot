# database/models/orm_partner_application.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List
from database.models.model_partner_application import PartnerApplication
from database.models.model_user import User
from database.enums.user_enums import UserRole, ApplicationStatus


async def orm_create_partner_application(
    session: AsyncSession,
    user_id: int,
    requested_role: UserRole,
    full_name: str,
    company: str,
    purpose: str,
    phone: str
) -> PartnerApplication:
    """Создать новую заявку на роль"""
    application = PartnerApplication(
        user_id=user_id,
        requested_role=requested_role,
        full_name=full_name,
        company=company,
        purpose=purpose,
        phone=phone,
        status=ApplicationStatus.PENDING
    )
    session.add(application)
    await session.commit()
    await session.refresh(application)
    return application


async def orm_get_pending_applications(session: AsyncSession) -> List[PartnerApplication]:
    """Получить все заявки в ожидании"""
    query = select(PartnerApplication).where(
        PartnerApplication.status == ApplicationStatus.PENDING
    ).order_by(PartnerApplication.created_at.desc())
    
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_application_by_id(session: AsyncSession, application_id: int) -> Optional[PartnerApplication]:
    """Получить заявку по ID"""
    query = select(PartnerApplication).where(PartnerApplication.id == application_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def orm_approve_application(session: AsyncSession, application_id: int) -> bool:
    """Одобрить заявку и назначить роль пользователю"""
    # Получаем заявку
    application = await orm_get_application_by_id(session, application_id)
    if not application or application.status != ApplicationStatus.PENDING:
        return False
    
    # Обновляем статус заявки
    await session.execute(
        update(PartnerApplication)
        .where(PartnerApplication.id == application_id)
        .values(status=ApplicationStatus.APPROVED)
    )
    
    # Назначаем роль пользователю
    await session.execute(
        update(User)
        .where(User.user_id == application.user_id)
        .values(role=application.requested_role)
    )
    
    await session.commit()
    return True


async def orm_reject_application(session: AsyncSession, application_id: int, reason: str = None) -> bool:
    """Отклонить заявку"""
    application = await orm_get_application_by_id(session, application_id)
    if not application or application.status != ApplicationStatus.PENDING:
        return False
    
    values = {"status": ApplicationStatus.REJECTED}
    if reason:
        values["rejection_reason"] = reason
    
    await session.execute(
        update(PartnerApplication)
        .where(PartnerApplication.id == application_id)
        .values(**values)
    )
    
    await session.commit()
    return True


async def orm_get_user_applications(session: AsyncSession, user_id: int) -> List[PartnerApplication]:
    """Получить все заявки пользователя"""
    query = select(PartnerApplication).where(
        PartnerApplication.user_id == user_id
    ).order_by(PartnerApplication.created_at.desc())
    
    result = await session.execute(query)
    return result.scalars().all()


async def orm_has_pending_application(session: AsyncSession, user_id: int) -> bool:
    """Проверить, есть ли у пользователя заявка в ожидании"""
    query = select(PartnerApplication).where(
        PartnerApplication.user_id == user_id,
        PartnerApplication.status == ApplicationStatus.PENDING
    )
    
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None
