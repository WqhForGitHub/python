"""刷新令牌 CRUD 操作。

RefreshToken 持久化于数据库，用于：
- 校验令牌是否有效 / 是否已被吊销
- 令牌轮转（refresh 时吊销旧令牌）
- 登出时吊销令牌
- 批量吊销某用户的所有令牌
"""
from datetime import datetime

from sqlalchemy.orm import Session

import models
from security import hash_token


def create_refresh_token(
    db: Session,
    user_id: int,
    jti: str,
    token: str,
    expires_at: datetime,
) -> models.RefreshToken:
    """将 refresh token 入库（仅存哈希）。"""
    record = models.RefreshToken(
        user_id=user_id,
        jti=jti,
        token_hash=hash_token(token),
        expires_at=expires_at,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_by_jti(db: Session, jti: str) -> models.RefreshToken | None:
    return db.query(models.RefreshToken).filter(models.RefreshToken.jti == jti).first()


def revoke(db: Session, token_record: models.RefreshToken) -> None:
    """吊销单个令牌。"""
    token_record.revoked = True
    db.commit()


def revoke_all_for_user(db: Session, user_id: int) -> int:
    """吊销某用户的所有未过期未吊销令牌，返回受影响行数。"""
    count = (
        db.query(models.RefreshToken)
        .filter(
            models.RefreshToken.user_id == user_id,
            models.RefreshToken.revoked == False,  # noqa: E712
        )
        .update({"revoked": True})
    )
    db.commit()
    return count


def cleanup_expired(db: Session) -> int:
    """清理已过期的令牌记录，返回删除行数。"""
    now = datetime.utcnow()
    count = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.expires_at < now)
        .delete()
    )
    db.commit()
    return count
