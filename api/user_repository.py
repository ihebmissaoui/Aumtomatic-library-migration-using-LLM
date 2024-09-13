### START CODE ###

import os
from typing import Optional, Iterator, List

from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


@lru_cache(maxsize=None)
def get_engine(db_string: str):
    """
        Create and cache a SQLAlchemy engine.
        """
    return create_async_engine(db_string, pool_pre_ping=True)


class UserInDB(Base):
    """
      SQLAlchemy model representing a user in the database.
      """
    __tablename__ = 'user_table'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(length=128), unique=True, nullable=False)
    password = Column(String(length=128), nullable=False)
    name = Column(String(length=128), nullable=True)
    status = Column(String, nullable=True)
    country = Column(String(length=128), nullable=True)


class User(BaseModel):
    """
    Pydantic model for user data validation.
    """
    email: str
    name: str
    country: str
    status: str
    password: str


class UserFilter(BaseModel):
    """
      Pydantic model for filtering users by criteria.
      """
    limit: Optional[int] = None
    by_name: Optional[str] = None
    by_country: Optional[str] = None
    status: Optional[str] = None


class UserRepository:
    """
      Interface for user repository operations.
      """

    def __aenter__(self) -> 'UserRepository':
        """
             Enter context for the repository.
             """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_traceback) -> None:
        # ...

    async def save(self, user: User) -> None:
        """
              Save a user
              """
        # ...

    async def get_by_email(self, email: str) -> Optional[User]:
        """
             Retrieve a user by email .
             """
        # ...

    async def get(self, user_filter: UserFilter) -> List[User]:
        """
              Get a list of users based on filtering criteria.
              """
        # ...


class SQLUserRepository(UserRepository):
    """
     SQL implementation of the UserRepository interface.
     """

    def __init__(self, session: AsyncSession):
        """
              Initialize with a SQLAlchemy session.
              """
        self._session: AsyncSession = session

    async def __aexit__(self, exc_type, exc_val, exc_traceback):
        if exc_type is None and exc_val is None and exc_traceback is None:
            await self._session.commit()
        else:
            await self._session.rollback()
            raise

    async def get(self, user_filter: UserFilter) -> List[User]:
        """
             Retrieve users from the database based on filters.
             """
        # ...

    async def get_by_email(self, email: str):
        """
           Get a user by their email from the database.
           """
        # ...

    async def save(self, user: User):
        """
              Save a user to the database.
              """
        # ...


async def create_user_repository() -> Iterator[UserRepository]:
    """
     Factory function to create and yield a user repository.
     """
    async with sessionmaker(bind=await get_engine(os.getenv("DB_STRING")))() as session:
        user_repository = SQLUserRepository(session)
        yield user_repository


class InMemoryUserRepository(UserRepository):
    """
      In-memory implementation of the UserRepository interface(for unit tests).
      """

    def __init__(self):
        """
            Initialize the in-memory user repository.
            """
        self.data = {}

    async def save(self, user: User):
        """
               Save a user to the in-memory repository.
               """
        # ...

    async def get_by_email(self, email: str):
        """
                Retrieve a user by email from the in-memory repository.
                """
        # ...

    async def get(self, user_filter: UserFilter):
        """
               Retrieve users from the in-memory repository based on filters.
               """
        # ...

### END CODE ###