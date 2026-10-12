"""User controller."""

import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Query, Request
from starlette import status
from fastapi.responses import JSONResponse

from apps.user.schemas.request import (
    EncryptedRequest,
    ListUsersRequest,
    PatchUserStatusRequest,
    UpdateUserRequest,
)
from apps.user.schemas.response import (
    BaseUserResponse,
    CreateUserResponse,
    CurrentUserResponse,
    TokenPairResponse,
    UserListItemResponse,
    UserPageResponse,
)
from apps.user.services.user import UserService
from constants import SIGNED_OUT, SUCCESSFULLY_DELETED
from core.auth import AdminHasPermission, HasPermission, UserClaims, user_id_from
from core.common_helpers import decrypt
from core.db import db_session
from core.types import RoleType
from core.utils.schema import BaseResponse, PageMeta, SuccessResponse
from core.utils.set_cookies import delete_cookies, set_auth_cookies

router = APIRouter(prefix="/api/user", tags=["User"])


# ------------------------------------------------------------------
# Auth
# ------------------------------------------------------------------


@router.post(
    "/sign-in",
    status_code=status.HTTP_200_OK,
    operation_id="sign_in",
    description="Authenticate a user and return tokens with httpOnly cookies.",
    name="sign_in",
    responses={200: {"model": BaseResponse[TokenPairResponse]}, 401: {"description": "Invalid credentials or inactive account."}},
)
async def sign_in(
    request: Request,
    body: Annotated[EncryptedRequest, Body()],
    service: Annotated[UserService, Depends(db_session)],
) -> JSONResponse:
    """Log in a user and set auth cookies on the response."""
    tokens = await service.login_user(
        request=request,
        encrypted_data=body.encryptedData,
        encrypted_key=body.encryptedKey,
        iv=body.iv,
    )
    response_data = BaseResponse[TokenPairResponse](data=TokenPairResponse(**tokens))
    response = JSONResponse(
        content=json.loads(response_data.model_dump_json()),
        status_code=status.HTTP_200_OK,
    )
    set_auth_cookies(response, tokens["accessToken"], tokens["refreshToken"])
    return response


@router.post(
    "/tokens/refresh",
    status_code=status.HTTP_200_OK,
    operation_id="refresh_tokens",
    description="Validate the refresh cookie and issue a new token pair.",
    name="refresh_tokens",
    responses={200: {"model": BaseResponse[TokenPairResponse]}, 401: {"description": "Invalid or expired refresh token."}},
)
async def refresh_tokens(
    request: Request,
    service: Annotated[UserService, Depends(db_session)],
) -> JSONResponse:
    """Refresh access and refresh tokens using the cookie."""
    from core.auth import refresh as refresh_token_module
    from core.utils.set_cookies import revoke_token

    old_refresh = request.cookies.get("refresh_token", "")
    tokens = await service.refresh_tokens(old_refresh)

    if old_refresh:
        await revoke_token(old_refresh)

    response_data = BaseResponse[TokenPairResponse](data=TokenPairResponse(**tokens))
    response = JSONResponse(
        content=json.loads(response_data.model_dump_json()),
        status_code=status.HTTP_200_OK,
    )
    set_auth_cookies(response, tokens["accessToken"], tokens["refreshToken"])
    return response


@router.post(
    "/sign-out",
    status_code=status.HTTP_200_OK,
    operation_id="sign_out",
    description="Revoke tokens in Redis and clear auth cookies.",
    name="sign_out",
    responses={200: {"model": BaseResponse[SuccessResponse]}},
)
async def sign_out(
    request: Request,
    service: Annotated[UserService, Depends(db_session)],
) -> JSONResponse:
    """Sign out the authenticated user."""
    access_tok = request.cookies.get("access_token", "")
    refresh_tok = request.cookies.get("refresh_token", "")
    await service.sign_out(access_tok, refresh_tok)

    response_data = BaseResponse[SuccessResponse](data=SuccessResponse(message=SIGNED_OUT))
    response = JSONResponse(
        content=json.loads(response_data.model_dump_json()),
        status_code=status.HTTP_200_OK,
    )
    delete_cookies(response)
    return response


# ------------------------------------------------------------------
# Current user
# ------------------------------------------------------------------


@router.get(
    "/self",
    status_code=status.HTTP_200_OK,
    operation_id="get_self",
    description="Return the authenticated user's own profile.",
    name="get_self",
    responses={200: {"model": BaseResponse[CurrentUserResponse]}, 401: {"description": "Not authenticated."}},
)
async def get_self(
    claims: UserClaims,
    service: Annotated[UserService, Depends(db_session)],
) -> BaseResponse[CurrentUserResponse]:
    """Return the current user's full profile."""
    user_id = user_id_from(claims)
    user = await service.get_current_user(user_id)
    return BaseResponse(data=CurrentUserResponse.model_validate(user))


# ------------------------------------------------------------------
# CRUD
# ------------------------------------------------------------------


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_user",
    description="Create a new user account. Admin or Staff only.",
    name="create_user",
    dependencies=[Depends(HasPermission(RoleType.ADMIN, RoleType.STAFF))],
    responses={
        201: {"model": BaseResponse[CreateUserResponse]},
        403: {"description": "Insufficient role."},
        409: {"description": "Email or phone already in use."},
    },
)
async def create_user(
    request: Request,
    body: Annotated[EncryptedRequest, Body()],
    service: Annotated[UserService, Depends(db_session)],
) -> BaseResponse[CreateUserResponse]:
    """Create a new user account (admin/staff only)."""
    payload = decrypt(
        rsa_key=request.app.state.rsa_key,
        enc_data=body.encryptedData,
        encrypt_key=body.encryptedKey,
        iv=body.iv,
        time_check=False,
        timeout=60,
    )
    user = await service.create_user(
        first_name=payload["firstName"],
        last_name=payload["lastName"],
        email=payload["email"],
        password=payload["password"],
        role=payload.get("role", RoleType.USER),
        phone=payload.get("phone"),
        request=request,
    )
    return BaseResponse(data=CreateUserResponse.model_validate(user))


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    operation_id="list_users",
    description="List users with optional search, role filter, and pagination.",
    name="list_users",
    dependencies=[Depends(HasPermission(RoleType.ADMIN, RoleType.STAFF))],
    responses={200: {"model": BaseResponse[UserPageResponse]}},
)
async def list_users(
    request: Annotated[ListUsersRequest, Query()],
    service: Annotated[UserService, Depends(db_session)],
) -> BaseResponse[UserPageResponse]:
    """Return a paginated list of users (admin/staff only)."""
    items, meta = await service.list_users(
        search=request.search,
        role=request.role,
        page=request.page,
        limit=request.limit,
        sort=request.sort,
    )
    return BaseResponse(
        data=UserPageResponse(
            items=[UserListItemResponse.model_validate(u) for u in items],
            meta=PageMeta(**meta),
        )
    )


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    operation_id="get_user",
    description="Return a single user by UUID.",
    name="get_user",
    dependencies=[Depends(HasPermission(RoleType.ADMIN, RoleType.STAFF))],
    responses={200: {"model": BaseResponse[BaseUserResponse]}, 404: {"description": "User not found."}},
)
async def get_user(
    user_id: Annotated[UUID, Path(description="UUID of the user to retrieve")],
    service: Annotated[UserService, Depends(db_session)],
) -> BaseResponse[BaseUserResponse]:
    """Return a single user record."""
    user = await service.get_user_by_id(user_id)
    return BaseResponse(data=BaseUserResponse.model_validate(user))


@router.put(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    operation_id="update_user",
    description="Full replace of user editable fields (admin/staff only).",
    name="update_user",
    dependencies=[Depends(HasPermission(RoleType.ADMIN, RoleType.STAFF))],
    responses={200: {"model": BaseResponse[BaseUserResponse]}, 404: {"description": "User not found."}},
)
async def update_user(
    user_id: Annotated[UUID, Path(description="UUID of the user to update")],
    body: UpdateUserRequest,
    service: Annotated[UserService, Depends(db_session)],
) -> BaseResponse[BaseUserResponse]:
    """Full update of a user record."""
    user = await service.update_user(
        user_id=user_id,
        first_name=body.firstName,
        last_name=body.lastName,
        email=body.email,
        phone=body.phone,
        role=body.role,
        is_active=body.isActive,
    )
    return BaseResponse(data=BaseUserResponse.model_validate(user))


@router.patch(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    operation_id="patch_user_status",
    description="Toggle the active flag on a user account.",
    name="patch_user",
    dependencies=[Depends(HasPermission(RoleType.ADMIN, RoleType.STAFF))],
    responses={200: {"model": BaseResponse[BaseUserResponse]}, 404: {"description": "User not found."}},
)
async def patch_user(
    request: Request,
    user_id: Annotated[UUID, Path(description="UUID of the user to update")],
    body: PatchUserStatusRequest,
    service: Annotated[UserService, Depends(db_session)],
) -> BaseResponse[BaseUserResponse]:
    """Patch the active flag on a user account."""
    caller_id_int: int | None = None
    claims: dict = getattr(request.state, "claims", {})
    if claims:
        caller_uuid = user_id_from(claims)
        # service.session is the raw AsyncSession
        caller_row = await service.session.get(UserModel, caller_uuid)
        if caller_row is not None:
            caller_id_int = caller_row.id
    user = await service.patch_user_status(
        user_id=user_id,
        is_active=body.isActive,
        updated_by=caller_id_int,
    )
    return BaseResponse(data=BaseUserResponse.model_validate(user))


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    operation_id="delete_user",
    description="Permanently delete a user account (admin only).",
    name="delete_user",
    dependencies=[Depends(AdminHasPermission())],
    responses={200: {"model": BaseResponse[SuccessResponse]}, 404: {"description": "User not found."}},
)
async def delete_user(
    user_id: Annotated[UUID, Path(description="UUID of the user to delete")],
    service: Annotated[UserService, Depends(db_session)],
) -> BaseResponse[SuccessResponse]:
    """Delete a user account (admin only)."""
    await service.delete_user(user_id)
    return BaseResponse(data=SuccessResponse(message=SUCCESSFULLY_DELETED))
