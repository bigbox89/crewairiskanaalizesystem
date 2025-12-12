"""Prometheus metrics for Arbitr MCP."""

from typing import Optional

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

tool_calls_total = Counter(
    "tool_calls_total",
    "Total tool calls by tool/status/mode",
    labelnames=("tool", "status", "mode"),
)

tool_duration_seconds = Histogram(
    "tool_duration_seconds",
    "Tool execution duration seconds",
    labelnames=("tool", "mode"),
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30),
)


def record_tool_call(tool: str, status: str, mode: str) -> None:
    try:
        tool_calls_total.labels(tool=tool, status=status, mode=mode).inc()
    except Exception:
        pass


def observe_duration(tool: str, mode: str, seconds: float) -> None:
    try:
        tool_duration_seconds.labels(tool=tool, mode=mode).observe(seconds)
    except Exception:
        pass


async def metrics_handler() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


