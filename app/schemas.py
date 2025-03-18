from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CoilBase(BaseModel):
    """Базовая схема для руллона.

    Атрибуты:
        length (float): Длина руллона (>0).
        weight (float): Вес руллона (>0).
    """
    length: float = Field(gt=0)
    weight: float = Field(gt=0)


class CoilCreate(CoilBase):
    """Схема для создания руллона."""
    pass


class Coil(CoilBase):
    """Схема руллона с дополнительными полями.

    Атрибуты:
        id (int): Уникальный идентификатор.
        date_added (datetime): Дата добавления.
        date_removed (datetime, optional): Дата удаления.
    """
    id: int
    date_added: datetime
    date_removed: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class CoilStats(BaseModel):
    """Схема статистики по руллонам.

    Атрибуты:
        added_count: Количество добавленных катушек за период.
        removed_count: Количество удалённых катушек за период.
        avg_length: Средняя длина катушек.
        avg_weight: Средний вес катушек.
        max_length: Максимальная длина катушек.
        min_length: Минимальная длина катушек.
        max_weight: Максимальный вес катушек.
        min_weight: Минимальный вес катушек.
        total_weight: Общий вес катушек.
        max_time_diff: Максимальная разница времени между добавлением и удалением.
        min_time_diff: Минимальная разница времени между добавлением и удалением.
        day_max_count: День с максимальным количеством катушек.
        day_min_count: День с минимальным количеством катушек.
        day_max_weight: День с максимальным весом катушек.
        day_min_weight: День с минимальным весом катушек.
    """
    added_count: int
    removed_count: int
    avg_length: Optional[float] = None
    avg_weight: Optional[float] = None
    max_length: Optional[float] = None
    min_length: Optional[float] = None
    max_weight: Optional[float] = None
    min_weight: Optional[float] = None
    total_weight: Optional[float] = None
    max_time_diff: Optional[float] = None
    min_time_diff: Optional[float] = None
    day_max_count: Optional[datetime] = None
    day_min_count: Optional[datetime] = None
    day_max_weight: Optional[datetime] = None
    day_min_weight: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
