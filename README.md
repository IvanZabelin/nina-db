# nina-db

Database schema and migrations for **Nina**.

This repository contains the database migration layer for the Nina project. It is intended to manage schema evolution in a predictable and versioned way, independent from the main application repository.

## Goals

- keep database schema changes under version control;
- manage migrations in a separate repository;
- provide a clean place for Alembic configuration and revision history;
- make database setup reproducible across environments.

## Stack

- PostgreSQL 16
- Alembic
- SQLAlchemy 2.x
- psycopg 3 for migrations

## Relationship to the main project

Main application repository:
- `nina` — application code and service logic

Database repository:
- `nina-db` — schema management and migrations

## Local development

### 1. Start PostgreSQL with Docker Compose

```bash
docker compose up -d
```

Check status:

```bash
docker compose ps
```

### 2. Create local environment file

```bash
cp .env.example .env
```

Default value:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/nina
```

### 3. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Run migrations

```bash
alembic upgrade head
```

## Notes

- This repository currently uses a synchronous PostgreSQL driver for Alembic migrations.
- The main `nina` service can still use an async engine separately (`asyncpg`) without any conflict.

## Status

Initial schema is created and ready to be applied to a local PostgreSQL instance.
