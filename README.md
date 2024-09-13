# Docker Compose Setup

This project uses Docker Compose to manage a multi-service setup for a FastAPI application with PostgreSQL migration to SQLAlchemy from version 1.4 to version 2 It use  Alembic for mgiration of schemas , and various testing tools.

## Services

- **api**: The FastAPI application.
  - **Ports**: `127.0.0.1:5000:5000`
  - **Environment Variables**:
    - `DB_STRING`: PostgreSQL connection string.
  - **Dependencies**: Depends on `db` and `migrate` services.

- **migrate**: Handles database migrations using Alembic.
  - **Command**: Runs Alembic to generate and apply migrations.
  - **Dependencies**: Depends on the `db` service.

- **db**: PostgreSQL database.
  - **Image**: `postgres:14.5`
  - **Ports**: `127.0.0.1:5432:5432`
  - **Environment Variables**:
    - `POSTGRES_USER`: Database user.
    - `POSTGRES_PASSWORD`: Database password.
    - `POSTGRES_DB`: Database name.
  - **Volume**: `postgres-data:/var/lib/postgresql/data`

- **pgadmin**: pgAdmin 4 for managing PostgreSQL databases.
  - **Image**: `dpage/pgadmin4`
  - **Ports**: `127.0.0.1:8080:80`
  - **Environment Variables**:
    - `PGADMIN_DEFAULT_EMAIL`: Admin email.
    - `PGADMIN_DEFAULT_PASSWORD`: Admin password.
  - **Dependencies**: Depends on `db` service.

- **pytest**: Runs tests using pytest.
  - **Command**: Executes `pytest` command.
  - **Dependencies**: Depends on `db` and `migrate` services.

- **pylint**: Runs pylint for code analysis.
  - **Command**: Executes `pylint user_repository.py`.
  - **Dependencies**: Depends on `pytest` service.

- **pyright**: Runs Pyright for type checking.
  - **Command**: Executes `pyright user_repository.py`.
  - **Dependencies**: Depends on `pylint` service.

## Volumes

- **postgres-data**: Persistent storage for PostgreSQL data.

## Usage

1. **Build and start services**:
   ```sh
   docker-compose up --build

It will build the FastAPI project, run migrations to update the schema, and then execute tests in separate services.

The migration process needs to be run in the LLM_migration_SQLAlchemy_using_gemini.ipynb notebook. Import the user_repository.py file from the sample_data folder. After running the code, a new migration file will be generated based on the approach (zero-shot migration, one-shot migration, etc.). Paste this new file into the root of the project to replace the previous version.