from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from python_uba_air_data import AsyncUBAAirDataClient, records_from_payload


class _FakeResponse:
    def __init__(self, body: str, charset: str = "utf-8") -> None:
        self._body = body.encode(charset)
        self.headers = SimpleNamespace(get_content_charset=lambda: charset)

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeAsyncResponse:
    def __init__(self, body: str, status: int = 200) -> None:
        self._body = body
        self.status = status

    async def text(self) -> str:
        return self._body

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")

    async def __aenter__(self) -> "_FakeAsyncResponse":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeAsyncSession:
    def __init__(self, body: str, status: int = 200) -> None:
        self._body = body
        self._status = status
        self.calls: list[dict[str, object]] = []

    def get(self, url: str, headers: dict[str, str], timeout: float) -> _FakeAsyncResponse:
        self.calls.append({"url": url, "headers": headers, "timeout": timeout})
        return _FakeAsyncResponse(self._body, status=self._status)


class PayloadTransformTests(unittest.TestCase):
    def test_records_from_payload_dict_data(self) -> None:
        payload = {
            "indices": ["station id", "station name"],
            "data": {"0": [100, "A"]},
        }
        self.assertEqual(records_from_payload(payload), [{"station id": 100, "station name": "A"}])

    def test_records_from_payload_missing_keys(self) -> None:
        self.assertEqual(records_from_payload({"foo": "bar"}), [])


class AsyncClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_airquality_json_uses_injected_session(self) -> None:
        session = _FakeAsyncSession('{"indices":["station"],"data":{"0":["A"]}}')
        client = AsyncUBAAirDataClient(base_url="https://example.com/api/air-data/v4", session=session)

        payload = await client.airquality_json(
            date_from="2026-01-01",
            date_to="2026-01-02",
            time_from=1,
            time_to=24,
            lang="en",
        )

        self.assertEqual(payload["indices"], ["station"])
        self.assertEqual(len(session.calls), 1)
        url = str(session.calls[0]["url"])
        self.assertIn("/airquality/json?", url)
        self.assertIn("date_from=2026-01-01", url)

    async def test_measures_json_keeps_query_shape(self) -> None:
        session = _FakeAsyncSession('{"indices":["date end"],"data":{"0":["2026-01-01 12:00:00"]}}')
        client = AsyncUBAAirDataClient(base_url="https://example.com/api/air-data/v4", session=session)

        payload = await client.measures_json(
            date_from="2026-01-01",
            date_to="2026-01-02",
            extra_params={"data[0][st]": 100, "data[0][co]": 1, "data[0][sc]": 1},
        )

        self.assertEqual(payload["indices"], ["date end"])
        self.assertEqual(len(session.calls), 1)
        url = str(session.calls[0]["url"])
        self.assertIn("/measures/json?", url)
        self.assertIn("data%5B0%5D%5Bst%5D=100", url)


if __name__ == "__main__":
    unittest.main()
