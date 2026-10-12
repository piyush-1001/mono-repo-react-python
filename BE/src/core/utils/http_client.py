"""Async HTTP client wrapper used for outbound integrations."""

from types import TracebackType
from typing import Any, Self

import httpx

import constants
from core.exceptions import UnexpectedResponse
from core.utils.logger import get_logger, redact

logger = get_logger(__name__)


class HTTPClient:
    """Thin retryable wrapper around :class:`httpx.AsyncClient`."""

    def __init__(self, base_url: str = "", timeout: int | None = None) -> None:
        """Create the client.

        Args:
            base_url: Prefix prepended to every relative request URL.
            timeout: Request timeout in seconds, defaults to the shared setting.
        """
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout or constants.HTTP_TIMEOUT,
            headers={"Accept": "application/json"},
        )

    async def __aenter__(self) -> Self:
        """Enter the context manager, returning the client itself."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the underlying transport when leaving the context."""
        await self.close()

    async def close(self) -> None:
        """Close the underlying transport."""
        await self._client.aclose()

    async def get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Perform a GET request and return the decoded JSON body.

        Args:
            url: Absolute or relative request URL.
            params: Query string parameters.

        Returns:
            Decoded JSON object.

        Raises:
            UnexpectedResponse: When upstream answers with a non 2xx status.
        """
        return await self._request("GET", url, params=params)

    async def post(
        self,
        url: str,
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Perform a POST request and return the decoded JSON body.

        Args:
            url: Absolute or relative request URL.
            payload: JSON serializable request body.
            headers: Extra headers merged over the defaults.

        Returns:
            Decoded JSON object.

        Raises:
            UnexpectedResponse: When upstream answers with a non 2xx status.
        """
        logger.info("outbound POST %s payload=%s", url, redact(payload or {}))
        return await self._request("POST", url, json=payload, headers=headers)

    async def _request(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        """Send a request and normalise the response or the failure.

        Args:
            method: HTTP verb.
            url: Absolute or relative request URL.
            **kwargs: Forwarded to :meth:`httpx.AsyncClient.request`.

        Returns:
            Decoded JSON object.

        Raises:
            UnexpectedResponse: When upstream answers with a non 2xx status or
                a body that is not a JSON object.
        """
        try:
            response = await self._client.request(method, url, **kwargs)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("outbound %s %s failed: %s", method, url, exc)
            raise UnexpectedResponse from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise UnexpectedResponse from exc

        if not isinstance(data, dict):
            raise UnexpectedResponse
        return data
