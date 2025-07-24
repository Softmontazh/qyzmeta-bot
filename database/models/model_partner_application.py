# database/models/model_partner_application.py

from datetime import datetime
from sqlalchemy import BigInteger, String, Text, DateTime, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column
from database.models.model_base import Base
from database.enums.user_enums import UserRole


class PartnerApplication(Base):
    """Модель заявки на получение роли партнера"""
    
    __tablename__ = "partner_applications"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    requested_role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PartnerApplication(id={self.id}, user_id={self.user_id}, role={self.requested_role}, status={self.status})>"