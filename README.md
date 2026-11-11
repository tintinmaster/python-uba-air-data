# python-uba-air-data

Small Python client for the Umweltbundesamt (UBA) Air Data API v4.

## Installation

```bash
pip install -e .
```

## Usage

```python
from python_uba_air_data import UBAAirDataClient, records_from_payload

client = UBAAirDataClient()

meta_payload = client.meta_json(
    use="airquality",
    date_from="2026-11-01",
    date_to="2026-11-02",
    time_from=1,
    time_to=24,
    lang="en",
)
rows = records_from_payload(meta_payload)

stations = client.stations_json(lang="en")
components = client.components_json(lang="en")
```

For measurement CSV data (`/api/air-data/v2/measures/csv`), pass query params exactly as defined by the API:

```python
rows = client.measures_csv_rows(
    {
        "data[0][st]": 100,
        "data[0][co]": 1,
        "data[0][sc]": 1,
        "date_from": "2026-11-01",
        "date_to": "2026-11-02",
        "time_from": 1,
        "time_to": 24,
        "lang": "de",
    }
)
```

## Notes

- API docs: https://luftdaten.umweltbundesamt.de/api/air-data/v4/doc
- Source reference: "Umweltbundesamt mit Daten der Messnetze der Länder und des Bundes".
- `records_from_payload` converts payloads using `indices` + `data` into row dictionaries.
