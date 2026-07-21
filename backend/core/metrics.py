import time

from fastapi import Request, Response
from fastapi.routing import APIRoute

from backend.core.logging import get_logger

logger = get_logger(__name__)

REQUEST_COUNT = 0
REQUEST_DURATIONS: list[float] = []


class MetricsRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handler(request: Request) -> Response:
            global REQUEST_COUNT
            REQUEST_COUNT += 1
            start = time.perf_counter()
            response = await original(request)
            duration = time.perf_counter() - start
            REQUEST_DURATIONS.append(duration)
            if len(REQUEST_DURATIONS) > 1000:
                REQUEST_DURATIONS.pop(0)
            return response

        return handler


def get_metrics() -> dict:
    global REQUEST_COUNT, REQUEST_DURATIONS
    avg_duration = 0.0
    if REQUEST_DURATIONS:
        avg_duration = sum(REQUEST_DURATIONS) / len(REQUEST_DURATIONS)
    return {
        "request_count": REQUEST_COUNT,
        "average_duration_ms": round(avg_duration * 1000, 2),
        "total_duration_seconds": round(sum(REQUEST_DURATIONS), 2),
    }
