"""BlackBox — Authentication and User Profile API Router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Investigation, Patch, Repository, User
from app.core.schemas import AuthResponse, UserLogin, UserProfileStats, UserRead, UserRegister
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    email_clean = payload.email.strip().lower()
    username_clean = payload.username.strip().lower()

    # Check if email or username already exists
    existing = await db.execute(
        select(User).where(or_(User.email == email_clean, User.username == username_clean))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or username already exists",
        )

    user = User(
        email=email_clean,
        username=username_clean,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip() if payload.full_name else username_clean.capitalize(),
        avatar_url=f"https://api.dicebear.com/7.x/bottts/svg?seed={username_clean}",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id), "username": user.username, "email": user.email})

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Authenticate existing user",
)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    query_str = payload.username_or_email.strip().lower()

    result = await db.execute(
        select(User).where(
            or_(User.username == query_str, User.email == query_str),
            User.is_active.is_(True),
        )
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": str(user.id), "username": user.username, "email": user.email})

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserProfileStats,
    summary="Get current user profile and isolated repository statistics",
)
async def me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileStats:
    # Compute counts for current user
    repo_count_res = await db.execute(
        select(func.count(Repository.id)).where(Repository.user_id == current_user.id)
    )
    repo_count = repo_count_res.scalar_one() or 0

    inv_count_res = await db.execute(
        select(func.count(Investigation.id))
        .join(Repository, Investigation.repository_id == Repository.id)
        .where(Repository.user_id == current_user.id)
    )
    inv_count = inv_count_res.scalar_one() or 0

    patch_count_res = await db.execute(
        select(func.count(Patch.id))
        .join(Investigation, Patch.investigation_id == Investigation.id)
        .join(Repository, Investigation.repository_id == Repository.id)
        .where(Repository.user_id == current_user.id)
    )
    patch_count = patch_count_res.scalar_one() or 0

    return UserProfileStats(
        user=UserRead.model_validate(current_user),
        repository_count=repo_count,
        investigation_count=inv_count,
        patch_count=patch_count,
    )
