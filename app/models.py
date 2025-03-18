from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, Integer

from app.db import Base


class Coil(Base):
    """Модель руллона в базе данных.

    Атрибуты:
        id (int): Уникальный идентификатор.
        length (float): Длина руллона.
        weight (float): Вес руллона.
        date_added (datetime): Дата добавления.
        date_removed (datetime, optional): Дата удаления.
    """
    __tablename__ = "coils"
    id = Column(Integer, primary_key=True, index=True)
    length = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    date_added = Column(DateTime, default=datetime.now(UTC))
    date_removed = Column(DateTime, nullable=True)
