from __future__ import annotations

from dataclasses import dataclass
from typing import Any


AirDataTable = dict[str, Any]


@dataclass
class AirDataTable:
    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> AirDataTable:
        return cls(
            indices=payload.get("indices", []),
            data=payload.get("data", []),
        )

    indices: list[Any]
    data: list[Any]
