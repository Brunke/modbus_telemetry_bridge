"""Typed mapping and sample models for Modbus tags."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RegisterType(StrEnum):
    """Supported Modbus register families."""

    HOLDING = "holding"
    INPUT = "input"


@dataclass(frozen=True)
class TagMapping:
    """Static metadata describing how to read and interpret one tag."""

    name: str
    address: int
    count: int
    register_type: RegisterType
    data_type: str
    scaling_factor: float = 1.0
    engineering_unit: str = ""
    enum_values: dict[str, str] = field(default_factory=dict)
    ha_device_id: str | None = None
    ha_component: str = "sensor"
    ha_object_id: str | None = None
    ha_entity_category: str | None = None
    ha_enabled_by_default: bool | None = None
    ha_device_class: str | None = None
    ha_state_class: str | None = None
    ha_command_topic: str | None = None
    ha_options: list[str] = field(default_factory=list)
    ha_payload_on: str | None = None
    ha_payload_off: str | None = None
    ha_min: float | None = None
    ha_max: float | None = None
    ha_step: float | None = None
    ha_mode: str | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> TagMapping:
        """Build a TagMapping instance from one raw config object."""
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
            ha_device_id=(
                str(raw.get("ha", {}).get("device_id"))
                if raw.get("ha", {}).get("device_id") is not None
                else None
            ),
            ha_component=str(raw.get("ha", {}).get("component", "sensor")).strip().lower(),
            ha_object_id=(
                str(raw.get("ha", {}).get("object_id"))
                if raw.get("ha", {}).get("object_id") is not None
                else None
            ),
            ha_entity_category=(
                str(raw.get("ha", {}).get("entity_category"))
                if raw.get("ha", {}).get("entity_category") is not None
                else None
            ),
            ha_enabled_by_default=raw.get("ha", {}).get("enabled_by_default"),
            ha_device_class=(
                str(raw.get("ha", {}).get("device_class"))
                if raw.get("ha", {}).get("device_class") is not None
                else None
            ),
            ha_state_class=(
                str(raw.get("ha", {}).get("state_class"))
                if raw.get("ha", {}).get("state_class") is not None
                else None
            ),
            ha_command_topic=(
                str(raw.get("ha", {}).get("command_topic"))
                if raw.get("ha", {}).get("command_topic") is not None
                else None
            ),
            ha_options=[str(item) for item in raw.get("ha", {}).get("options", [])],
            ha_payload_on=(
                str(raw.get("ha", {}).get("payload_on"))
                if raw.get("ha", {}).get("payload_on") is not None
                else None
            ),
            ha_payload_off=(
                str(raw.get("ha", {}).get("payload_off"))
                if raw.get("ha", {}).get("payload_off") is not None
                else None
            ),
            ha_min=(
                float(raw.get("ha", {}).get("min"))
                if raw.get("ha", {}).get("min") is not None
                else None
            ),
            ha_max=(
                float(raw.get("ha", {}).get("max"))
                if raw.get("ha", {}).get("max") is not None
                else None
            ),
            ha_step=(
                float(raw.get("ha", {}).get("step"))
                if raw.get("ha", {}).get("step") is not None
                else None
            ),
            ha_mode=(
                str(raw.get("ha", {}).get("mode"))
                if raw.get("ha", {}).get("mode") is not None
                else None
            ),
        )


@dataclass(frozen=True)
class TagSample:
    """A measured value paired with its originating tag mapping."""

    mapping: TagMapping
    value: float | int | str

    @property
    def name(self) -> str:
        """Return the display name for the sampled tag."""
        return self.mapping.name

    @property
    def unit(self) -> str:
        """Return the engineering unit declared for the sampled tag."""
        return self.mapping.engineering_unit
