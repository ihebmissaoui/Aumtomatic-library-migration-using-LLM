import os
from functools import lru_cache
from typing import Optional, List, AsyncGenerator, Any

from pydantic import BaseModel
from sqlalchemy import Integer, String, NullPool, select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

SQL_BASE = declarative_base()


@lru_cache(maxsize=None)
def get_engine(db_string: str):
    """
    Create and cache a SQLAlchemy engine.

    Args:
        db_string (str): The database connection string.

    Returns:
        Engine: The SQLAlchemy async engine.
    """
    return create_async_engine(db_string, pool_pre_ping=True, poolclass=NullPool)


class UserInDB(SQL_BASE):
    """
    SQLAlchemy model representing a user in the database.
    """
    __tablename__ = 'user_table'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(length=128), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(length=128), nullable=False)
    name: Mapped[str] = mapped_column(String(length=128), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=True)
    country: Mapped[str] = mapped_column(String(length=128), nullable=True)


class User(BaseModel):
    """
    Pydantic model for user data validation.

    Attributes:
        email (str): User email.
        name (str): User name.
        country (str): User country.
        status (str): User status.
        password (str): User password.
    """
    email: str
    name: str
    country: str
    status: str
    password: str


class UserFilter(BaseModel):
    """
    Pydantic model for filtering users by criteria.

    Attributes:
        limit (Optional[int]): Maximum number of users to return.
        by_name (Optional[str]): Filter users by name.
        by_country (Optional[str]): Filter users by country.
        status (Optional[str]): Filter users by status.
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

        Returns:
            UserRepository: The repository instance.
        """
        return self



    async def save(self, user: User) -> None:
        """
        Save a user.

        Args:
            user (User): The user to save.
        """
        raise NotImplementedError()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email.

        Args:
            email (str): The email of the user to retrieve.

        Returns:
            Optional[User]: The user with the given email, or None if not found.
        """
        raise NotImplementedError()

    async def get(self, user_filter: UserFilter) -> List[User]:
        """
        Get a list of users based on filtering criteria.

        Args:
            user_filter (UserFilter): The filter criteria.

        Returns:
            List[User]: List of users matching the filter criteria.
        """
        raise NotImplementedError()


class SQLUserRepository(UserRepository):
    """
    SQL implementation of the UserRepository interface.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize with a SQLAlchemy session.

        Args:
            session (AsyncSession): The SQLAlchemy async session.
        """
        self._session: AsyncSession = session

    async def __aexit__(self, exc_type, exc_value, exc_traceback: str) -> None:
        """
        Exit context for the repository, handle transactions.

        Args:
            exc_type (Optional[Type[BaseException]]): Exception type.
            exc_value (Optional[BaseException]): Exception value.
            exc_traceback (Optional[TracebackType]): Exception traceback.
        """
        if any([exc_value, exc_type, exc_traceback]):
            await self._session.rollback()
            return
        try:
            await self._session.commit()
        except DatabaseError as error:
            await self._session.rollback()
            raise error

    async def get(self, user_filter: UserFilter) -> List[User]:
        """
        Get a list of users based on filtering criteria.

        Args:
            user_filter (UserFilter): The filter criteria.

        Returns:
            List[User]: List of users matching the filter criteria.
        """
        statement = select(UserInDB)

        if user_filter.by_name is not None:
            statement = statement.where(UserInDB.name == user_filter.by_name)
        if user_filter.by_country is not None:
            statement = statement.where(UserInDB.country == user_filter.by_country)
        if user_filter.status is not None:
            statement = statement.where(UserInDB.status == user_filter.status)
        if user_filter.limit is not None:
            statement = statement.limit(user_filter.limit)
        users_in_db = await self._session.execute(statement)
        return [
            User(email=user.email, name=user.name,
                 country=user.country, status=user.status, password=user.password)
            for user in users_in_db.scalars()]

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email.

        Args:
            email (str): The email of the user to retrieve.

        Returns:
            Optional[User]: The user with the given email, or None if not found.
        """
        result = await self._session.execute(select(UserInDB).where(UserInDB.email == email))
        user = result.scalars().first()
        if user:
            return User(email=user.email, name=user.name,
                        country=user.country, status=user.status,
                        password=user.password)
        return None

    async def save(self, user: User) -> None:
        """
        Save a user.

        Args:
            user (User): The user to save.
        """
        self._session.add(UserInDB(email=user.email, name=user.name,
                                   country=user.country, status=user.status,
                                   password=user.password))

        await self._session.commit()


async def create_user_repository() -> AsyncGenerator[SQLUserRepository, Any]:
    """
    Create a SQLUserRepository instance within an async context.

    Returns:
        AsyncGenerator[SQLUserRepository, Any]:
        An asynchronous generator yielding a SQLUserRepository.
    """
    async with AsyncSession(get_engine(os.getenv("DB_STRING"))) as session:
        try:
            user_repository = SQLUserRepository(session)

            yield user_repository
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class InMemoryUserRepository:
    """
    In-memory implementation of the UserRepository interface (for unit tests).
    """

    async def __aenter__(self):
        """
        Enter context for the in-memory repository.

        Returns:
            InMemoryUserRepository: The repository instance.
        """
        return self



    def __init__(self):
        """
        Initialize the in-memory user repository.
        """
        self.data = {}

    async def save(self, user: User) -> None:
        """
        Save a user to the in-memory repository.

        Args:
            user (User): The user to save.
        """
        self.data[user.email] = user

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email from the in-memory repository.

        Args:
            email (str): The email of the user to retrieve.

        Returns:
            Optional[User]: The user with the given email, or None if not found.
        """
        return self.data.get(email)

    async def get(self, user_filter: UserFilter) -> List[User]:
        """
        Retrieve users from the in-memory repository based on filters.

        Args:
            user_filter (UserFilter): The filter criteria.

        Returns:
            List[User]: List of users matching the filter criteria.
        """
        all_matching_users = filter(
            lambda user: (not user_filter.status or user_filter.status == user.status)
                         and (not user_filter.by_name or user_filter.by_name == user.name)
                         and (not user_filter.by_country or user_filter.by_country == user.country),

            self.data.values(),
        )

        return list(all_matching_users)[: user_filter.limit]
