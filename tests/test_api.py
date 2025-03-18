from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import Coil


@pytest.fixture
async def client():
    """Предоставляет асинхронный клиент для тестирования API.

    Yields:
        AsyncClient: Клиент для отправки HTTP-запросов.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_coil(client: AsyncClient, db_session: Session):
    """Тестирует создание нового руллона через API.

    Аргументы:
        client (AsyncClient): Асинхронный клиент для запросов.
        db_session (Session): Сессия базы данных.
    """
    response = await client.post("/coils/", json={"length": 10.0, "weight": 20.0})
    assert response.status_code == 200
    data = response.json()
    assert data["length"] == 10.0
    assert data["weight"] == 20.0


@pytest.mark.asyncio
async def test_remove_coil(client: AsyncClient, db_session: Session):
    """Тестирует удаление руллона через API.

    Аргументы:
        client (AsyncClient): Асинхронный клиент для запросов.
        db_session (Session): Сессия базы данных.
    """
    coil = Coil(length=10.0, weight=20.0, date_added=datetime.now(UTC))
    db_session.add(coil)
    db_session.commit()
    response = await client.delete(f"/coils/{coil.id}")
    assert response.status_code == 200
    assert response.json()["date_removed"] is not None


@pytest.mark.asyncio
async def test_remove_coil_not_found(client: AsyncClient, db_session: Session):
    """Тестирует попытку удаления несуществующего руллона.

    Аргументы:
        client (AsyncClient): Асинхронный клиент для запросов.
        db_session (Session): Сессия базы данных.
    """
    response = await client.delete("/coils/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_coils_with_all_filters(client: AsyncClient, db_session: Session):
    """Тестирует получение руллонов с полным набором фильтров.

    Аргументы:
        client (AsyncClient): Асинхронный клиент для запросов.
        db_session (Session): Сессия базы данных.
    """
    now = datetime.now(UTC)
    yesterday = now - timedelta(days=1)
    coil = Coil(length=10.0, weight=20.0, date_added=yesterday, date_removed=now)
    db_session.add(coil)
    db_session.commit()
    response = await client.get(
        f"/coils/?id_min={coil.id}&id_max={coil.id}"
        f"&weight_min=19.0&weight_max=21.0"
        f"&length_min=9.0&length_max=11.0"
        f"&date_added_min={yesterday.isoformat()}&date_added_max={now.isoformat()}"
        f"&date_removed_min={yesterday.isoformat()}&date_removed_max={now.isoformat()}"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_statistics_empty_db(client: AsyncClient, db_session: Session):
    """Тестирует получение статистики при пустой базе данных.

    Аргументы:
        client (AsyncClient): Асинхронный клиент для запросов.
        db_session (Session): Сессия базы данных.
    """
    now = datetime.now(UTC)
    yesterday = now - timedelta(days=1)
    response = await client.get(
        f"/statistics/?start_date={yesterday.isoformat()}&end_date={now.isoformat()}"
    )
    assert response.status_code == 200
    stats = response.json()
    assert stats["added_count"] == 0
    assert stats["removed_count"] == 0
    assert stats["avg_length"] is None


@pytest.mark.asyncio
async def test_get_statistics_with_data(client: AsyncClient, db_session: Session):
    """Тестирует получение статистики с данными в базе.

    Аргументы:
        client (AsyncClient): Асинхронный клиент для запросов.
        db_session (Session): Сессия базы данных.
    """
    now = datetime.now(UTC)
    yesterday = now - timedelta(days=1)
    coil = Coil(length=10.0, weight=20.0, date_added=yesterday, date_removed=now)
    db_session.add(coil)
    db_session.commit()
    response = await client.get(
        f"/statistics/?start_date={yesterday.isoformat()}&end_date={now.isoformat()}"
    )
    assert response.status_code == 200
    stats = response.json()
    assert stats["added_count"] == 1
    assert stats["removed_count"] == 1
    assert stats["avg_length"] == 10.0


@pytest.mark.asyncio
async def test_get_statistics_invalid_date(client: AsyncClient):
    """Тестирует обработку неверного формата даты в запросе статистики.

    Аргументы:
        client (AsyncClient): Асинхронный клиент для запросов.
    """
    response = await client.get(
        "/statistics/?start_date=invalid&end_date=2023-01-02T00:00:00"
    )
    assert response.status_code == 422
