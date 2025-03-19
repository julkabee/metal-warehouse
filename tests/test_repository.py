from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app import models, schemas
from app.repository import InMemoryCoilRepository, CoilRepository


@pytest.fixture
def mock_db_session():
    """Предоставляет мок-объект сессии базы данных для тестирования.

    Возвращает:
        Mock: Мок-объект с интерфейсом sqlalchemy.orm.Session.
    """
    return Mock(spec=Session)


@pytest.fixture
def coil_create():
    """Предоставляет фикстуру с данными для создания руллона.

    Возвращает:
        schemas.CoilCreate: Объект с тестовыми данными длины и веса руллона.
    """
    return schemas.CoilCreate(length=10.0, weight=20.0)


@pytest.fixture
def coil():
    """Предоставляет фикстуру с объектом руллона для тестирования.

    Возвращает:
        models.Coil: Тестовый объект руллона с заданными параметрами.
    """
    return models.Coil(
        id=1,
        length=10.0,
        weight=20.0,
        date_added=datetime.now(UTC) - timedelta(days=1),
        date_removed=None,
    )

def test_sqlalchemy_create_coil(mock_db_session, coil_create):
    """Тестирует создание руллона в репозитории CoilRepository.

    Аргументы:
        mock_db_session (Mock): Мок-объект сессии базы данных.
        coil_create (schemas.CoilCreate): Данные для создания руллона.
    """
    repo = CoilRepository(mock_db_session)
    mock_coil = models.Coil(
        id=1, length=coil_create.length, weight=coil_create.weight, date_added=datetime.now(UTC)
    )

    # Мокируем поведение базы данных
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = None
    mock_db_session.refresh.side_effect = lambda x: setattr(x, "id", 1)

    # Устанавливаем, что add добавляет mock_coil
    def mock_add(coil):
        coil.id = 1 
        return None

    mock_db_session.add.side_effect = mock_add
    result = repo.create_coil(coil_create)

    # Проверяем, что результат соответствует mock_coil
    assert result.length == mock_coil.length
    assert result.weight == mock_coil.weight
    assert result.id == mock_coil.id
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once()


def test_sqlalchemy_remove_coil(mock_db_session, coil):
    """Тестирует удаление существующего руллона в репозитории SQLAlchemyCoilRepository.

    Аргументы:
        mock_db_session (Mock): Мок-объект сессии базы данных.
        coil (models.Coil): Тестовый объект руллона.
    """
    repo = CoilRepository(mock_db_session)
    mock_db_session.query.return_value.filter.return_value.first.return_value = coil

    result = repo.remove_coil(coil.id)

    assert result == coil
    assert result.date_removed is not None
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(coil)


def test_sqlalchemy_remove_coil_not_found(mock_db_session):
    """Тестирует попытку удаления несуществующего руллона в CoilRepository.

    Аргументы:
        mock_db_session (Mock): Мок-объект сессии базы данных.
    """
    repo = CoilRepository(mock_db_session)
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    result = repo.remove_coil(999)

    assert result is None
    mock_db_session.commit.assert_not_called()


def test_sqlalchemy_get_coils_empty(mock_db_session):
    """Тестирует получение пустого списка руллонов в SQLAlchemyCoilRepository.

    Аргументы:
        mock_db_session (Mock): Мок-объект сессии базы данных.
    """
    repo = CoilRepository(mock_db_session)
    mock_db_session.query.return_value.all.return_value = []

    result = repo.get_coils()

    assert result == []
    mock_db_session.query.assert_called_once_with(models.Coil)


def test_sqlalchemy_get_statistics_empty(mock_db_session):
    """Тестирует получение статистики при пустой базе в SQLAlchemyCoilRepository.

    Аргументы:
        mock_db_session (Mock): Мок-объект сессии базы данных.
    """
    repo = CoilRepository(mock_db_session)
    start_date = datetime.now(UTC) - timedelta(days=1)
    end_date = datetime.now(UTC)

    mock_db_session.query.return_value.filter.return_value.scalar.return_value = 0
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    mock_db_session.query.return_value.filter.return_value.count.return_value = (
        0
    )
    mock_db_session.query.return_value.filter.return_value.scalar.return_value = (
        0.0
    )

    stats = repo.get_statistics(start_date, end_date)

    assert stats.added_count == 0
    assert stats.removed_count == 0
    assert stats.avg_length is None


# Тесты для InMemoryCoilRepository
def test_inmemory_create_coil(coil_create):
    """Тестирует создание руллона в репозитории InMemoryCoilRepository.

    Аргументы:
        coil_create (schemas.CoilCreate): Данные для создания руллона.
    """
    repo = InMemoryCoilRepository()
    result = repo.create_coil(coil_create)

    assert result.id == 1
    assert result.length == coil_create.length
    assert result.weight == coil_create.weight
    assert result.date_added is not None
    assert result.date_removed is None
    assert len(repo.coils) == 1


def test_inmemory_remove_coil():
    """Тестирует удаление существующего руллона в InMemoryCoilRepository."""
    repo = InMemoryCoilRepository()
    coil = repo.create_coil(schemas.CoilCreate(length=10.0, weight=20.0))

    result = repo.remove_coil(coil.id)

    assert result == coil
    assert result.date_removed is not None
    assert len(repo.coils) == 1


def test_inmemory_remove_coil_not_found():
    """Тестирует попытку удаления несуществующего руллона в InMemoryCoilRepository."""
    repo = InMemoryCoilRepository()
    result = repo.remove_coil(999)

    assert result is None
    assert len(repo.coils) == 0


def test_inmemory_get_coils_empty():
    """Тестирует получение пустого списка руллонов в InMemoryCoilRepository."""
    repo = InMemoryCoilRepository()
    result = repo.get_coils()

    assert result == []


def test_inmemory_get_coils_with_filters():
    """Тестирует получение руллонов с фильтрами в InMemoryCoilRepository."""
    repo = InMemoryCoilRepository()
    coil = repo.create_coil(schemas.CoilCreate(length=10.0, weight=20.0))

    result = repo.get_coils(
        id_range=(1, 1), weight_range=(19.0, 21.0), length_range=(9.0, 11.0)
    )

    assert len(result) == 1
    assert result[0] == coil


def test_inmemory_get_statistics_empty():
    """Тестирует получение статистики при пустом хранилище в InMemoryCoilRepository."""
    repo = InMemoryCoilRepository()
    start_date = datetime.now(UTC) - timedelta(days=1)
    end_date = datetime.now(UTC)

    stats = repo.get_statistics(start_date, end_date)

    assert stats.added_count == 0
    assert stats.removed_count == 0
    assert stats.avg_length is None


def test_inmemory_get_statistics_with_data():
    """Тестирует получение статистики с данными в InMemoryCoilRepository."""
    repo = InMemoryCoilRepository()
    now = datetime.now(UTC)
    yesterday = now - timedelta(days=1)
    coil = repo.create_coil(schemas.CoilCreate(length=10.0, weight=20.0))
    coil.__dict__["date_added"] = yesterday
    repo.remove_coil(coil.id, now)

    stats = repo.get_statistics(yesterday, now)

    assert stats.added_count == 1
    assert stats.removed_count == 1
    assert stats.avg_length == 10.0
    assert stats.avg_weight == 20.0
    assert stats.total_weight == 20.0
