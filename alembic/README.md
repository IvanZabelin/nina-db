# Alembic migrations

This directory contains Alembic configuration and migration revisions for the Nina database.

## Quick start

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a revision:

```bash
alembic revision -m "create initial tables"
```

Apply migrations:

```bash
alembic upgrade head
```
