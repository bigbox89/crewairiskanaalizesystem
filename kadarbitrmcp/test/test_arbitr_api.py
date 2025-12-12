"""Tests for Arbitr MCP tools and HTTP client."""

import pathlib
import sys

import httpx
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import reload_settings
from tools import (
    arbitr_search_cases,
    arbitr_details_by_number,
    arbitr_details_by_id,
    arbitr_download_pdf,
)
from tools.arbitr_client import ArbitrApiClient, ArbitrApiError


class MockContext:
    async def info(self, msg):
        return None

    async def error(self, msg):
        return None

    async def report_progress(self, progress, total):
        return None


@pytest.fixture(autouse=True)
def ensure_test_mode(monkeypatch):
    monkeypatch.setenv("ARBITR_MODE", "test")
    reload_settings()
    yield
    reload_settings()


@pytest.fixture
def ctx():
    return MockContext()


@pytest.mark.asyncio
async def test_search_cases_stub(ctx):
    result = await arbitr_search_cases.fn(Inn="РОСНЕФТЬ", ctx=ctx)
    assert result["meta"]["mode"] == "test"
    assert result["structured_content"]["Success"] == 1
    assert result["meta"]["returned"] >= 1


@pytest.mark.asyncio
async def test_details_by_number_stub(ctx):
    result = await arbitr_details_by_number.fn(CaseNumber="А71-1202/2015", ctx=ctx)
    assert result["meta"]["mode"] == "test"
    assert result["structured_content"]["Cases"][0]["CaseNumber"] == "А71-1202/2015"


@pytest.mark.asyncio
async def test_details_by_id_stub(ctx):
    result = await arbitr_details_by_id.fn(CaseId="6fb9afec-b71d-4183-b917-4cace5958c16", ctx=ctx)
    assert result["meta"]["mode"] == "test"
    assert result["structured_content"]["Cases"][0]["CaseId"] == "6fb9afec-b71d-4183-b917-4cace5958c16"


@pytest.mark.asyncio
async def test_download_pdf_stub(ctx):
    result = await arbitr_download_pdf.fn(url="https://kad.arbitr.ru/PdfDocument/test.pdf", ctx=ctx)
    assert result["meta"]["mode"] == "test"
    assert result["meta"]["has_pdf"] is True
    assert result["structured_content"]["Success"] == 1


@pytest.mark.asyncio
async def test_client_success(monkeypatch):
    monkeypatch.setenv("ARBITR_MODE", "prod")
    monkeypatch.setenv("ARBITR_API_KEY", "dummy-key")
    settings = reload_settings()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"Success": 1, "Cases": [], "PagesCount": 1},
        )

    transport = httpx.MockTransport(handler)
    client = ArbitrApiClient(settings, transport=transport)
    data = await client.search_cases(Inn="TEST")
    assert data["Success"] == 1


@pytest.mark.asyncio
async def test_client_handles_403(monkeypatch):
    monkeypatch.setenv("ARBITR_MODE", "prod")
    monkeypatch.setenv("ARBITR_API_KEY", "dummy-key")
    settings = reload_settings()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={"error": "Invalid access key", "error_code": 40301},
        )

    transport = httpx.MockTransport(handler)
    client = ArbitrApiClient(settings, transport=transport)

    with pytest.raises(ArbitrApiError):
        await client.search_cases(Inn="TEST")

