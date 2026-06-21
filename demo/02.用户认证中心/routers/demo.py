"""受保护资源示例：演示不同级别的访问控制。

用于直观展示 RBAC 的三个层级：
1. 公开接口（无需认证）
2. 已登录用户即可访问
3. 需要特定权限才能访问
"""

from fastapi import APIRouter, Depends

from deps import get_current_user, require_permissions
from models import User

router = APIRouter(prefix="/demo", tags=["示例受保护资源"])


@router.get("/public", summary="公开接口（无需认证）")
def public():
    return {"message": "这是一个公开接口，任何人都可以访问"}


@router.get("/profile", summary="已登录用户即可访问")
def profile(user: User = Depends(get_current_user)):
    return {
        "message": f"你好，{user.username}",
        "user_id": user.id,
        "roles": [r.name for r in user.roles],
    }


@router.get("/read", summary="需要 article:read 权限")
def need_read(_: User = Depends(require_permissions("article:read"))):
    return {"message": "你拥有 article:read 权限，可以查看文章"}


@router.post("/write", summary="需要 article:write 权限")
def need_write(_: User = Depends(require_permissions("article:write"))):
    return {"message": "你拥有 article:write 权限，写入成功"}
