### START CODE ###
import asyncio
import os
from functools import lru_cache
from typing import AsyncIterator, Optional, List, Iterator

from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session
import sqlalchemy.ext.asyncio as asyncio_sa
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.decl_api import DeclSpec

SQL_BASE = declarative_base()


@lru_cache(maxsize=None)
def get_engine(db_string: str):
    """
        Create and cache a SQLAlchemy engine.
        """
    return create_engine(db_string, pool_pre_ping=True)


class UserInDB(SQL_BASE):
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

    @declared_attr
    def __sa_dataclass_metadata__(cls: DeclSpec[SQL_BASE]):
        return {
            "schema": "user",
            "table_name": cls.__tablename__
        }


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

    async def __aenter__(self):
        """
             Enter context for the repository.
             """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_traceback: str) -> None:
        """
            Exit context for the repository.
            """
        pass

    async def save(self, user: User) -> None:
        """
              Save a user
              """
        raise NotImplementedError()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
             Retrieve a user by email .
             """
        raise NotImplementedError()

    async def get(self, user_filter: UserFilter) -> List[User]:
        """
              Get a list of users based on filtering criteria.
              """
        raise NotImplementedError()


class SQLUserRepository(UserRepository):
    """
     SQL implementation of the UserRepository interface.
     """

    def __init__(self, async_session):
        """
              Initialize with a SQLAlchemy session.
              """
        self._session: Session = async_session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_traceback: str) -> None:
        if exc_val:
            print(f"{exc_type}, {exc_val}, {exc_traceback}")
            try:
                await self._session.rollback()
            except Exception as e:
                print(f"rollback failed: {e}")
            await self._session.close()
            return

        await self._session.commit()
        await self._session.close()

    async def save(self, user: User) -> None:
        """
              Save a user to the database.
              """
        db_user = UserInDB(email=user.email, name=user.name, country=user.country, status=user.status,
                             password=user.password)
        self._session.add(db_user)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
           Get a user by their email from the database.
           """
        user = await self._session.get(UserInDB, {"email": email})
        if user is not None:
            return User(email=user.email, name=user.name, country=user.country, status=user.status,
                        password=user.password)
        return None

    async def get(self, user_filter: UserFilter) -> List[User]:
        """
             Retrieve users from the database based on filters.
             """
        query = self._session.query(UserInDB)

        if user_filter.by_name is not None:
            query = query.filter(UserInDB.name == user_filter.by_name)
        if user_filter.by_country is not None:
            query = query.filter(UserInDB.country == user_filter.by_country)
        if user_filter.status is not None:
            query = query.filter(UserInDB.status == user_filter.status)
        if user_filter.limit is not None:
            query = query.limit(user_filter.limit)
        # Execute the query and retrieve results
        users_in_db = await query.all()
        return [
            User(email=user.email, name=user.name,
                 country=user.country, status=user.status, password=user.password)
            for user in users_in_db]


async def create_user_repository() -> AsyncIterator[UserRepository]:
    """
     Factory function to create and yield a user repository.
     """
    async_session = sessionmaker(
        bind=get_engine(os.getenv("DB_STRING")),
        class_=asyncio_sa.AsyncSession,
        expire_on_commit=False
    )
    session = async_session()
    user_repository = SQLUserRepository(session)

    try:
        yield user_repository
    except Exception:
        try:
            await session.rollback()
        except Exception:
            pass
        raise
    finally:
        await session.close()


class InMemoryUserRepository:
    """
      In-memory implementation of the UserRepository interface(for unit tests).
      """

    # In-memory implementation of interface
    def __init__(self):
        """
            Initialize the in-memory user repository.
            """
        self.data = {}

    async def save(self, user: User) -> None:
        """
               Save a user to the in-memory repository.
               """
        self.data[user.email] = user

    async def get_by_email(self, email: str) -> Optional[User]:
        """
                Retrieve a user by email from the in-memory repository.
                """
        return self.data.get(email)

    async def get(self, user_filter: UserFilter) -> List[User]:
        """
               Retrieve users from the in-memory repository based on filters.
               """
        all_matching_users = filter(
            lambda user: (not user_filter.status or user_filter.status == user.status)
                         and (not user_filter.by_name or user_filter.by_name == user.name)
                         and (not user_filter.by_country or user_filter.by_country == user.country),

            self.data.values(),
        )

        return list(all_matching_users)[: user_filter.limit]
### END CODE ###