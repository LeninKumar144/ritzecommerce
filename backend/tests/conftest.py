"""Pytest setup. Tests use product_shopping_test, never the development database."""

import os

os.environ["DB_NAME"] = "product_shopping_test"
os.environ["JWT_SECRET"] = "test-only-secret-with-sufficient-length"

import pymysql
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import engine


def _ensure_test_database() -> None:
    settings = get_settings()
    connection = pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_username,
        password=settings.db_password,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "CREATE DATABASE IF NOT EXISTS product_shopping_test "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
            )
        connection.commit()
    finally:
        connection.close()


@pytest.fixture(scope="session", autouse=True)
def migrated_test_database() -> None:
    _ensure_test_database()
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def db_session() -> Session:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()
