"""User v1 controller — read-only endpoints on a stable contract."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.user.schemas.response import BaseUserResponse, CurrentUserResponse
from apps.user.services.user import UserService
from core.auth import HasPermission, UserClaims, user_id_from
from core.db import db_session
from core.types import RoleType
from core.utils.schema import BaseResponse


router = APIRouter(prefix="/api/v1/user", tags=["User_V1"])


@router.get(
    "/self",
    status_code=status.HTTP_200_OK,
    operation_id="get_self_v1",
    description="Return the authenticated user's own profile on the v1 contract.",
    name="get_self_v1",
    responses={200: {"model": BaseResponse[CurrentUserResponse]}, 401: {"description": "Not authenticated."}},
)
async def get_self(
    claims: UserClaims,
    service: Annotated[UserService, Depends(db_session)],
) -> BaseResponse[CurrentUserResponse]:
    """Return the current user's full profile on v1."""
    user_id = user_id_from(claims)
    user = await service.get_current_user(user_id)
    return BaseResponse(data=CurrentUserResponse.model_validate(user))


@router.get(
    "/{user_id}/permissions",
    status_code=status.HTTP_200_OK,
    operation_id="get_user_permissions_v1",
    description="Return a lightweight permission summary for a user on v1.",
    name="get_user_permissions_v1",
    dependencies=[Depends(HasPermission(RoleType.ADMIN, RoleType.STAFF))],
    responses={200: {"model": BaseResponse[dict]}, 404: {"description": "User not found."}},
)
async def get_user_permissions(
    user_id: Annotated[UUID, Path(description="UUID of the user whose permissions to inspect")],
    service: Annotated[UserService, Depends(db_session)],
) -> BaseResponse[dict]:
    """Return a permission summary for a given user.

    The response shape is intentionally simple — a dict with role and isActive.
    """
    user = await service.get_user_by_id(user_id)
    return BaseResponse(
        data={
            "userId": str(user.id),
            "role": user.role.value,
            "isActive": user.is_active,
        }
    )
