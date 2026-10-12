"""User service."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Request
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.user.exceptions import (
    DuplicateEmailException,
    DuplicatePhoneException,
    InactiveUserException,
    InvalidCredentialsException,
    SelfDeactivationException,
    UserNotFoundException,
)
from apps.user.models.user import UserModel
from apps.user.types import UserSortField
from apps.user.utils import build_user_page, fetch_user, verify_active_user
from config import settings
from constants import PAYLOAD_TIMEOUT
from core.common_helpers import (
    create_tokens,
    decrypt,
    hash_password,
    validate_email,
    validate_input_fields,
    verify_password,
)
from core.db import db_session
from core.types import RoleType
from core.utils.set_cookies import create_user_token_caching


class UserService:
    """Manages user accounts and authentication."""

    def __init__(self, session: Annotated[AsyncSession, db_session]) -> None:
        """Initialize the user service.

        Args:
            session: Async database session.
        """
        self.session = session

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    async def login_user(
        self,
        request: Request,
        encrypted_data: str,
        encrypted_key: str,
        iv: str,
    ) -> dict[str, str]:
        """Decrypt sign-in credentials, verify the user, and issue tokens.

        Args:
            request: FastAPI request exposing the RSA key on app.state.
            encrypted_data: Base64 AES ciphertext.
            encrypted_key: Base64 RSA-wrapped AES key.
            iv: Base64 initialisation vector.

        Returns:
            ``{"accessToken": ..., "refreshToken": ...}``

        Raises:
            InvalidCredentialsException: When email or password does not match.
            InactiveUserException: When the account is deactivated.
        """
        payload = decrypt(
            rsa_key=request.app.state.rsa_key,
            enc_data=encrypted_data,
            encrypt_key=encrypted_key,
            iv_input=iv,
            time_check=settings.DECRYPT_REQUEST_TIME_CHECK or False,
            timeout=PAYLOAD_TIMEOUT,
        )

        email = payload.get("email", "")
        password = payload.get("password", "")
        validate_input_fields(email=email, password=password)
        validate_email(email)

        user = await self.session.scalar(
            select(UserModel).where(UserModel.email == email)
        )
        if user is None:
            raise InvalidCredentialsException

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsException

        if not user.is_active:
            raise InactiveUserException

        user.last_login_at = datetime.now(timezone.utc)

        tokens = create_tokens(user.id, user.role.value)
        await create_user_token_caching(
            user_id=user.id,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            role=user.role.value,
        )
        return tokens

    async def refresh_tokens(self, refresh_token: str) -> dict[str, str]:
        """Validate a refresh token and issue a fresh pair.

        Args:
            refresh_token: The client's current refresh token.

        Returns:
            Fresh ``accessToken`` / ``refreshToken`` pair.

        Raises:
            InvalidJWTTokenException: When the refresh token is invalid or revoked.
        """
        from core.auth import refresh as refresh_token_module

        claims = refresh_token_module.decode(refresh_token)
        user_id = UUID(claims["sub"])
        role = claims["role"]

        user = await fetch_user(self.session, user_id)
        if user is None or not user.is_active:
            raise InvalidCredentialsException

        return create_tokens(user_id, role)

    async def sign_out(self, access_token: str, refresh_token: str) -> None:
        """Revoke both tokens from Redis.

        Args:
            access_token: Current access token.
            refresh_token: Current refresh token.
        """
        from core.utils.set_cookies import revoke_token

        if access_token:
            await revoke_token(access_token)
        if refresh_token:
            await revoke_token(refresh_token)

    # ------------------------------------------------------------------
    # Current user
    # ------------------------------------------------------------------

    async def get_current_user(self, user_id: UUID) -> UserModel:
        """Return the full user record for the authenticated caller.

        Args:
            user_id: UUID extracted from the access token.

        Returns:
            UserModel of the authenticated user.
        """
        return await verify_active_user(self.session, user_id)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create_user(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        role: RoleType,
        phone: str | None,
        request: Request,
        created_by: int | None = None,
    ) -> UserModel:
        """Create a new user account.

        Args:
            first_name: User's first name.
            last_name: User's last name.
            email: Unique email address.
            password: Plain text password (hashed before storage).
            role: Platform role.
            phone: Optional unique phone number.
            request: FastAPI request (passed through, not used at service level).
            created_by: ID of the admin/staff creating this user.

        Returns:
            Newly created UserModel.

        Raises:
            DuplicateEmailException: When the email is already registered.
            DuplicatePhoneException: When the phone is already registered.
        """
        validate_input_fields(first_name=first_name, last_name=last_name, email=email, password=password)
        validate_email(email)

        await self._check_email_unique(email)
        if phone:
            await self._check_phone_unique(phone)

        user = UserModel.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=hash_password(password),
            role=role,
            phone=phone,
            created_by=created_by,
            updated_by=created_by,
        )
        self.session.add(user)
        return user

    async def list_users(
        self,
        search: str | None,
        role: RoleType | None,
        page: int,
        limit: int,
        sort: UserSortField,
    ) -> tuple[list[UserModel], dict[str, int]]:
        """Return a paginated, optionally filtered list of users.

        Args:
            search: Substring match on first name, last name, or email.
            role: Exact role filter.
            page: 1-indexed page number.
            limit: Page size (capped at 100).
            sort: Column and direction for ordering.

        Returns:
            Tuple of (list of UserModel, pagination meta dict).
        """
        q = select(UserModel)
        count_q = select(func.count()).select_from(UserModel)

        if search:
            pattern = f"%{search}%"
            filter_clause = or_(
                UserModel.first_name.ilike(pattern),
                UserModel.last_name.ilike(pattern),
                UserModel.email.ilike(pattern),
            )
            q = q.where(filter_clause)
            count_q = count_q.where(filter_clause)

        if role:
            q = q.where(UserModel.role == role)
            count_q = count_q.where(UserModel.role == role)

        total = await self.session.scalar(count_q) or 0
        offset = (page - 1) * limit
        q = q.order_by(getattr(UserModel, sort.value)).offset(offset).limit(limit)

        result = await self.session.scalars(q)
        items = list(result.all())
        meta = build_user_page(total, page, limit)
        return items, meta

    async def get_user_by_id(self, user_id: UUID) -> UserModel:
        """Return a single user by UUID.

        Args:
            user_id: UUID of the user to fetch.

        Returns:
            UserModel of the requested user.

        Raises:
            UserNotFoundException: When no user matches the UUID.
        """
        user = await fetch_user(self.session, user_id)
        if user is None:
            raise UserNotFoundException
        return user

    async def update_user(
        self,
        user_id: UUID,
        first_name: str,
        last_name: str,
        email: str,
        phone: str | None,
        role: RoleType,
        is_active: bool,
        updated_by: int | None = None,
    ) -> UserModel:
        """Full replace of user editable fields.

        Args:
            user_id: UUID of the user to update.
            first_name: New first name.
            last_name: New last name.
            email: New email address.
            phone: New phone number (or None to clear).
            role: New role.
            is_active: New active flag.
            updated_by: ID of the staff/admin making the change.

        Returns:
            Updated UserModel.

        Raises:
            UserNotFoundException: When no user matches the UUID.
            DuplicateEmailException: When the new email is already taken.
            DuplicatePhoneException: When the new phone is already taken.
        """
        user = await fetch_user(self.session, user_id)
        if user is None:
            raise UserNotFoundException

        validate_input_fields(first_name=first_name, last_name=last_name, email=email)
        validate_email(email)

        if email != user.email:
            await self._check_email_unique(email)
        if phone != user.phone:
            if phone:
                await self._check_phone_unique(phone)

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone = phone
        user.role = role
        user.is_active = is_active
        user.updated_by = updated_by
        return user

    async def patch_user_status(
        self,
        user_id: UUID,
        is_active: bool,
        updated_by: int | None = None,
    ) -> UserModel:
        """Toggle the active flag on a user account.

        Args:
            user_id: UUID of the user to update.
            is_active: New active flag value.
            updated_by: ID of the staff/admin making the change.

        Returns:
            Updated UserModel.

        Raises:
            UserNotFoundException: When no user matches the UUID.
            SelfDeactivationException: When a user tries to deactivate themselves.
        """
        user = await fetch_user(self.session, user_id)
        if user is None:
            raise UserNotFoundException

        if not is_active and updated_by is not None:
            # Self-deactivation guard: prevent a user from deactivating themselves.
            # created_by on the target holds the FK id of the user who created it.
            if user.created_by == updated_by:
                raise SelfDeactivationException

        user.is_active = is_active
        user.updated_by = updated_by
        return user

    async def delete_user(self, user_id: UUID) -> None:
        """Hard-delete a user record.

        Args:
            user_id: UUID of the user to delete.

        Raises:
            UserNotFoundException: When no user matches the UUID.
        """
        user = await fetch_user(self.session, user_id)
        if user is None:
            raise UserNotFoundException
        await self.session.delete(user)
        await self.session.commit()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _check_email_unique(self, email: str) -> None:
        """Raise DuplicateEmailException when the email is already registered."""
        existing = await self.session.scalar(
            select(UserModel.id).where(UserModel.email == email)
        )
        if existing is not None:
            raise DuplicateEmailException

    async def _check_phone_unique(self, phone: str) -> None:
        """Raise DuplicatePhoneException when the phone is already registered."""
        existing = await self.session.scalar(
            select(UserModel.id).where(UserModel.phone == phone)
        )
        if existing is not None:
            raise DuplicatePhoneException
