"""Returns sync service."""

import json
from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.returns_sync.models import ReturnsSyncModel
from apps.returns_sync.schemas import (
    CreateReturnsSyncRequest,
    CreateReturnsSyncResponse,
    ReturnsSyncResponse,
)
from core.db import db_session
from core.exceptions import AlreadyExistsError, BadRequestError, NotFoundError

SYNC_WINDOW_DAYS = 30


class ReturnsSyncService:
    """Stores and syncs barcode batches pushed by handheld devices."""

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """Initialize the returns sync service.

        Args:
            session: Async database session.
        """
        self.session = session

    async def create_sync(
        self, body: CreateReturnsSyncRequest
    ) -> CreateReturnsSyncResponse:
        """Record a barcode batch pushed by a device.

        Args:
            body: Payload received from the handheld.

        Returns:
            Identifier of the stored sync row.
        """
        await self.session.execute(
            delete(ReturnsSyncModel).where(ReturnsSyncModel.device_id == body.device_id)
        )
        await self.session.commit()

        if not body.barcode.strip():
            raise BadRequestError(message="barcode is required")

        existing = await self.session.scalar(
            select(ReturnsSyncModel).where(ReturnsSyncModel.barcode == body.barcode)
        )
        if existing:
            raise AlreadyExistsError(message="A sync record for this barcode already exists")

        row = ReturnsSyncModel.create(
            barcode=body.barcode,
            device_id=body.device_id,
            payload=json.dumps(body.payload),
            created_by=body.user_id,
        )
        self.session.add(row)
        await self.session.commit()

        return CreateReturnsSyncResponse(
            id=row.id,
            barcode=row.barcode,
            created_at=row.created_at,
        )

    async def list_syncs(self, status: str | None = None) -> list[ReturnsSyncResponse]:
        """List the sync rows with the user that pushed them.

        Args:
            status: Optional status filter.

        Returns:
            Sync rows for the console.
        """
        query = select(ReturnsSyncModel)
        if status:
            query = query.where(ReturnsSyncModel.status == status)

        result = await self.session.execute(query)
        rows = result.scalars().all()

        items: list[ReturnsSyncResponse] = []
        for row in rows:
            creator = await self.session.scalar(
                text("SELECT email FROM users WHERE id = :id"), {"id": row.created_by}
            )
            items.append(
                ReturnsSyncResponse(
                    id=row.id,
                    barcode=row.barcode,
                    device_id=row.device_id,
                    status=row.status,
                    payload=json.loads(row.payload),
                    created_by_email=creator if creator else None,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
            )
        return items

    async def mark_synced(self, sync_ids: list[UUID]) -> int:
        """Mark the given sync rows as synced.

        Args:
            sync_ids: Identifiers of the rows to close.

        Returns:
            Number of rows updated.
        """
        for sync_id in sync_ids:
            row = await self.session.scalar(
                select(ReturnsSyncModel).where(ReturnsSyncModel.id == sync_id)
            )
            if not row:
                raise NotFoundError(message=f"returns sync {sync_id} not found")

        await self.session.execute(
            update(ReturnsSyncModel)
            .where(ReturnsSyncModel.id.in_(sync_ids))
            .values(status="synced", synced_at=datetime.utcnow())
        )
        await self.session.commit()
        return len(sync_ids)

    async def purge_expired(self, days: int = SYNC_WINDOW_DAYS) -> int:
        """Delete sync rows that fell outside the refund window.

        Args:
            days: Age of the rows to remove.

        Returns:
            Number of rows removed.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            text("DELETE FROM returns_sync WHERE created_at < :cutoff"),
            {"cutoff": cutoff},
        )
        return result.rowcount
