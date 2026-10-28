"""Thin client for the Jolpica F1 API (Ergast-compatible historical F1 data).

Jolpica is the community-run replacement for the now-deprecated Ergast
API and speaks the same response shape, so this client mirrors the
classic Ergast endpoint structure: /{season}/..., MRData -> *Table -> list.
"""
from __future__ import annotations

import time
from typing import Any

import requests

PAGE_LIMIT = 100
MAX_RETRIES = 5
RETRY_BACKOFF_S = 3.0
MIN_REQUEST_INTERVAL_S = 0.8  # free tier: bursts get 429, so stay well under the limit


class JolpicaClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < MIN_REQUEST_INTERVAL_S:
            time.sleep(MIN_REQUEST_INTERVAL_S - elapsed)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        url = f"{self.base_url}/{path.lstrip('/')}"
        last_exc: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            self._throttle()
            try:
                resp = self._session.get(url, params=params, timeout=30)
                self._last_request_at = time.monotonic()
                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("Retry-After", RETRY_BACKOFF_S * attempt))
                    time.sleep(retry_after)
                    last_exc = requests.exceptions.HTTPError("429 Too Many Requests", response=resp)
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as exc:
                last_exc = exc
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_S * attempt)
        raise RuntimeError(f"Jolpica request failed after {MAX_RETRIES} attempts: {url}") from last_exc

    def _get_all_pages(self, path: str, table_key: str, list_key: str) -> list[dict]:
        """Follow MRData pagination (limit/offset/total) until exhausted."""
        offset = 0
        items: list[dict] = []
        while True:
            data = self._get(path, params={"limit": PAGE_LIMIT, "offset": offset})
            mrdata = data["MRData"]
            table = mrdata[table_key]
            page_items = table[list_key]
            items.extend(page_items)
            total = int(mrdata["total"])
            offset += len(page_items)
            if offset >= total or not page_items:
                break
        return items

    def get_season_races(self, season: int) -> list[dict]:
        """Season schedule: rounds, circuits, dates."""
        return self._get_all_pages(f"{season}.json", "RaceTable", "Races")

    def get_drivers(self, season: int) -> list[dict]:
        return self._get_all_pages(f"{season}/drivers.json", "DriverTable", "Drivers")

    def get_constructors(self, season: int) -> list[dict]:
        return self._get_all_pages(f"{season}/constructors.json", "ConstructorTable", "Constructors")

    def get_results(self, season: int, round_: int | None = None) -> list[dict]:
        """Races with nested Results (grid, finish position, status, points)."""
        path = f"{season}/{round_}/results.json" if round_ else f"{season}/results.json"
        return self._get_all_pages(path, "RaceTable", "Races")

    def get_qualifying(self, season: int, round_: int | None = None) -> list[dict]:
        path = f"{season}/{round_}/qualifying.json" if round_ else f"{season}/qualifying.json"
        return self._get_all_pages(path, "RaceTable", "Races")

    def get_driver_standings(self, season: int, round_: int | None = None) -> list[dict]:
        path = f"{season}/{round_}/driverStandings.json" if round_ else f"{season}/driverStandings.json"
        data = self._get(path, params={"limit": PAGE_LIMIT})
        lists = data["MRData"]["StandingsTable"]["StandingsLists"]
        return lists[0]["DriverStandings"] if lists else []

    def get_constructor_standings(self, season: int, round_: int | None = None) -> list[dict]:
        path = (
            f"{season}/{round_}/constructorStandings.json" if round_ else f"{season}/constructorStandings.json"
        )
        data = self._get(path, params={"limit": PAGE_LIMIT})
        lists = data["MRData"]["StandingsTable"]["StandingsLists"]
        return lists[0]["ConstructorStandings"] if lists else []
