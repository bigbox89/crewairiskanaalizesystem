"""HTTP client for api-assist.com arbitr endpoints."""

from typing import Any, Dict, Optional

import httpx

from config import Settings


class ArbitrApiError(Exception):
    """Raised when API returns error or invalid payload."""

    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class ArbitrApiClient:
    def __init__(self, settings: Settings, transport: Optional[httpx.AsyncBaseTransport] = None):
        self.settings = settings
        self.transport = transport

    async def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if self.settings.mode == "prod" and not self.settings.api_key:
            raise ArbitrApiError("ARBITR_API_KEY is required for prod mode")

        query = {"key": self.settings.api_key}
        query.update({k: v for k, v in params.items() if v is not None})

        url = f"{self.settings.base_url}/{path}"

        async with httpx.AsyncClient(timeout=self.settings.timeout, transport=self.transport) as client:
            response = await client.get(url, params=query)

        if response.status_code in (400, 403):
            payload = response.json()
            raise ArbitrApiError(
                payload.get("error", "Request validation or auth error"),
                status_code=response.status_code,
                error_code=payload.get("error_code"),
            )

        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and data.get("Success") == 1:
            return data

        if isinstance(data, dict) and "error" in data:
            raise ArbitrApiError(data.get("error", "Unknown API error"), error_code=data.get("error_code"))

        raise ArbitrApiError("Unexpected API response format")

    async def search_cases(self, **params: Any) -> Dict[str, Any]:
        return await self._get("search", params)

    async def details_by_number(self, case_number: str) -> Dict[str, Any]:
        return await self._get("details_by_number", {"CaseNumber": case_number})

    async def details_by_id(self, case_id: str) -> Dict[str, Any]:
        return await self._get("details_by_id", {"CaseId": case_id})

    async def download_pdf(self, url: str) -> Dict[str, Any]:
        return await self._get("pdf_download", {"url": url})


