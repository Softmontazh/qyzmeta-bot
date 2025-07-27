import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models.model_base import Base
# Импортируем все модели для правильного создания таблиц
from database.models.model_jk import JK
from database.models.model_user_jk import UserJK
from database.models.model_user import User
from database.models.model_offer import Offer
from database.models.model_lot import Lot
from database.models.model_lot_limit import LotLimit
from database.models.model_jk_service_provider import JKServiceProvider
from database.models.model_partner_application import PartnerApplication
from database.models.model_user_subscription import UserSubscription
from database.models.model_subscription_price import SubscriptionPrice

# from .env file:
# DATABASE_URL=postgresql+asyncpg://login:password@localhost:5432/db_name

db_url = os.getenv("DATABASE_URL")
if db_url is None:
    raise ValueError("Environment variable DATABASE_URL is not set")

engine = create_async_engine(db_url, echo=True)

session_maker = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

from typing import AsyncGenerator


async def get_sessionmaker() -> AsyncGenerator[AsyncSession, None]:
    async with session_maker() as session:
        yield session


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
