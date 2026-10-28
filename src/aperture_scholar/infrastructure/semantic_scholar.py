"""Read-only metadata search: bounded retry, rate limiting and persistent cache."""

import hashlib
import json
import time
from collections.abc import Callable

import httpx
from pydantic import ValidationError

from aperture_scholar.application.ports import ResponseCache
from aperture_scholar.config import ScholarSettings
from aperture_scholar.domain.errors import ProviderError
from aperture_scholar.domain.models import Paper


class SemanticScholarSource:
    """Single-worker adapter. Inject one instance per worker; share only the cache."""

    def __init__(
        self,
        client: httpx.Client,
        cache: ResponseCache,
        settings: ScholarSettings,
        *,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.client, self.cache, self.settings = client, cache, settings
        self.sleep, self.clock = sleep, clock
        self._next_request = 0.0

    def search(self, query: str, limit: int) -> list[Paper]:
        if not query.strip() or not 1 <= limit <= 100:
            raise ValueError("query required; search limit must be between 1 and 100")
        params = {
            "query": query.strip(),
            "limit": str(limit),
            "fields": "title,abstract,year,url,externalIds",
        }
        url = self.settings.base_url.rstrip("/") + "/paper/search"
        key = hashlib.sha256(json.dumps([url, params], sort_keys=True).encode()).hexdigest()
        cached = self.cache.get(key)
        if cached is not None:
            return self._parse(cached)
        headers = {}
        if self.settings.api_key and self.settings.api_key.get_secret_value():
            headers["x-api-key"] = self.settings.api_key.get_secret_value()
        for attempt in range(self.settings.max_attempts):
            self.sleep(max(0, self._next_request - self.clock()))
            self._next_request = self.clock() + 1 / self.settings.requests_per_second
            try:
                response = self.client.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.settings.timeout_seconds,
                )
            except httpx.TransportError as error:
                if attempt + 1 == self.settings.max_attempts:
                    raise ProviderError("metadata transport failed after bounded retry") from error
                self.sleep(2.0**attempt)
                continue
            if response.status_code == 429 or response.status_code >= 500:
                if attempt + 1 == self.settings.max_attempts:
                    raise ProviderError(
                        f"metadata service unavailable: HTTP {response.status_code}"
                    )
                # Bounded delay; date-form Retry-After falls back to exponential delay.
                try:
                    delay = float(response.headers.get("Retry-After", 2.0**attempt))
                except ValueError:
                    delay = 2.0**attempt
                self.sleep(min(60.0, max(0.0, delay)))
                continue
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                raise ProviderError(
                    f"metadata request rejected: HTTP {response.status_code}"
                ) from error
            papers = self._parse(response.text)
            self.cache.put(key, response.text, self.settings.cache_ttl_seconds)
            return papers
        raise AssertionError("unreachable")

    @staticmethod
    def _parse(payload: str) -> list[Paper]:
        try:
            data = json.loads(payload)
            rows = data["data"]
            if not isinstance(rows, list):
                raise TypeError("data must be a list")
            return [
                Paper(
                    id=row["paperId"],
                    title=row["title"],
                    abstract=row.get("abstract") or "",
                    year=row.get("year"),
                    url=row.get("url"),
                    doi=(row.get("externalIds") or {}).get("DOI"),
                )
                for row in rows
            ]
        except (ValueError, KeyError, TypeError, AttributeError, ValidationError) as error:
            raise ProviderError("invalid metadata response") from error
