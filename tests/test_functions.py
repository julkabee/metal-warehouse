from sqlalchemy.orm import Session

from app import functions


def test_create_coil(db_session: Session, coil_create):
    """Тестирует создание руллона через функцию create_coil.

    Аргументы:
        db_session (Session): Сессия базы данных.
        coil_create: Фикстура с данными для создания руллона.
    """
    result = functions.create_coil(db_session, coil_create)
    assert result.id is not None
    assert result.length == coil_create.length
    assert result.weight == coil_create.weight
    assert result.date_added is not None
    assert result.date_removed is None


def test_remove_coil_success(db_session: Session, coil):
    """Тестирует успешное удаление руллона.

    Аргументы:
        db_session (Session): Сессия базы данных.
        coil: Фикстура с активным руллоном.
    """
    result = functions.remove_coil(db_session, coil.id)
    assert result == coil
    assert result.date_removed is not None


def test_remove_coil_not_found(db_session: Session):
    """Тестирует попытку удаления несуществующего руллона.

    Аргументы:
        db_session (Session): Сессия базы данных.
    """
    result = functions.remove_coil(db_session, 999)
    assert result is None


def test_remove_coil_already_removed(db_session: Session, removed_coil):
    """Тестирует попытку удаления уже удалённого руллона.

    Аргументы:
        db_session (Session): Сессия базы данных.
        removed_coil: Фикстура с удалённым руллоном.
    """
    result = functions.remove_coil(db_session, removed_coil.id)
    assert result is None


def test_get_coils_no_filters(db_session: Session, coil_list):
    """Тестирует получение всех руллонов без фильтров.

    Аргументы:
        db_session (Session): Сессия базы данных.
        coil_list: Фикстура со списком руллонов.
    """
    result = functions.get_coils(db_session)
    assert len(result) == 2
    assert result[0].id == coil_list[0].id
    assert result[1].id == coil_list[1].id


def test_get_coils_with_filters(db_session: Session, coil, date_range):
    """Тестирует получение руллонов с фильтрами.

    Аргументы:
        db_session (Session): Сессия базы данных.
        coil: Фикстура с активным руллоном.
        date_range: Фикстура с диапазоном дат.
    """
    result = functions.get_coils(
        db_session,
        id_range=(coil.id, coil.id),
        weight_range=(19.0, 21.0),
        length_range=(9.0, 11.0),
        date_added_range=(date_range["start_date"], date_range["end_date"]),
    )
    assert len(result) == 1
    assert result[0].id == coil.id


def test_get_coils_empty(db_session: Session):
    """Тестирует получение руллонов при пустой базе данных.

    Аргументы:
        db_session (Session): Сессия базы данных.
    """
    result = functions.get_coils(db_session)
    assert result == []


def test_get_statistics_empty(db_session: Session, date_range):
    """Тестирует получение статистики при пустой базе данных.

    Аргументы:
        db_session (Session): Сессия базы данных.
        date_range: Фикстура с диапазоном дат.
    """
    stats = functions.get_statistics(
        db_session, date_range["start_date"], date_range["end_date"]
    )
    assert stats.added_count == 0
    assert stats.removed_count == 0
    assert stats.avg_length is None


def test_get_statistics_with_data(db_session: Session, coil_list, date_range):
    """Тестирует получение статистики с данными в базе.

    Аргументы:
        db_session (Session): Сессия базы данных.
        coil_list: Фикстура со списком руллонов.
        date_range: Фикстура с диапазоном дат.
    """
    stats = functions.get_statistics(
        db_session, date_range["start_date"], date_range["end_date"]
    )
    assert stats.added_count == 2
    assert stats.removed_count == 1
    assert stats.avg_length == 12.5
    assert stats.avg_weight == 22.5
    assert stats.total_weight == 45.0
