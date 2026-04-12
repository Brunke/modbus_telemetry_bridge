from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class ModbusRTUConfig(BaseModel):
    method: str = "rtu"
    port: str
    baudrate: int = 9600
    parity: str = "N"
    stopbits: int = 1
    bytesize: int = 8
    timeout: float = 1.0
    unit_id: int
    endianness: Literal["BIG", "LITTLE"] = "BIG"


class ModbusTCPConfig(BaseModel):
    host: str
    port: int = 502
    timeout: float = 1.0
    unit_id: int
    endianness: Literal["BIG", "LITTLE"] = "BIG"


class InfluxConfig(BaseModel):
    enabled: bool = True
    url: str
    org: str
    bucket: str
    token: str | None = None
    token_env: str | None = None


class MQTTConfig(BaseModel):
    enabled: bool = False
    host: str = "localhost"
    port: int = 1883
    username: str | None = None
    password: str | None = None
    username_env: str | None = None
    password_env: str | None = None
    node_id: str = "modbus_bridge"
    device_name: str = "Modbus Bridge"
    manufacturer: str = "Custom"
    model: str = "Modbus Mapping"
    discovery_prefix: str = "homeassistant"
    state_prefix: str = "modbus_telemetry"
    entity_overrides: dict[str, dict[str, Any]] = Field(default_factory=dict)


class TagConfig(BaseModel):
    name: str
    address: int
    count: int = 1
    type: Literal["holding", "input"]
    engineering_unit: str = ""
    sourced_data_type: str = "uint"
    scaling_factor: float = 1.0
    enum_values: dict[str, str] = Field(default_factory=dict)


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    modbusRTU: ModbusRTUConfig | None = None
    modbusTCP: ModbusTCPConfig | None = None
    poll_interval: float = 3.0
    span_gaps: bool = False
    maximum_read_length: int = 64
    influxdb: InfluxConfig | None = None
    mqtt: MQTTConfig | None = None
    tags: list[TagConfig]

    @model_validator(mode="after")
    def validate_modbus_endpoint(self) -> AppConfig:
        if self.modbusRTU is None and self.modbusTCP is None:
            raise ValueError("One of modbusRTU or modbusTCP is required")
        if self.modbusRTU is not None and self.modbusTCP is not None:
            raise ValueError("Only one of modbusRTU or modbusTCP should be configured")
        return self


def validate_config_dict(data: dict[str, Any]) -> None:
    AppConfig.model_validate(data)


def format_validation_error(error: ValidationError) -> str:
    return error.json(indent=2)
