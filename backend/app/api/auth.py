"""认证 API。"""

from __future__ import annotations

import threading
import time
from collections import deque

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserMe

router = APIRouter(prefix="/auth", tags=["auth"])

# --- 登录失败限流（进程内实现，无需 Redis）---
# key: f"{username}|{ip}", value: deque of failure timestamps
_login_failures: dict[str, deque[float]] = {}
_login_lock = threading.Lock()
_LOGIN_WINDOW_SEC = 15 * 60  # 15 分钟窗口
_LOGIN_MAX_FAILS = 5  # 窗口内最多失败次数


def _record_failure(key: str) -> int:
    """记录一次失败，返回当前窗口内的失败次数。"""
    now = time.time()
    with _login_lock:
        dq = _login_failures.setdefault(key, deque())
        # 清理窗口外的旧记录
        while dq and now - dq[0] > _LOGIN_WINDOW_SEC:
            dq.popleft()
        dq.append(now)
        return len(dq)


def _clear_failures(key: str) -> None:
    """登录成功清零。"""
    with _login_lock:
        _login_failures.pop(key, None)


def _get_block_status(key: str) -> tuple[bool, int]:
    """返回 (是否被限流, 剩余秒数)。"""
    now = time.time()
    with _login_lock:
        dq = _login_failures.get(key)
        if not dq:
            return False, 0
        # 清理过期
        while dq and now - dq[0] > _LOGIN_WINDOW_SEC:
            dq.popleft()
        if len(dq) >= _LOGIN_MAX_FAILS:
            remaining = int(_LOGIN_WINDOW_SEC - (now - dq[0]))
            return True, max(0, remaining)
        return False, 0


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    ip = request.client.host if request.client else "unknown"
    key = f"{payload.username}|{ip}"

    # 限流预检
    blocked, remaining = _get_block_status(key)
    if blocked:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"登录失败次数过多，请 {remaining} 秒后再试",
        )

    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        count = _record_failure(key)
        remaining_fails = _LOGIN_MAX_FAILS - count
        if remaining_fails <= 0:
            # 刚触发限流
            _, rem = _get_block_status(key)
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                f"登录失败次数过多，请 {rem} 秒后再试",
            )
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            f"用户名或密码错误（还可尝试 {remaining_fails} 次）",
        )

    # 登录成功，清零
    _clear_failures(key)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserMe)
def me(current: User = Depends(get_current_user)) -> UserMe:
    return current
