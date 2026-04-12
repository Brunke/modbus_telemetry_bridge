from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RegisterType(StrEnum):
    HOLDING = "holding"
    INPUT = "input"


@dataclass(frozen=True)
class TagMapping:
    name: str
    address: int
    count: int
    register_type: RegisterType
    data_type: str
    scaling_factor: float = 1.0
    engineering_unit: str = ""
    enum_values: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> TagMapping:
        register_type_raw = str(raw["type"]).strip().lower()
        try:
            register_type = RegisterType(register_type_raw)
        except ValueError as exc:
            tag_name = str(raw.get("name", "<unknown>"))
            raise ValueError(
                f"Invalid register type '{register_type_raw}' for tag '{tag_name}'. "
                "Allowed values: 'holding', 'input'."
            ) from exc

        data_type = str(raw.get("sourced_data_type", "uint")).strip().lower()

        return cls(
            name=str(raw["name"]),
            address=int(raw["address"]),
            count=int(raw.get("count", 1)),
            register_type=register_type,
            data_type=data_type,
            scaling_factor=float(raw.get("scaling_factor", 1.0)),
            engineering_unit=str(raw.get("engineering_unit", "")),
            enum_values={str(k): str(v) for k, v in raw.get("enum_values", {}).items()},
        )


@dataclass(frozen=True)
class TagSample:
    mapping: TagMapping
    value: float | int | str

    @property
    def name(self) -> str:
        return self.mapping.name

    @property
    def unit(self) -> str:
        return self.mapping.engineering_unit
