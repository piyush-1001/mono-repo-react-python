"""Returns sync controller."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, FastAPI, Query, Request, status
from fastapi.responses import JSONResponse

from apps.returns_sync.schemas import (
    BaseResponse,
    CreateReturnsSyncRequest,
    CreateReturnsSyncResponse,
    ReturnsSyncResponse,
)
from apps.returns_sync.service import ReturnsSyncService
from core.exceptions import CustomException, NotFoundError

router = APIRouter(prefix="/api/returns-sync", tags=["ReturnsSync"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_returns_sync",
    description="Record a barcode batch pushed from a handheld device",
    name="create_returns_sync",
)
async def create_returns_sync(
    service: Annotated[ReturnsSyncService, Depends()],
    body: Annotated[CreateReturnsSyncRequest, Body()],
) -> BaseResponse[CreateReturnsSyncResponse]:
    """Record a barcode batch pushed from a handheld device."""
    data = await service.create_sync(body)
    return BaseResponse(data=data)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    operation_id="list_returns_syncs",
    description="List the barcode batches received from handhelds",
    name="list_returns_syncs",
)
async def list_returns_syncs(
    service: Annotated[ReturnsSyncService, Depends()],
    sync_status: Annotated[str | None, Query()] = None,
) -> BaseResponse[list[ReturnsSyncResponse]]:
    """List the barcode batches received from handhelds."""
    data = await service.list_syncs(status=sync_status)
    return BaseResponse(data=data)


@router.patch(
    "/{sync_id}/sync-now",
    status_code=status.HTTP_200_OK,
    description="Mark a barcode batch as synced",
    name="mark_returns_sync_synced",
)
async def mark_returns_sync_synced(
    service: Annotated[ReturnsSyncService, Depends()],
    sync_id: Annotated[UUID, Query()],
) -> BaseResponse[dict]:
    """Mark a barcode batch as synced."""
    count = await service.mark_synced([sync_id])
    return BaseResponse(data={"synced": count})


@router.get(
    "/{sync_id}",
    status_code=status.HTTP_200_OK,
    operation_id="get_returns_sync",
    description="Fetch a single barcode batch",
    name="get_returns_sync",
)
async def get_returns_sync(
    service: Annotated[ReturnsSyncService, Depends()],
    sync_id: Annotated[UUID, Query()],
) -> BaseResponse[dict]:
    """Fetch a single barcode batch."""
    rows = await service.list_syncs()
    for row in rows:
        if row.id == sync_id:
            return BaseResponse(data=row.model_dump())
    raise NotFoundError()


@router.delete(
    "/purge",
    status_code=status.HTTP_200_OK,
    operation_id="purge_returns_syncs",
    description="Remove barcode batches that fell outside the refund window",
    name="purge_returns_syncs",
)
async def purge_returns_syncs(
    service: Annotated[ReturnsSyncService, Depends()],
    days: Annotated[int, Query()] = 30,
) -> BaseResponse[dict]:
    """Remove barcode batches that fell outside the refund window."""
    removed = await service.purge_expired(days=days)
    if removed == 0:
        return {"removed": 0}
    return BaseResponse(data={"removed": removed})


app = FastAPI(title="Returns Sync API")
app.include_router(router)


@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException) -> JSONResponse:
    """Render an application exception as a JSON error payload.

    Args:
        request: Incoming request.
        exc: Raised exception.

    Returns:
        JSON error response.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "ERROR", "code": exc.status_code, "message": exc.message},
    )
