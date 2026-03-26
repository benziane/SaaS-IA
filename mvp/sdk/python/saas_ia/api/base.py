"""BaseAPI — shared async HTTP helper used by every module API class."""

from __future__ import annotations

from typing import Any

import httpx

from saas_ia.exceptions import SaaSIAError


class BaseAPI:
    """Thin wrapper around an ``httpx.AsyncClient`` that handles auth headers,
    JSON (de)serialisation and error normalisation.

    Concrete API classes inherit from this and only declare endpoint methods.
    """

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    # -- HTTP primitives ----------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        data: Any | None = None,
        files: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        # Strip None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.request(
            method,
            path,
            json=json,
            data=data,
            files=files,
            params=params,
        )

        if response.status_code >= 400:
            try:
                body = response.json()
                detail = body.get("detail", response.reason_phrase)
            except Exception:
                detail = response.reason_phrase or str(response.status_code)
            raise SaaSIAError(response.status_code, detail)

        if response.status_code == 204:
            return None

        return response.json()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def _post(
        self,
        path: str,
        json: Any | None = None,
        *,
        data: Any | None = None,
        files: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return await self._request(
            "POST", path, json=json, data=data, files=files, params=params
        )

    async def _put(self, path: str, json: Any | None = None) -> Any:
        return await self._request("PUT", path, json=json)

    async def _patch(self, path: str, json: Any | None = None) -> Any:
        return await self._request("PATCH", path, json=json)

    async def _delete(self, path: str) -> Any:
        return await self._request("DELETE", path)
