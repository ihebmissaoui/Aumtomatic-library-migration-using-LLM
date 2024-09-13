### START CODE ###
import os
from functools import lru_cache
from typing import Iterator, Optional, List
from sqlalchemy import MetaData, Table, Column, Text, Integer

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

metadata = MetaData()

user_table = Table(
    "user_table",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(255), unique=True),
    Column("password", String(255)),
    Column("name", String(255)),
    Column("status", String(255)),
    Column("country", String(255)),
)


class User(BaseModel):
    email: str
    name: str
    country: str
    status: str
    password: str


class UserFilter(BaseModel):
    limit: Optional[int] = None
    by_name: Optional[str] = None
    by_country: Optional[str] = None
    status: Optional[str] = None


class UserRepository:

    async def __aenter__(self):
        engine = create_async_engine(os.getenv("DB_STRING"))
        async with engine.begin() as conn:
            await conn.run_sync(metadata.create_all)
        self.session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)()
        return self

    async def __aexit__(self, type, value, traceback):
        await self.session.close()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(user_table).where(user_table.c.email == email)
        )
        return result.scalar()

    async def get(self, user_filter: UserFilter) -> List[User]:
        query = select(user_table)
        if user_filter.by_name is not None:
            query = query.where(user_table.c.name == user_filter.by_name)
        if user_filter.by_country is not None:
            query = query.where(user_table.c.country == user_filter.by_country)
        if user_filter.status is not None:
            query = query.where(user_table.c.status == user_filter.status)
        if user_filter.limit is not None:
            query = query.limit(user_filter.limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def save(self, user: User):
        query = user_table.insert().values(
            email=user.email,
            password=user.password,
            name=user.name,
            status=user.status,
            country=user.country,
        )

        await self.session.execute(query)
### END CODE ###