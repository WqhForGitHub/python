"""权限 CRUD 操作。"""

from sqlalchemy.orm import Session

import models
import schemas


def get_permission(db: Session, permission_id: int) -> models.Permission | None:
    return (
        db.query(models.Permission)
        .filter(models.Permission.id == permission_id)
        .first()
    )


def get_permission_by_code(db: Session, code: str) -> models.Permission | None:
    return db.query(models.Permission).filter(models.Permission.code == code).first()


def get_permissions(
    db: Session, skip: int = 0, limit: int = 100
) -> list[models.Permission]:
    return db.query(models.Permission).offset(skip).limit(limit).all()


def get_permissions_by_ids(
    db: Session, permission_ids: list[int]
) -> list[models.Permission]:
    return (
        db.query(models.Permission)
        .filter(models.Permission.id.in_(permission_ids))
        .all()
    )


def create_permission(
    db: Session, perm_in: schemas.PermissionCreate
) -> models.Permission:
    perm = models.Permission(
        code=perm_in.code,
        name=perm_in.name,
        description=perm_in.description,
    )
    db.add(perm)
    db.commit()
    db.refresh(perm)
    return perm


def delete_permission(db: Session, perm: models.Permission) -> None:
    db.delete(perm)
    db.commit()
