from datetime import UTC, datetime, timedelta

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models, schemas
from app.config import settings
from app.db import Base, get_db
from app.main import app


engine = create_engine(
    settings.TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Настраивает тестовую базу данных перед тестами и очищает после.

    Создаёт все таблицы перед запуском тестов и удаляет их после завершения.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    """Переопределяет зависимость get_db для использования тестовой базы данных.

    Возвращает:
        Session: Тестовая сессия базы данных.
    """
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="module")
async def client():
    """Предоставляет асинхронный HTTP-клиент для тестирования API.

    Возвращает:
        httpx.AsyncClient: Клиент для отправки запросов к приложению.
    """
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.fixture(scope="function")
def db_session():
    """Предоставляет сессию базы данных для каждого теста.

    Очищает таблицу руллонов перед тестом и откатывает изменения после.

    Возвращает:
        Session: Сессия базы данных для теста.
    """
    db = TestingSessionLocal()
    db.query(models.Coil).delete()
    db.commit()
    yield db
    db.rollback()
    db.close()


@pytest.fixture
def coil_create():
    """Фикстура для создания данных руллона.

    Возвращает:
        schemas.CoilCreate: Объект с данными для создания руллона.
    """
    return schemas.CoilCreate(length=10.0, weight=20.0)


@pytest.fixture
def coil(db_session):
    """Фикстура для создания активной руллона в базе данных.

    Аргументы:
        db_session (Session): Сессия базы данных.

    Возвращает:
        models.Coil: Активная руллон.
    """
    coil = models.Coil(
        length=10.0,
        weight=20.0,
        date_added=datetime.now(UTC) - timedelta(days=1),
        date_removed=None,
    )
    db_session.add(coil)
    db_session.commit()
    yield coil
    db_session.query(models.Coil).filter(models.Coil.id == coil.id).delete()
    db_session.commit()


@pytest.fixture
def removed_coil(db_session):
    """Фикстура для создания удалённого руллона в базе данных.

    Аргументы:
        db_session (Session): Сессия базы данных.

    Возвращает:
        models.Coil: Удалённый руллон.
    """
    coil = models.Coil(
        length=15.0,
        weight=25.0,
        date_added=datetime.now(UTC) - timedelta(days=2),
        date_removed=datetime.now(UTC) - timedelta(hours=1),
    )
    db_session.add(coil)
    db_session.commit()
    yield coil
    db_session.query(models.Coil).filter(models.Coil.id == coil.id).delete()
    db_session.commit()


@pytest.fixture
def date_range():
    """Фикстура для создания диапазона дат для тестирования.

    Возвращает:
        dict: Словарь с начальной и конечной датами.
    """
    now = datetime.now(UTC)
    start_date = now - timedelta(days=2)
    return {"start_date": start_date, "end_date": now}


@pytest.fixture
def coil_list(db_session, date_range):
    """Фикстура для создания списка руллонов в базе данных.

    Аргументы:
        db_session (Session): Сессия базы данных.
        date_range (dict): Диапазон дат для теста.

    Возвращает:
        List[models.Coil]: Список созданных руллонов.
    """
    start_date = date_range["start_date"]
    now = date_range["end_date"]
    coils = [
        models.Coil(
            length=10.0,
            weight=20.0,
            date_added=start_date + timedelta(days=1),
            date_removed=None,
        ),
        models.Coil(
            length=15.0,
            weight=25.0,
            date_added=start_date,
            date_removed=now - timedelta(hours=1),
        ),
    ]
    db_session.add_all(coils)
    db_session.commit()
    saved_coils = db_session.query(models.Coil).all()
    print(
        f"Сохранённые руллоны в фикстуре: {len(saved_coils)} руллонов: "
        f"{[{'id': c.id, 'date_added': c.date_added, 
             'date_removed': c.date_removed} for c in saved_coils]}"
    )
    yield coils
    for coil in coils:
        db_session.query(models.Coil).filter(models.Coil.id == coil.id).delete()
    db_session.commit()
