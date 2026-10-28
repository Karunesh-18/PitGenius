"""Thin OpenF1 client with a short TTL cache; OpenF1 updates ~every few seconds during sessions."""
import time

import httpx

BASE = "https://api.openf1.org/v1"
_cache: dict[tuple, tuple[float, list]] = {}


def get(endpoint: str, ttl: float = 5.0, **params) -> list[dict]:
    key = (endpoint, tuple(sorted(params.items())))
    hit = _cache.get(key)
    if hit and time.monotonic() - hit[0] < ttl:
        return hit[1]
    try:
        r = httpx.get(f"{BASE}/{endpoint}", params=params, timeout=8)
        data = r.json() if r.status_code == 200 else []
    except Exception:
        data = hit[1] if hit else []  # serve stale on upstream failure
    _cache[key] = (time.monotonic(), data)
    return data if isinstance(data, list) else []
