"""角色 CRUD 操作。"""

from sqlalchemy.orm import Session

import models
import schemas


def get_role(db: Session, role_id: int) -> models.Role | None:
    return db.query(models.Role).filter(models.Role.id == role_id).first()


def get_role_by_name(db: Session, name: str) -> models.Role | None:
    return db.query(models.Role).filter(models.Role.name == name).first()


def get_roles(db: Session, skip: int = 0, limit: int = 50) -> list[models.Role]:
    return db.query(models.Role).offset(skip).limit(limit).all()


def get_roles_by_ids(db: Session, role_ids: list[int]) -> list[models.Role]:
    return db.query(models.Role).filter(models.Role.id.in_(role_ids)).all()


def create_role(db: Session, role_in: schemas.RoleCreate) -> models.Role:
    role = models.Role(name=role_in.name, description=role_in.description)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def update_role(
    db: Session, role: models.Role, role_in: schemas.RoleUpdate
) -> models.Role:
    update_data = role_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)
    db.commit()
    db.refresh(role)
    return role


def delete_role(db: Session, role: models.Role) -> None:
    db.delete(role)
    db.commit()


def set_permissions(
    db: Session, role: models.Role, permission_ids: list[int]
) -> models.Role:
    """全量覆盖角色的权限。"""
    from crud.permission import get_permissions_by_ids

    role.permissions = get_permissions_by_ids(db, permission_ids)
    db.commit()
    db.refresh(role)
    return role
