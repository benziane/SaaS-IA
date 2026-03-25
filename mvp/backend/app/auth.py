"""
JWT Authentication and user management
"""

import uuid
from datetime import UTC, datetime, timedelta, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.core.token_blacklist import (
    blacklist_token,
    blacklist_user_tokens,
    is_blacklisted,
    is_user_tokens_revoked,
)
from app.database import get_session
from app.models.user import User, Role
from app.schemas.user import UserCreate, UserRead, Token, TokenData, TokenResponse, RefreshTokenRequest, UserUpdateProfile, PasswordChange
from app.rate_limit import limiter, get_rate_limit

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# MED-02: Account lockout after repeated failed login attempts
# ---------------------------------------------------------------------------
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60  # 15 minutes


async def _get_login_redis():
    """Return the async Redis client used by app.cache, or None."""
    try:
        from app.cache import _get_redis as _cache_get_redis
        return await _cache_get_redis()
    except Exception:
        return None


async def _check_login_lockout(email: str) -> Optional[int]:
    """
    Check whether *email* is locked out due to too many failed attempts.

    Returns the number of seconds remaining in the lockout window, or
    ``None`` if the account is not locked.  Fails open (returns None) when
    Redis is unavailable.
    """
    try:
        client = await _get_login_redis()
        if client is None:
            return None
        key = f"login_attempts:{email}"
        attempts = await client.get(key)
        if attempts is not None and int(attempts) >= LOGIN_MAX_ATTEMPTS:
            ttl = await client.ttl(key)
            return max(ttl, 1)
    except Exception as e:
        logger.debug("login_lockout_check_error", email=email, error=str(e))
    return None


async def _record_failed_login(email: str) -> None:
    """Increment the failed-login counter for *email* (TTL = lockout window)."""
    try:
        client = await _get_login_redis()
        if client is None:
            return
        key = f"login_attempts:{email}"
        pipe = client.pipeline()
        pipe.incr(key)
        pipe.expire(key, LOGIN_LOCKOUT_SECONDS)
        await pipe.execute()
    except Exception as e:
        logger.debug("login_lockout_record_error", email=email, error=str(e))


async def _reset_login_attempts(email: str) -> None:
    """Clear the failed-login counter for *email* on successful login."""
    try:
        client = await _get_login_redis()
        if client is None:
            return
        await client.delete(f"login_attempts:{email}")
    except Exception as e:
        logger.debug("login_lockout_reset_error", email=email, error=str(e))


# Router
router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with type='access', jti and iat claims"""
    to_encode = data.copy()

    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "access",
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """Create a long-lived JWT refresh token with type='refresh', jti and iat claims"""
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """Get user by email"""
    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def authenticate_user(session: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate a user"""
    user = await get_user_by_email(session, email)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    revoked_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has been revoked",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")

        if email is None:
            raise credentials_exception

        # Reject refresh tokens used as access tokens
        token_type = payload.get("type")
        if token_type == "refresh":
            raise credentials_exception

        # --- CRIT-03: Token blacklist checks ---
        jti = payload.get("jti")
        if jti and await is_blacklisted(jti):
            logger.info("token_rejected_blacklisted", jti=jti)
            raise revoked_exception

        iat = payload.get("iat")
        if await is_user_tokens_revoked(email, iat):
            logger.info("token_rejected_user_revoked", email=email)
            raise revoked_exception
        # --- End CRIT-03 ---

        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = await get_user_by_email(session, email=token_data.email)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


async def get_current_user_optional(request: Request) -> Optional[User]:
    """
    Get current user from request without raising exceptions.

    Returns the User if a valid Bearer token is present and the user
    exists and is active.  Returns None otherwise.

    Useful for middleware or optional-auth scenarios where
    unauthenticated requests should not be rejected.
    """
    try:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            return None

        # Reject refresh tokens
        if payload.get("type") == "refresh":
            return None

        # --- CRIT-03: Token blacklist checks ---
        jti = payload.get("jti")
        if jti and await is_blacklisted(jti):
            return None

        iat = payload.get("iat")
        if await is_user_tokens_revoked(email, iat):
            return None
        # --- End CRIT-03 ---

        from app.database import get_session_context

        async with get_session_context() as session:
            user = await get_user_by_email(session, email=email)
            if user and user.is_active:
                return user

        return None
    except Exception:
        return None


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_role(required_role: Role):
    """Dependency to require a specific role"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user
    return role_checker


# Routes

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_rate_limit("auth_register"))
async def register(
    request: Request,
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Register a new user
    
    Rate limit: 5 requests/minute (anti-abuse)
    """
    
    # Check if user already exists
    existing_user = await get_user_by_email(session, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=Role.USER,
        is_active=True
    )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=TokenResponse)
@limiter.limit(get_rate_limit("auth_login"))
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session)
):
    """
    Login and get JWT access token + refresh token.

    Rate limit: 5 requests/minute (anti-brute force)
    Account lockout: 15 minutes after 5 failed attempts (MED-02)
    """

    email = form_data.username

    # --- MED-02: Check account lockout before authentication ---
    lockout_remaining = await _check_login_lockout(email)
    if lockout_remaining is not None:
        logger.warning("login_locked_out", email=email, retry_after=lockout_remaining)
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many failed login attempts. Account temporarily locked."},
            headers={"Retry-After": str(lockout_remaining)},
        )

    user = await authenticate_user(session, email, form_data.password)

    if not user:
        # Record the failed attempt
        await _record_failed_login(email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Successful login: reset the failed-attempt counter
    await _reset_login_attempts(email)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(user_id=user.email)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(get_rate_limit("auth_login"))
async def refresh(
    request: Request,
    body: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Refresh an expired access token using a valid refresh token.

    Returns a new access token and a rotated refresh token.
    Rate limit: same as login (5 requests/minute)
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            body.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        email: str = payload.get("sub")
        token_type: str = payload.get("type")

        if email is None or token_type != "refresh":
            raise credentials_exception

        # --- CRIT-03: Check if refresh token is blacklisted ---
        jti = payload.get("jti")
        if jti and await is_blacklisted(jti):
            raise credentials_exception

        iat = payload.get("iat")
        if await is_user_tokens_revoked(email, iat):
            raise credentials_exception
        # --- End CRIT-03 ---

    except JWTError:
        raise credentials_exception

    # Verify that the user still exists and is active
    user = await get_user_by_email(session, email=email)

    if user is None or not user.is_active:
        raise credentials_exception

    # Blacklist the old refresh token so it cannot be reused
    if jti:
        old_exp = payload.get("exp", 0)
        remaining = max(int(old_exp - datetime.now(UTC).timestamp()), 1)
        await blacklist_token(jti, remaining)

    # Issue new token pair (token rotation)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires,
    )
    new_refresh_token = create_refresh_token(user_id=user.email)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.get("/me", response_model=UserRead)
@limiter.limit(get_rate_limit("auth_me"))
async def read_users_me(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information

    Rate limit: 20 requests/minute
    """
    return current_user


@router.put("/profile", response_model=UserRead)
@limiter.limit(get_rate_limit("auth_me"))
async def update_profile(
    request: Request,
    profile_data: UserUpdateProfile,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Update current user profile (full_name)

    Rate limit: 20 requests/minute
    """
    current_user.full_name = profile_data.full_name
    current_user.updated_at = datetime.now(UTC)

    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)

    return current_user


@router.put("/password")
@limiter.limit("3/minute")
async def change_password(
    request: Request,
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Change current user password

    Rate limit: 3 requests/minute
    """
    # Validate current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Prevent setting the same password
    if verify_password(password_data.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.now(UTC)

    session.add(current_user)
    await session.commit()

    # CRIT-03: Invalidate all existing tokens for this user
    await blacklist_user_tokens(str(current_user.email))
    logger.info("password_changed_tokens_revoked", user_id=str(current_user.id))

    return {"message": "Password changed successfully"}


# ---------------------------------------------------------------------------
# Logout endpoints (CRIT-03)
# ---------------------------------------------------------------------------

async def _extract_token_claims(token: str) -> dict:
    """Decode a token and return its claims. Raises on invalid tokens."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


@router.post("/logout")
@limiter.limit("10/minute")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    token: str = Depends(oauth2_scheme),
):
    """
    Logout the current session by blacklisting the access token.

    The token's JTI is added to the Redis blacklist with a TTL equal to
    the token's remaining lifetime, so it auto-expires.

    Rate limit: 10 requests/minute
    """
    try:
        payload = _extract_token_claims(token)
        jti = payload.get("jti")
        exp = payload.get("exp", 0)
        if jti:
            remaining = max(int(exp - datetime.now(UTC).timestamp()), 1)
            await blacklist_token(jti, remaining)
            logger.info("user_logged_out", user_id=str(current_user.id), jti=jti)
    except JWTError:
        pass  # Token already validated by get_current_active_user

    return {"message": "Successfully logged out"}


@router.post("/logout-all")
@limiter.limit("3/minute")
async def logout_all(
    request: Request,
    current_user: User = Depends(get_current_active_user),
):
    """
    Logout all sessions by invalidating every token issued for this user.

    A revoked-at timestamp is stored in Redis; any token with an ``iat``
    earlier than that timestamp will be rejected.

    Rate limit: 3 requests/minute
    """
    await blacklist_user_tokens(str(current_user.email))
    logger.info("user_logged_out_all", user_id=str(current_user.id))

    return {"message": "All sessions have been logged out"}

