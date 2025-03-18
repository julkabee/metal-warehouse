import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime
from typing import List, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import engine, get_db
from app.repository import CoilRepository, SQLAlchemyCoilRepository

app = FastAPI(
    title="Metal Warehouse API",
    description="API для работы с руллонами на складе металлопроката.",
    version="1.0.0",
)

models.Base.metadata.create_all(bind=engine)


def get_repository(db: Session = Depends(get_db)) -> CoilRepository:
    """Получает репозиторий для работы с руллонами.

    Аргументы:
        db: Сессия базы данных.

    Возвращает:
        Экземпляр репозитория руллонов.
    """
    return SQLAlchemyCoilRepository(db)


@app.post("/coils/", response_model=schemas.Coil)
def create_coil(
    coil: schemas.CoilCreate, repo: CoilRepository = Depends(get_repository)
) -> schemas.Coil:
    """Создаёт новый руллон.

    Аргументы:
        coil: Данные для создания руллона.
        repo: Репозиторий руллонов.

    Возвращает:
        Созданный руллон.
    """
    return repo.create_coil(coil)


@app.delete("/coils/{coil_id}", response_model=schemas.Coil)
def remove_coil(
    coil_id: int, repo: CoilRepository = Depends(get_repository)
) -> schemas.Coil:
    """Удаляет руллон по его ID.

    Аргументы:
        coil_id: Идентификатор руллон.
        repo: Репозиторий руллонов.

    Возвращает:
        Удалённый руллон.

    Исключения:
        HTTPException: Если руллон не найден или уже удален (404).
    """
    coil = repo.remove_coil(coil_id)
    if not coil:
        raise HTTPException(status_code=404, detail="Coil not found or already removed")
    return coil


@app.get("/coils/", response_model=List[schemas.Coil])
def get_coils(
    id_min: Optional[int] = None,
    id_max: Optional[int] = None,
    weight_min: Optional[float] = None,
    weight_max: Optional[float] = None,
    length_min: Optional[float] = None,
    length_max: Optional[float] = None,
    date_added_min: Optional[str] = None,
    date_added_max: Optional[str] = None,
    date_removed_min: Optional[str] = None,
    date_removed_max: Optional[str] = None,
    repo: CoilRepository = Depends(get_repository),
) -> List[schemas.Coil]:
    """Получает список руллонов с фильтрацией по заданным параметрам.

    Аргументы:
        id_min: Минимальный идентификатор руллона.
        id_max: Максимальный идентификатор руллона.
        weight_min: Минимальный вес руллона.
        weight_max: Максимальный вес руллона.
        length_min: Минимальная длина руллона.
        length_max: Максимальная длина руллона.
        date_added_min: Минимальная дата добавления в формате ISO 8601.
        date_added_max: Максимальная дата добавления в формате ISO 8601.
        date_removed_min: Минимальная дата удаления в формате ISO 8601.
        date_removed_max: Максимальная дата удаления в формате ISO 8601.
        repo (CoilRepository): Репозиторий для операций с руллонами.

    Возвращает:
        List[schemas.Coil]: Список руллонов, соответствующих фильтрам.

    Исключения:
        HTTPException: Если формат даты неверный (код 422).
    """
    id_range = (id_min, id_max) if id_min is not None and id_max is not None else None
    weight_range = (
        (weight_min, weight_max)
        if weight_min is not None and weight_max is not None
        else None
    )
    length_range = (
        (length_min, length_max)
        if length_min is not None and length_max is not None
        else None
    )

    date_added_range = None
    if date_added_min is not None and date_added_max is not None:
        try:
            start = datetime.fromisoformat(date_added_min.replace(" ", "+", 1))
            end = datetime.fromisoformat(date_added_max.replace(" ", "+", 1))
            date_added_range = (start, end)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="Invalid date_added format. Use ISO 8601 (e.g., '2023-01-01T00:00:00')",
            )

    date_removed_range = None
    if date_removed_min is not None and date_removed_max is not None:
        try:
            start = datetime.fromisoformat(date_removed_min.replace(" ", "+", 1))
            end = datetime.fromisoformat(date_removed_max.replace(" ", "+", 1))
            date_removed_range = (start, end)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="Invalid date_removed format. Use ISO 8601 (e.g., '2023-01-01T00:00:00')",
            )

    coils = repo.get_coils(
        id_range=id_range,
        weight_range=weight_range,
        length_range=length_range,
        date_added_range=date_added_range,
        date_removed_range=date_removed_range,
    )
    return [schemas.Coil.model_validate(coil) for coil in coils]


@app.get("/statistics/", response_model=schemas.CoilStats)
def get_statistics(
    start_date: str, end_date: str, repo: CoilRepository = Depends(get_repository)
) -> schemas.CoilStats:
    """Вычисляет статистику по руллонам за заданный период.

    Аргументы:
        start_date: Начальная дата периода в формате ISO 8601.
        end_date: Конечная дата периода в формате ISO 8601.
        repo: Репозиторий для операций с руллонами.

    Возвращает:
        schemas.CoilStats: Объект статистики с данными о руллонах.

    Исключения:
        HTTPException: Если формат даты неверный (код 422) или start_date > end_date (код 400).
    """
    try:
        start_date_fixed = (
            start_date.replace(" ", "+", 1) if " " in start_date else start_date
        )
        end_date_fixed = end_date.replace(" ", "+", 1) if " " in end_date else end_date
        start = datetime.fromisoformat(start_date_fixed.rstrip("Z"))
        end = datetime.fromisoformat(end_date_fixed.rstrip("Z"))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid date format: {str(e)}")

    if start > end:
        raise HTTPException(
            status_code=400, detail="Start date must be before end date"
        )
    return repo.get_statistics(start, end)


# Запуск приложения через uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
