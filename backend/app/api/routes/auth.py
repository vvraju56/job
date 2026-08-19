"""Authentication routes: register, login, refresh, logout, me."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbDep
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.models import User
from app.schemas.schemas import GoogleLoginRequest, LoginRequest, RefreshRequest, RegisterRequest, TokenPair, UserOut
from app.services.firebase import verify_google_id_token

router = APIRouter(prefix="/auth", tags=["auth"])


async def _authenticate(db: DbDep, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()
    if user is None or user.hashed_password is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user


def _token_pair(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: DbDep) -> TokenPair:
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        name=payload.name,
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        skills=[],
        preferences={"remote_only": False, "job_types": [], "locations": [], "keywords": []},
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _token_pair(user)


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, db: DbDep) -> TokenPair:
    user = await _authenticate(db, payload.email, payload.password)
    return _token_pair(user)


@router.post("/google", response_model=TokenPair)
async def google_login(payload: GoogleLoginRequest, db: DbDep) -> TokenPair:
    """Google sign-in via a Firebase-verified ID token.

    The web/mobile client signs in with the Google Firebase provider and
    sends the resulting ID token here. The backend verifies it with the
    Firebase Admin SDK and creates/logs in the matching user.
    """
    claims = verify_google_id_token(payload.id_token)
    if claims is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google session. Firebase is not configured or the token could not be verified.",
        )
    email = (claims.get("email") or "").lower()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account has no email address.",
        )

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            name=claims.get("name") or email.split("@")[0],
            email=email,
            avatar=claims.get("picture"),
            hashed_password=None,
            skills=[],
            preferences={"remote_only": False, "job_types": [], "locations": [], "keywords": []},
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return _token_pair(user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: DbDep) -> TokenPair:
    subject = decode_token(payload.refresh_token, expected_type="refresh")
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    result = await db.execute(select(User).where(User.id == subject))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return _token_pair(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(_user: CurrentUser) -> None:
    # Token is stateless JWT; clients discard it. Revocation can be layered with Redis.
    return None


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> User:
    return user