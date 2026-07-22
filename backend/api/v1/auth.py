from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from backend.api.v1.schemas import LoginRequest, TokenResponse, UserResponse
from backend.core.config import settings
from backend.core.exceptions import AuthenticationError
from backend.core.logging import get_logger
from backend.database.postgres import UserModel, async_session_factory
from backend.services.auth_service import (
    create_access_token,
    decode_access_token,
    verify_password,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = decode_access_token(credentials.credentials)
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"user_id": payload["sub"], "role": payload["role"]}


async def require_role(required_role: str, user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != required_role and user["role"] != "admin":
        raise HTTPException(status_code=403, detail=f"Role '{required_role}' required")
    return user


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    async with async_session_factory() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.username == request.username)
        )
        user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    token = create_access_token(user.id, user.role)
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    async with async_session_factory() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.id == user["user_id"])
        )
        db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=db_user.id,
        username=db_user.username,
        role=db_user.role,
        full_name=db_user.full_name,
    )
