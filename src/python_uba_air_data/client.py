from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from io import StringIO
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://luftdaten.umweltbundesamt.de/api/air-data/v4"


class UBAAirDataError(RuntimeError):
    """Raised when the UBA Air Data API returns an error or cannot be reached."""


@dataclass(slots=True)
class UBAAirDataClient:
    """Client for UBA Air Data API v4."""

    base_url: str = DEFAULT_BASE_URL
    timeout_seconds: float = 30.0
    user_agent: str = "python-uba-air-data/0.1.0"

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
        request = Request(url, headers={"User-Agent": self.user_agent})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset)
        except HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise UBAAirDataError(f"HTTP {exc.code} from {url}: {message}") from exc
        except URLError as exc:
            raise UBAAirDataError(f"Request to {url} failed: {exc}") from exc

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
