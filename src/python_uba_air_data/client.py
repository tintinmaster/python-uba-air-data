from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from io import StringIO
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from aiohttp import ClientSession

from .auth import Auth
from .models import AirDataTable


DEFAULT_BASE_URL = "https://luftdaten.umweltbundesamt.de/api/air-data/v4"


class UBAAirDataError(RuntimeError):
    """Raised when the UBA Air Data API returns an error or cannot be reached."""


def _request_text_sync(url: str, *, user_agent: str, timeout_seconds: float) -> str:
    request = Request(url, headers={"User-Agent": user_agent})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset)
    except HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise UBAAirDataError(f"HTTP {exc.code} from {url}: {message}") from exc
    except URLError as exc:
        raise UBAAirDataError(f"Request to {url} failed: {exc}") from exc


@dataclass(slots=True)
class UBAAirDataClient:
    """Client for UBA Air Data API v4."""

    base_url: str = DEFAULT_BASE_URL
    timeout_seconds: float = 30.0
    user_agent: str = "uba-air-data/0.1.0"

    def _build_url(self, path: str, params: dict[str, Any] | None = None) -> str:
        cleaned_path = path.lstrip("/")
        base = self.base_url.rstrip("/")
        url = f"{base}/{cleaned_path}" if cleaned_path else base
        if params:
            query = urlencode(params, doseq=True)
            if query:
                url = f"{url}?{query}"
        return url

    def _request_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = self._build_url(path=path, params=params)
        payload = self._request_text(url)
        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise UBAAirDataError(f"Invalid JSON response from {url}: {exc}") from exc

    def _request_text(self, url: str) -> str:
        return _request_text_sync(url, user_agent=self.user_agent, timeout_seconds=self.timeout_seconds)

    def components_json(self, *, lang: str | None = None) -> Any:
        params = {"lang": lang} if lang else None
        return self._request_json("components/json", params=params)

    def scopes_json(self, *, lang: str | None = None) -> Any:
        params = {"lang": lang} if lang else None
        return self._request_json("scopes/json", params=params)

    def stations_json(self, *, lang: str | None = None) -> Any:
        params = {"lang": lang} if lang else None
        return self._request_json("stations/json", params=params)

    def stationtypes_json(self, *, lang: str | None = None) -> Any:
        params = {"lang": lang} if lang else None
        return self._request_json("stationtypes/json", params=params)

    def stationsettings_json(self, *, lang: str | None = None) -> Any:
        params = {"lang": lang} if lang else None
        return self._request_json("stationsettings/json", params=params)

    def meta_json(
        self,
        *,
        use: str,
        date_from: str,
        date_to: str,
        time_from: int | None = None,
        time_to: int | None = None,
        lang: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> Any:
        params: dict[str, Any] = {
            "use": use,
            "date_from": date_from,
            "date_to": date_to,
        }
        if time_from is not None:
            params["time_from"] = time_from
        if time_to is not None:
            params["time_to"] = time_to
        if lang:
            params["lang"] = lang
        if extra_params:
            params.update(extra_params)
        return self._request_json("meta/json", params=params)

    def airquality_json(
        self,
        *,
        date_from: str,
        date_to: str,
        time_from: int | None = None,
        time_to: int | None = None,
        lang: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> Any:
        params: dict[str, Any] = {
            "date_from": date_from,
            "date_to": date_to,
        }
        if time_from is not None:
            params["time_from"] = time_from
        if time_to is not None:
            params["time_to"] = time_to
        if lang:
            params["lang"] = lang
        if extra_params:
            params.update(extra_params)
        return self._request_json("airquality/json", params=params)

    def measures_json(
        self,
        *,
        date_from: str,
        date_to: str,
        time_from: int | None = None,
        time_to: int | None = None,
        lang: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> Any:
        params: dict[str, Any] = {
            "date_from": date_from,
            "date_to": date_to,
        }
        if time_from is not None:
            params["time_from"] = time_from
        if time_to is not None:
            params["time_to"] = time_to
        if lang:
            params["lang"] = lang
        if extra_params:
            params.update(extra_params)
        return self._request_json("measures/json", params=params)

    def measures_csv_text(self, params: dict[str, Any]) -> str:
        if self.base_url.rstrip("/").endswith("/v4"):
            measures_base_url = f"{self.base_url.rstrip('/')[:-3]}/v2/measures/csv"
        else:
            measures_base_url = f"{self.base_url.rstrip('/')}/v2/measures/csv"
        query = urlencode(params, doseq=True)
        url = f"{measures_base_url}?{query}" if query else measures_base_url
        return self._request_text(url)

    def measures_csv_rows(self, params: dict[str, Any], *, delimiter: str = ";") -> list[dict[str, str]]:
        text = self.measures_csv_text(params=params)
        if not text.strip():
            return []
        reader = csv.DictReader(StringIO(text), delimiter=delimiter)
        return [dict(row) for row in reader]


@dataclass(slots=True)
class AsyncUBAAirDataClient:
    """Async client for UBA Air Data API v4."""

    base_url: str = DEFAULT_BASE_URL
    session: ClientSession | None = None
    auth: Auth | None = None
    timeout_seconds: float = 30.0
    user_agent: str = "uba-air-data/0.1.0"

    def _build_url(self, path: str, params: dict[str, Any] | None = None) -> str:
        cleaned_path = path.lstrip("/")
        base = self.base_url.rstrip("/")
        url = f"{base}/{cleaned_path}" if cleaned_path else base
        if params:
            query = urlencode(params, doseq=True)
            if query:
                url = f"{url}?{query}"
        return url

    async def _request_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        payload = await self._request_text(path=path, params=params)
        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            url = self._build_url(path=path, params=params)
            raise UBAAirDataError(f"Invalid JSON response from {url}: {exc}") from exc

    async def _request_text(self, *, path: str, params: dict[str, Any] | None = None) -> str:
        if self.auth is not None:
            request_coro = self.auth.request(
                "GET",
                path,
                params=params,
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout_seconds,
            )
        elif self.session is not None:
            url = self._build_url(path=path, params=params)
            request_coro = self.session.request(
                "GET",
                url,
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout_seconds,
            )
        else:
            raise UBAAirDataError("AsyncUBAAirDataClient requires a ClientSession or an Auth instance.")

        try:
            response = await request_coro
            if hasattr(response, "raise_for_status"):
                response.raise_for_status()
            return await response.text()
        except UBAAirDataError:
            raise
        except Exception as exc:  # pragma: no cover - error type depends on session/auth implementation
            raise UBAAirDataError(f"Request to {url} failed: {exc}") from exc

    async def components_json(self, *, lang: str | None = None) -> Any:
        params = {"lang": lang} if lang else None
        return await self._request_json("components/json", params=params)

    async def scopes_json(self, *, lang: str | None = None) -> Any:
        params = {"lang": lang} if lang else None
        return await self._request_json("scopes/json", params=params)

    async def stations_json(self, *, lang: str | None = None) -> Any:
        params = {"lang": lang} if lang else None
        return await self._request_json("stations/json", params=params)

    async def stationtypes_json(self, *, lang: str | None = None) -> Any:
        params = {"lang": lang} if lang else None
        return await self._request_json("stationtypes/json", params=params)

    async def stationsettings_json(self, *, lang: str | None = None) -> Any:
        params = {"lang": lang} if lang else None
        return await self._request_json("stationsettings/json", params=params)

    async def meta_json(
        self,
        *,
        use: str,
        date_from: str,
        date_to: str,
        time_from: int | None = None,
        time_to: int | None = None,
        lang: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> Any:
        params: dict[str, Any] = {
            "use": use,
            "date_from": date_from,
            "date_to": date_to,
        }
        if time_from is not None:
            params["time_from"] = time_from
        if time_to is not None:
            params["time_to"] = time_to
        if lang:
            params["lang"] = lang
        if extra_params:
            params.update(extra_params)
        return await self._request_json("meta/json", params=params)

    async def airquality_json(
        self,
        *,
        date_from: str,
        date_to: str,
        time_from: int | None = None,
        time_to: int | None = None,
        lang: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> Any:
        params: dict[str, Any] = {
            "date_from": date_from,
            "date_to": date_to,
        }
        if time_from is not None:
            params["time_from"] = time_from
        if time_to is not None:
            params["time_to"] = time_to
        if lang:
            params["lang"] = lang
        if extra_params:
            params.update(extra_params)
        return await self._request_json("airquality/json", params=params)

    async def measures_json(
        self,
        *,
        date_from: str,
        date_to: str,
        time_from: int | None = None,
        time_to: int | None = None,
        lang: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> Any:
        params: dict[str, Any] = {
            "date_from": date_from,
            "date_to": date_to,
        }
        if time_from is not None:
            params["time_from"] = time_from
        if time_to is not None:
            params["time_to"] = time_to
        if lang:
            params["lang"] = lang
        if extra_params:
            params.update(extra_params)
        return await self._request_json("measures/json", params=params)

    async def measures_csv_text(self, params: dict[str, Any]) -> str:
        if self.base_url.rstrip("/").endswith("/v4"):
            measures_base_url = f"{self.base_url.rstrip('/')[:-3]}/v2/measures/csv"
        else:
            measures_base_url = f"{self.base_url.rstrip('/')}/v2/measures/csv"
        query = urlencode(params, doseq=True)
        url = f"{measures_base_url}?{query}" if query else measures_base_url
        if self.auth is not None:
            path = url.split("://", 1)[-1].split("/", 1)[-1]
            return await self._request_text(path=path)
        return await self._request_text(path=url)

    async def measures_csv_rows(self, params: dict[str, Any], *, delimiter: str = ";") -> list[dict[str, str]]:
        text = await self.measures_csv_text(params=params)
        if not text.strip():
            return []
        reader = csv.DictReader(StringIO(text), delimiter=delimiter)
        return [dict(row) for row in reader]

    @staticmethod
    def as_table(payload: dict[str, Any]) -> AirDataTable:
        """Represent `indices`/`data` payloads in a typed data model."""
        return AirDataTable.from_payload(payload)


def records_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert payload with `indices` + `data` into row dictionaries."""
    indices = payload.get("indices")
    data = payload.get("data")
    if not isinstance(indices, list) or data is None:
        return []

    if isinstance(data, dict):
        rows = data.values()
    elif isinstance(data, list):
        rows = data
    else:
        return []

    output: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, list):
            output.append(dict(zip(indices, row)))
    return output
