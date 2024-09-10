import os
import time

import alembic.config
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from main import app
from user_repository import (
    SQL_BASE,
    SQLUserRepository,
    User,
    UserFilter,
    get_engine,
)
from user_repository import InMemoryUserRepository


@pytest.fixture
def fake_user_repository():
    return InMemoryUserRepository()


@pytest.fixture
def user_repository():
    time.sleep(1)
    alembicArgs = ["--raiseerr", "upgrade", "head"]
    alembic.config.main(argv=alembicArgs)

    engine = get_engine(os.getenv("DB_STRING"))
    session = sessionmaker(bind=engine)()

    yield SQLUserRepository(session)

    session.close()

    sessionmaker(bind=engine, autocommit=True)().execute(
        ";".join([f"TRUNCATE TABLE {t} CASCADE" for t in SQL_BASE.metadata.tables.keys()])
    )


# Unit Tests

@pytest.mark.unit
def test_save_and_retrieve_user(fake_user_repository):
    email = "unit2@test.com"
    user = User(email=email, name="Unit User 2", country="Country", status="Student", password="password")
    fake_user_repository.save(user)
    retrieved_user = fake_user_repository.get_by_email(email)
    assert retrieved_user is not None
    assert retrieved_user.email == email


@pytest.mark.unit
def test_get_user_by_non_existent_email(fake_user_repository):
    retrieved_user = fake_user_repository.get_by_email("nonexistent@test.com")
    assert retrieved_user is None


@pytest.mark.unit
def test_filter_users_by_status(fake_user_repository):
    user1 = User(email="unitfilter3@test.com", name="Unit Filter User 3", country="Country1", status="Student",
                 password="password3")
    user2 = User(email="unitfilter4@test.com", name="Unit Filter User 4", country="Country2", status="Worker",
                 password="password4")
    fake_user_repository.save(user1)
    fake_user_repository.save(user2)
    filter_criteria = UserFilter(status="Student")
    users = fake_user_repository.get(filter_criteria)
    assert len(users) == 1
    assert users[0].email == "unitfilter3@test.com"


@pytest.mark.unit
def test_filter_users_by_country(fake_user_repository):
    user1 = User(email="unitfilter1@test.com", name="Unit Filter User 1", country="Country1", status="Student",
                 password="password1")
    user2 = User(email="unitfilter2@test.com", name="Unit Filter User 2", country="Country2", status="Worker",
                 password="password2")
    fake_user_repository.save(user1)
    fake_user_repository.save(user2)
    filter_criteria = UserFilter(by_country="Country1")
    users = fake_user_repository.get(filter_criteria)
    assert len(users) == 1
    assert users[0].email == "unitfilter1@test.com"


@pytest.mark.unit
def test_filter_users_by_name(fake_user_repository):
    user1 = User(email="unitname1@test.com", name="Alice", country="Country1", status="Student", password="password1")
    user2 = User(email="unitname2@test.com", name="Bob", country="Country2", status="Worker", password="password2")
    fake_user_repository.save(user1)
    fake_user_repository.save(user2)
    filter_criteria = UserFilter(by_name="Alice")
    users = fake_user_repository.get(filter_criteria)
    assert len(users) == 1
    assert users[0].email == "unitname1@test.com"


@pytest.mark.unit
def test_filter_users_with_limit(fake_user_repository):
    user1 = User(email="unitlimit1@test.com", name="User Limit 1", country="Country1", status="Student",
                 password="password1")
    user2 = User(email="unitlimit2@test.com", name="User Limit 2", country="Country2", status="Worker",
                 password="password2")
    user3 = User(email="unitlimit3@test.com", name="User Limit 3", country="Country3", status="Student",
                 password="password3")
    fake_user_repository.save(user1)
    fake_user_repository.save(user2)
    fake_user_repository.save(user3)
    filter_criteria = UserFilter(by_status="Student", limit=2)
    users = fake_user_repository.get(filter_criteria)
    assert len(users) == 2
    assert users[0].email == "unitlimit1@test.com"
    assert users[1].email == "unitlimit2@test.com"


# Integration Tests
@pytest.mark.integration
def test_create_and_retrieve_user( user_repository):
    user = User(email="integration1@test.com", name="Integration User 1", country="Country1", status="Student",
                password="password123")
    with user_repository as repo:
        repo.save(user)
    client = TestClient(app)
    response = client.get("/user/integration1@test.com")
    assert response.status_code == 200
    assert response.json()["email"] == "integration1@test.com"
    assert response.json()["name"] == "Integration User 1"


@pytest.mark.integration
def test_filter_users(user_repository):
    user1 = User(email="filter1@test.com", name="Filter User 1", country="Country1", status="Student", password="password1")
    user2 = User(email="filter2@test.com", name="Filter User 2", country="Country2", status="Worker", password="password2")
    with user_repository as repo:
        repo.save(user1)
        repo.save(user2)
    client = TestClient(app)

    # Define filter query parameters
    filter_params = {
        "by_country": "Country1"
    }

    response = client.get("/find", params=filter_params)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["email"] == "filter1@test.com"


@pytest.mark.integration
def test_create_user_duplicate_email(user_repository):
    user = User(email="duplicate@test.com", name="Duplicate User", country="Country", status="Student", password="password")
    with user_repository as repo:
        repo.save(user)
        with pytest.raises(IntegrityError):
            repo.save(User(email="duplicate@test.com", name="Another User", country="Country", status="Student",
                           password="password"))
