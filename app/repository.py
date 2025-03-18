from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, extract, func, or_
from sqlalchemy.orm import Session

from app import models, schemas


class CoilRepository(ABC):
    """Абстрактный базовый класс для репозитория руллонов.

    Определяет интерфейс для операций с руллонами.
    """
    @abstractmethod
    def create_coil(self, coil: schemas.CoilCreate) -> models.Coil:
        """Создаёт новый руллон.

        Аргументы:
            coil (schemas.CoilCreate): Данные для создания руллона.

        Возвращает:
            models.Coil: Созданный руллона.
        """
        pass

    @abstractmethod
    def remove_coil(
        self, coil_id: int, date_removed: Optional[datetime] = None
    ) -> Optional[models.Coil]:
        """Удаляет руллон по его идентификатору.

        Аргументы:
            coil_id (int): Уникальный идентификатор руллона.
            date_removed (Optional[datetime]): Дата удаления (по умолчанию текущая).

        Возвращает:
            Optional[models.Coil]: Удалённый руллон или None.
        """
        pass

    @abstractmethod
    def get_coils(
        self,
        id_range: Optional[Tuple[int, int]] = None,
        weight_range: Optional[Tuple[float, float]] = None,
        length_range: Optional[Tuple[float, float]] = None,
        date_added_range: Optional[Tuple[datetime, datetime]] = None,
        date_removed_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> List[models.Coil]:
        """Получает список руллонов с фильтрацией.

        Аргументы:
            id_range (Optional[Tuple[int, int]]): Диапазон идентификаторов.
            weight_range (Optional[Tuple[float, float]]): Диапазон веса.
            length_range (Optional[Tuple[float, float]]): Диапазон длины.
            date_added_range (Optional[Tuple[datetime, datetime]]): Диапазон дат добавления.
            date_removed_range (Optional[Tuple[datetime, datetime]]): Диапазон дат удаления.

        Возвращает:
            List[models.Coil]: Список руллонов, соответствующих фильтрам.
        """
        pass

    @abstractmethod
    def get_statistics(
        self, start_date: datetime, end_date: datetime
    ) -> schemas.CoilStats:
        pass


class InMemoryCoilRepository(CoilRepository):
    """Репозиторий руллонов в памяти для тестирования или локального использования."""

    def __init__(self) -> None:
        """Инициализирует репозиторий с пустым списком руллонов."""
        self.coils: List[models.Coil] = []
        self._next_id = 1

    def create_coil(self, coil: schemas.CoilCreate) -> models.Coil:
        """Создаёт новый руллон в памяти.

        Аргументы:
            coil (schemas.CoilCreate): Данные для создания руллона.

        Возвращает:
            models.Coil: Созданный руллон с уникальным ID.
        """
        db_coil = models.Coil(
            id=self._next_id,
            length=coil.length,
            weight=coil.weight,
            date_added=datetime.now(UTC),
            date_removed=None,
        )
        self._next_id += 1
        self.coils.append(db_coil)
        return db_coil

    def remove_coil(
        self, coil_id: int, date_removed: Optional[datetime] = None
    ) -> Optional[models.Coil]:
        """Удаляет руллон по его идентификатору.

        Аргументы:
            coil_id (int): Уникальный идентификатор руллона.
            date_removed (Optional[datetime]): Дата удаления (по умолчанию текущая).

        Возвращает:
            Optional[models.Coil]: Удалённый руллон или None, если не найдена.
        """
        for coil in self.coils:
            if coil.id == coil_id and coil.date_removed is None:
                coil.date_removed = (
                    date_removed if date_removed is not None else datetime.now(UTC)
                )
                return coil
        return None

    def get_coils(
        self,
        id_range: Optional[Tuple[int, int]] = None,
        weight_range: Optional[Tuple[float, float]] = None,
        length_range: Optional[Tuple[float, float]] = None,
        date_added_range: Optional[Tuple[datetime, datetime]] = None,
        date_removed_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> List[models.Coil]:
        """Получает список руллонов с фильтрацией.

        Аргументы:
            id_range (Optional[Tuple[int, int]]): Диапазон идентификаторов.
            weight_range (Optional[Tuple[float, float]]): Диапазон веса.
            length_range (Optional[Tuple[float, float]]): Диапазон длины.
            date_added_range (Optional[Tuple[datetime, datetime]]): Диапазон дат добавления.
            date_removed_range (Optional[Tuple[datetime, datetime]]): Диапазон дат удаления.

        Возвращает:
            List[models.Coil]: Список руллонов, соответствующих фильтрам.
        """
        result = self.coils
        if id_range:
            result = [c for c in result if id_range[0] <= c.id <= id_range[1]]
        if weight_range:
            result = [c for c in result if weight_range[0] <= c.weight <= weight_range[1]]
        if length_range:
            result = [c for c in result if length_range[0] <= c.length <= length_range[1]]
        if date_added_range:
            result = [
                c
                for c in result
                if date_added_range[0] <= c.date_added <= date_added_range[1]
            ]
        if date_removed_range:
            result = [
                c
                for c in result
                if c.date_removed
                and date_removed_range[0] <= c.date_removed <= date_removed_range[1]
            ]
        return result

    def get_statistics(
        self, start_date: datetime, end_date: datetime
    ) -> schemas.CoilStats:
        """Вычисляет статистику по руллонам в памяти.

        Аргументы:
            start_date (datetime): Начальная дата периода.
            end_date (datetime): Конечная дата периода.

        Возвращает:
            schemas.CoilStats: Объект статистики по руллонам.
        """
        relevant_coils = [
            c
            for c in self.coils
            if (
                (c.date_added >= start_date and c.date_added <= end_date)
                or (
                    c.date_removed
                    and c.date_removed >= start_date
                    and c.date_removed <= end_date
                )
                or (
                    c.date_added <= end_date
                    and (c.date_removed is None or c.date_removed >= start_date)
                )
            )
        ]
        added_count = len(
            [c for c in self.coils if start_date <= c.date_added <= end_date]
        )
        removed_count = len(
            [
                c
                for c in self.coils
                if c.date_removed and start_date <= c.date_removed <= end_date
            ]
        )

        if not relevant_coils:
            return schemas.CoilStats(
                added_count=added_count,
                removed_count=removed_count,
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

        lengths = [c.length for c in relevant_coils]
        weights = [c.weight for c in relevant_coils]
        time_diffs = [
            (c.date_removed - c.date_added).total_seconds()
            for c in relevant_coils
            if c.date_removed is not None
        ]

        days_stats: List[Dict[str, Any]] = []
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        while current_date <= end_date:
            active_coils = [
                c
                for c in self.coils
                if c.date_added <= current_date
                and (c.date_removed is None or c.date_removed > current_date)
            ]
            days_stats.append(
                {
                    "date": current_date,
                    "count": len(active_coils),
                    "weight": sum(c.weight for c in active_coils),
                }
            )
            current_date += timedelta(days=1)

        day_max_count = (
            max(days_stats, key=lambda x: x["count"])["date"] if days_stats else None
        )
        day_min_count = (
            min(days_stats, key=lambda x: x["count"])["date"] if days_stats else None
        )
        day_max_weight = (
            max(days_stats, key=lambda x: x["weight"])["date"] if days_stats else None
        )
        day_min_weight = (
            min(days_stats, key=lambda x: x["weight"])["date"] if days_stats else None
        )

        return schemas.CoilStats(
            added_count=added_count,
            removed_count=removed_count,
            avg_length=sum(lengths) / len(lengths),
            avg_weight=sum(weights) / len(weights),
            max_length=max(lengths),
            min_length=min(lengths),
            max_weight=max(weights),
            min_weight=min(weights),
            total_weight=sum(weights),
            max_time_diff=max(time_diffs) if time_diffs else None,
            min_time_diff=min(time_diffs) if time_diffs else None,
            day_max_count=day_max_count,
            day_min_count=day_min_count,
            day_max_weight=day_max_weight,
            day_min_weight=day_min_weight,
        )
