import os
import random
import string
import sys
import time
from pathlib import Path

import pymysql
import pytest
from pymysql.cursors import DictCursor


sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.db import DbClient


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("mariadb")
    group.addoption("--db-host", default=os.getenv("DB_HOST", "127.0.0.1"))
    group.addoption("--db-port", type=int, default=int(os.getenv("DB_PORT", 3306)))
    group.addoption("--db-database", default=os.getenv("DB_NAME", "db"))
    group.addoption("--db-user", default=os.getenv("DB_USER", "root"))
    group.addoption("--db-password", default=os.getenv("DB_PASSWORD", ""))


@pytest.fixture(scope="session")
def connection(pytestconfig):
    host = pytestconfig.getoption("--db-host")
    port = pytestconfig.getoption("--db-port")
    db = pytestconfig.getoption("--db-database")
    user = pytestconfig.getoption("--db-user")
    password = pytestconfig.getoption("--db-password")
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db,
        cursorclass=DictCursor,
        autocommit=True,
        charset="utf8mb4",
    )
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture(scope="session")
def db_client(connection):
    yield DbClient(connection)


def random_str(n=6):
    return "".join(random.choices(string.ascii_lowercase, k=n))


@pytest.fixture(name="customer_payload")
def customer_payload():
    ts = int(time.time())
    return {
        "firstname": f"John{random_str(3)}",
        "lastname": f"Doe{random_str(3)}",
        "email": f"john{ts}{random_str(3)}@example.test",
        "telephone": f"+1{random.randint(100000000, 999999999)}",
        "password": "test_password",
        "status": 1,
        "customer_group_id": 1,
        "store_id": 0,
        "language_id": 1,
    }


@pytest.fixture
def created_customer_id(db_client, customer_payload):
    cust_id = db_client.create_customer(customer_payload)
    yield cust_id
    try:
        db_client.delete_customer_by_id(cust_id)
    except Exception:
        pass


@pytest.fixture(name="update_payload")
def update_payload():
    return {
        "firstname": "Test",
        "lastname": "Testiovich",
        "email": f"test{random_str(4)}@example.test",
        "telephone": "+123456789",
    }
