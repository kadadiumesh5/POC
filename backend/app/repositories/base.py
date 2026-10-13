from typing import Type, TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository:
    model: Type[T]

    def __init__(self, db: Session):
        self.db = db

    def add(self, entity: T) -> T:
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, entity_id: int) -> T | None:
        return self.db.query(self.model).filter(self.model.id == entity_id).first()

    def update(self, entity: T) -> T:
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity: T) -> None:
        self.db.delete(entity)
        self.db.commit()
