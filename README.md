# nina-db

Database schema and migrations for **Nina**.

This repository contains the database migration layer for the Nina project. It is intended to manage schema evolution in a predictable and versioned way, independent from the main application repository.

## Goals

- keep database schema changes under version control;
- manage migrations in a separate repository;
- provide a clean place for Alembic configuration and revision history;
- make database setup reproducible across environments.

## Planned contents

- Alembic configuration;
- migration revisions;
- schema bootstrap instructions;
- environment configuration examples;
- database-related documentation.

## Relationship to the main project

Main application repository:
- `nina` — application code and service logic

Database repository:
- `nina-db` — schema management and migrations

## Status

Initial repository setup.
