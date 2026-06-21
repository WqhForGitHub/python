"""用户路由。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.user
import schemas
from database import get_db

router = APIRouter(prefix="/users", tags=["用户"])


@router.post(
    "/",
    response_model=schemas.UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # 用户名唯一性校验
    if crud.user.get_user_by_username(db, username=user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )
    # 邮箱唯一性校验
    if crud.user.get_user_by_email(db, email=user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册",
        )
    return crud.user.create_user(db, user_in=user_in)


@router.get(
    "/",
    response_model=list[schemas.UserRead],
    summary="获取用户列表",
)
def list_users(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return crud.user.get_users(db, skip=skip, limit=limit)


@router.get(
    "/{user_id}",
    response_model=schemas.UserRead,
    summary="获取用户详情",
)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 ID {user_id} 不存在",
        )
    return db_user


@router.put(
    "/{user_id}",
    response_model=schemas.UserRead,
    summary="更新用户",
)
def update_user(
    user_id: int,
    user_in: schemas.UserUpdate,
    db: Session = Depends(get_db),
):
    db_user = crud.user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 ID {user_id} 不存在",
        )

    # 若要修改用户名，校验新用户名是否已被占用
    if user_in.username and user_in.username != db_user.username:
        if crud.user.get_user_by_username(db, username=user_in.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在",
            )
    # 若要修改邮箱，校验新邮箱是否已被占用
    if user_in.email and user_in.email != db_user.email:
        if crud.user.get_user_by_email(db, email=user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册",
            )

    return crud.user.update_user(db, db_user=db_user, user_in=user_in)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除用户",
)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 ID {user_id} 不存在",
        )
    crud.user.delete_user(db, db_user=db_user)
    return None
