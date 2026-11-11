from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from python_uba_air_data import UBAAirDataClient, records_from_payload


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


class ClientTests(unittest.TestCase):
    def test_build_url_with_params(self) -> None:
        client = UBAAirDataClient(base_url="https://example.com/api/air-data/v4/")
        url = client._build_url("meta/json", {"use": "airquality", "lang": "de"})
        self.assertEqual(url, "https://example.com/api/air-data/v4/meta/json?use=airquality&lang=de")

    @patch("python_uba_air_data.client.urlopen")
    def test_meta_json(self, mocked_urlopen) -> None:
        mocked_urlopen.return_value = _FakeResponse('{"ok": true}')
        client = UBAAirDataClient(base_url="https://example.com/api/air-data/v4")

        payload = client.meta_json(use="airquality", date_from="2026-01-01", date_to="2026-01-02")

        self.assertEqual(payload, {"ok": True})
        request = mocked_urlopen.call_args.args[0]
        self.assertIn("/meta/json?", request.full_url)
        self.assertIn("use=airquality", request.full_url)

    @patch("python_uba_air_data.client.urlopen")
    def test_measures_csv_rows(self, mocked_urlopen) -> None:
        mocked_urlopen.return_value = _FakeResponse("Datum;Messwert\n2026-01-01;8.3\n")
        client = UBAAirDataClient(base_url="https://example.com/api/air-data/v4")

        rows = client.measures_csv_rows({"data[0][st]": 100, "data[0][co]": 1})

        self.assertEqual(rows, [{"Datum": "2026-01-01", "Messwert": "8.3"}])
        request = mocked_urlopen.call_args.args[0]
        self.assertIn("/api/air-data/v2/measures/csv", request.full_url)

    @patch("python_uba_air_data.client.urlopen")
    def test_airquality_json(self, mocked_urlopen) -> None:
        mocked_urlopen.return_value = _FakeResponse('{"indices":["station"],"data":{"0":["A"]}}')
        client = UBAAirDataClient(base_url="https://example.com/api/air-data/v4")

        payload = client.airquality_json(
            date_from="2026-01-01",
            date_to="2026-01-02",
            time_from=1,
            time_to=24,
            lang="en",
        )

        self.assertEqual(payload["indices"], ["station"])
        request = mocked_urlopen.call_args.args[0]
        self.assertIn("/airquality/json?", request.full_url)
        self.assertIn("date_from=2026-01-01", request.full_url)

    @patch("python_uba_air_data.client.urlopen")
    def test_measures_json(self, mocked_urlopen) -> None:
        mocked_urlopen.return_value = _FakeResponse('{"indices":["date end"],"data":{"0":["2026-01-01 12:00:00"]}}')
        client = UBAAirDataClient(base_url="https://example.com/api/air-data/v4")

        payload = client.measures_json(
            date_from="2026-01-01",
            date_to="2026-01-02",
            extra_params={"data[0][st]": 100, "data[0][co]": 1, "data[0][sc]": 1},
        )

        self.assertEqual(payload["indices"], ["date end"])
        request = mocked_urlopen.call_args.args[0]
        self.assertIn("/measures/json?", request.full_url)
        self.assertIn("data%5B0%5D%5Bst%5D=100", request.full_url)


class PayloadTransformTests(unittest.TestCase):
    def test_records_from_payload_dict_data(self) -> None:
        payload = {
            "indices": ["station id", "station name"],
            "data": {"0": [100, "A"]},
        }
        self.assertEqual(records_from_payload(payload), [{"station id": 100, "station name": "A"}])

    def test_records_from_payload_missing_keys(self) -> None:
        self.assertEqual(records_from_payload({"foo": "bar"}), [])


if __name__ == "__main__":
    unittest.main()
