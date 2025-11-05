#!/bin/bash
# Script to initialize the database with the complete schema
# This script is run automatically by docker-compose when the postgres container starts

set -e

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
  sleep 1
done

echo "PostgreSQL is ready. Initializing database schema..."

# Execute the schema file
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f /docker-entrypoint-initdb.d/db_schema.sql

echo "Database schema initialized successfully!"

