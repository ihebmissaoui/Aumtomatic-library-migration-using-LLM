import os
from functools import lru_cache
from typing import Optional, Iterator, List

from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

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

    def __enter__(self):
        """
             Enter context for the repository.
             """
        return self



    def save(self, user: User) -> None:
        """
              Save a user
              """
        raise NotImplementedError()

    def get_by_email(self, email: str) -> Optional[User]:
        """
             Retrieve a user by email .
             """
        raise NotImplementedError()

    def get(self, user_filter: UserFilter) -> List[User]:
        """
              Get a list of users based on filtering criteria.
              """
        raise NotImplementedError()


class SQLUserRepository(UserRepository):
    """
     SQL implementation of the UserRepository interface.
     """

    def __init__(self, session):
        """
              Initialize with a SQLAlchemy session.
              """
        self._session: Session = session

    def __exit__(self, exc_type, exc_val, exc_traceback: str) -> None:
        if any([exc_val, exc_type, exc_traceback]):
            self._session.rollback()
            return

    def get(self, user_filter: UserFilter) -> List[User]:
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
        users_in_db = query.all()
        return [
            User(email=user.email, name=user.name,
                 country=user.country, status=user.status, password=user.password)
            for user in users_in_db]

    def get_by_email(self, email: str) -> Optional[User]:
        """
           Get a user by their email from the database.
           """
        user = self._session.query(UserInDB).filter(UserInDB.email == email).first()
        if user is not None:
            print(f"returned object : {user.email}")

            return User(email=user.email, name=user.name, country=user.country, status=user.status,
                        password=user.password)
        return None

    def save(self, user: User) -> None:
        """
              Save a user to the database.
              """
        self._session.add(UserInDB(email=user.email, name=user.name,
                                   country=user.country, status=user.status,
                                   password=user.password))
        self._session.commit()


def create_user_repository() -> Iterator[UserRepository]:
    """
     Factory function to create and yield a user repository.
     """
    session = sessionmaker(bind=get_engine(os.getenv("DB_STRING")))()
    user_repository = SQLUserRepository(session)

    try:
        yield user_repository
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


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

    def save(self, user: User) -> None:
        """
               Save a user to the in-memory repository.
               """
        self.data[user.email] = user

    def get_by_email(self, email: str) -> Optional[User]:
        """
                Retrieve a user by email from the in-memory repository.
                """
        return self.data.get(email)

    def get(self, user_filter: UserFilter) -> List[User]:
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
