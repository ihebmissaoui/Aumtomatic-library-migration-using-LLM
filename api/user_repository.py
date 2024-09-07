import os
from functools import lru_cache
from typing import Optional, Iterator, List

from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

SQL_BASE = declarative_base()


@lru_cache(maxsize=None)
def get_engine(db_string: str):
    return create_engine(db_string, pool_pre_ping=True)


class UserInDB(SQL_BASE):
    __tablename__ = 'user'


    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(length=128), unique=True, nullable=False)
    password = Column(String(length=128), nullable=False)
    name = Column(String(length=128),nullable=True)
    student = Column(Boolean,nullable=True)
    country = Column(String(length=128), nullable=True)


class User(BaseModel):
    email: str
    name: str
    country: str
    student: bool
    password: str


class UserFilter(BaseModel):
    limit: Optional[int] = None
    by_name: Optional[str] = None
    by_country: Optional[str] = None
    status: Optional[str] = None


class UserRepository:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    def save(self, user: User) -> None:
        raise NotImplementedError()

    def get_by_email(self, email: str) -> Optional[User]:
        raise NotImplementedError()

    def get(self, user_filter: UserFilter) -> List[User]:
        raise NotImplementedError()


class SQLUserRepository(UserRepository):
    def __init__(self, session):
        self._session: Session = session


    def __exit__(self, exc_type, exc_val, exc_traceback: str) -> None:
        if any([exc_val, exc_type, exc_traceback]):
            self._session.rollback()
            return

    def get(self, user_filter: UserFilter) -> List[User]:
        query = self._session.query(UserInDB)

        if user_filter.by_name is not None:
            query = query.filter(UserInDB == user_filter.by_name)
        if user_filter.by_country is not None:
            query = query.filter(UserInDB.country == user_filter.by_country)
        if user_filter.status is not None:
            query = query.filter(UserInDB.status == user_filter.status)
        if user_filter.limit is not None:
            query = query.limit(user_filter.limit)
        return [
            User(email=user.email, name=user.name, country=user.country, student=user.student, passwword=user.password)
            for user in query]

    def get_by_email(self, email: str) -> Optional[User]:
        user = self._session.query(UserInDB).filter(UserInDB.email == email).first()

        if user is not None:
            return User(email=user.email, name=user.name, country=user.country, student=user.student,
                        passwword=user.password)
        return None

    def save(self,user:User) -> None:
        self._session.add(UserInDB(email=user.email, name=user.name, country=user.country, student=user.student,password=user.password))
def create_user_repository() -> Iterator[UserRepository]:
    session = sessionmaker(bind=get_engine(os.getenv("DB_STRING")))()
    user_repository = SQLUserRepository(session)

    try:
        yield user_repository
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
