from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.database import get_db
from app.models.user import User
from app.schemas import Token, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/auth", tags=["认证"])
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """开发模式：认证已关闭。
    有有效 token 时解析对应用户（向后兼容）；无 token 一律返回默认 admin 用户。
    """
    if credentials:
        payload = decode_access_token(credentials.credentials)
        if payload and payload.get("sub"):
            user = db.query(User).filter(User.id == int(payload["sub"])).first()
            if user and user.is_active:
                return user
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        user = User(
            username="admin",
            email="admin@aigc.com",
            hashed_password=get_password_hash("admin123"),
            nickname="创作者小明",
            is_vip=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.post("/register", response_model=Token)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        nickname=user_data.nickname or user_data.username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = create_access_token({"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer", user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="账号已被禁用")
    access_token = create_access_token({"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer", user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
