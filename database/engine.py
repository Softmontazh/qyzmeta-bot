import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models.model_base import Base
from database.models.model_jk import JK
from database.models.model_user_jk import UserJK

# from .env file:
# DB_URL=postgresql+asyncpg://login:password@localhost:5432/db_name

db_url = os.getenv("DB_URL")
if db_url is None:
    raise ValueError("Environment variable DB_URL is not set")
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
