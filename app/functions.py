from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, extract, func, or_
from sqlalchemy.orm import Session

from app import models, schemas


def create_coil(db: Session, coil: schemas.CoilCreate) -> models.Coil:
    """Создаёт новый руллон в базе данных.

    Args:
        db: Сессия базы данных.
        coil: Данные для создания руллона.

    Returns:
        Созданный руллон.
    """
    db_coil = models.Coil(**coil.model_dump())
    db.add(db_coil)
    db.commit()
    db.refresh(db_coil)
    return db_coil


def remove_coil(db: Session, coil_id: int) -> Optional[models.Coil]:
    """Удаляет руллон по его идентификатору.

    Аргументы:
        db: Сессия базы данных.
        coil_id: Идентификатор руллона.

    Возвращает:
        Удалённый руллон или None, если руллон не найден или уже удален.
    """
    coil = db.query(models.Coil).filter(models.Coil.id == coil_id).first()
    if coil and coil.date_removed is None:
        coil.date_removed = datetime.now(UTC)
        db.commit()
        db.refresh(coil)
        return coil
    return None


def get_coils(
    db: Session,
    id_range: Optional[Tuple[int, int]] = None,
    weight_range: Optional[Tuple[float, float]] = None,
    length_range: Optional[Tuple[float, float]] = None,
    date_added_range: Optional[Tuple[datetime, datetime]] = None,
    date_removed_range: Optional[Tuple[datetime, datetime]] = None,
) -> List[models.Coil]:
    """Получает список руллонов с фильтрацией.

    Аргументы:
        db: Сессия базы данных.
        id_range: Диапазон идентификаторов.
        weight_range: Диапазон веса.
        length_range: Диапазон длины.
        date_added_range: Диапазон дат добавления.
        date_removed_range: Диапазон дат удаления.

    Возвращает:
        Список руллонов, соответствующих фильтрам.
    """
    query = db.query(models.Coil)

    if id_range:
        query = query.filter(models.Coil.id.between(id_range[0], id_range[1]))
    if weight_range:
        query = query.filter(
            models.Coil.weight.between(weight_range[0], weight_range[1])
        )
    if length_range:
        query = query.filter(
            models.Coil.length.between(length_range[0], length_range[1])
        )
    if date_added_range:
        query = query.filter(
            models.Coil.date_added.between(date_added_range[0], date_added_range[1])
        )
    if date_removed_range:
        query = query.filter(
            models.Coil.date_removed.between(
                date_removed_range[0], date_removed_range[1]
            )
        )
    return query.all()


def get_statistics(
    db: Session, start_date: datetime, end_date: datetime
) -> schemas.CoilStats:
    """Вычисляет статистику по руллонам за период.

    Args:
        db: Сессия базы данных.
        start_date: Начало периода.
        end_date: Конец периода.

    Returns:
        Статистика по руллонам.
    """
    added_count = (
        db.query(models.Coil)
        .filter(models.Coil.date_added.between(start_date, end_date))
        .count()
    )

    removed_count = (
        db.query(models.Coil)
        .filter(models.Coil.date_removed.between(start_date, end_date))
        .count()
    )

    coils = db.query(models.Coil).filter(
        or_(
            models.Coil.date_added.between(start_date, end_date),
            models.Coil.date_removed.between(start_date, end_date),
            and_(
                models.Coil.date_added <= end_date,
                or_(
                    models.Coil.date_removed >= start_date,
                    models.Coil.date_removed.is_(None),
                ),
            ),
        )
    )

    stats = coils.with_entities(
        func.avg(models.Coil.length).label("avg_length"),
        func.avg(models.Coil.weight).label("avg_weight"),
        func.max(models.Coil.length).label("max_length"),
        func.min(models.Coil.length).label("min_length"),
        func.max(models.Coil.weight).label("max_weight"),
        func.min(models.Coil.weight).label("min_weight"),
        func.sum(models.Coil.weight).label("total_weight"),
    ).first()

    time_diff = (
        db.query(
            func.max(
                extract("epoch", models.Coil.date_removed)
                - extract("epoch", models.Coil.date_added)
            ).label("max_time_diff"),
            func.min(
                extract("epoch", models.Coil.date_removed)
                - extract("epoch", models.Coil.date_added)
            ).label("min_time_diff"),
        )
        .filter(
            models.Coil.date_removed.isnot(None),
            models.Coil.date_added.between(start_date, end_date),
        )
        .first()
    )

    days_stats: List[Dict[str, Any]] = []
    current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    while current_date <= end_date:
        count = (
            db.query(models.Coil)
            .filter(
                models.Coil.date_added <= current_date,
                or_(
                    models.Coil.date_removed > current_date,
                    models.Coil.date_removed.is_(None),
                ),
            )
            .count()
        )
        weight = (
            db.query(func.sum(models.Coil.weight))
            .filter(
                models.Coil.date_added <= current_date,
                or_(
                    models.Coil.date_removed > current_date,
                    models.Coil.date_removed.is_(None),
                ),
            )
            .scalar()
        )
        days_stats.append(
            {
                "date": current_date,
                "count": count,
                "weight": weight if weight is not None else 0.0,
            }
        )
        current_date += timedelta(days=1)

    if days_stats:
        day_max_count = max(days_stats, key=lambda x: x["count"])["date"]
        day_min_count = min(days_stats, key=lambda x: x["count"])["date"]
        day_max_weight = max(days_stats, key=lambda x: x["weight"])["date"]
        day_min_weight = min(days_stats, key=lambda x: x["weight"])["date"]
    else:
        day_max_count = day_min_count = day_max_weight = day_min_weight = None

    if not added_count:
        return schemas.CoilStats(
            added_count=0,
            removed_count=0,
            avg_length=None,
            avg_weight=None,
            max_length=None,
            min_length=None,
            max_weight=None,
            min_weight=None,
            total_weight=None,
            max_time_diff=None,
            min_time_diff=None,
            day_max_count=None,
            day_min_count=None,
            day_max_weight=None,
            day_min_weight=None,
        )

    return schemas.CoilStats(
        added_count=added_count or 0,
        removed_count=removed_count or 0,
        avg_length=stats.avg_length,
        avg_weight=stats.avg_weight,
        max_length=stats.max_length,
        min_length=stats.min_length,
        max_weight=stats.max_weight,
        min_weight=stats.min_weight,
        total_weight=stats.total_weight,
        max_time_diff=time_diff.max_time_diff if time_diff else None,
        min_time_diff=time_diff.min_time_diff if time_diff else None,
        day_max_count=day_max_count,
        day_min_count=day_min_count,
        day_max_weight=day_max_weight,
        day_min_weight=day_min_weight,
    )
