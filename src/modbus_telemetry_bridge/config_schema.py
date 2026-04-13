"""Pydantic configuration schema for the telemetry bridge."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class ModbusRTUConfig(BaseModel):
    """Configuration for Modbus RTU/ASCII serial transport."""

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
    """Configuration for Modbus TCP transport."""

    host: str
    port: int = 502
    timeout: float = 1.0
    unit_id: int
    endianness: Literal["BIG", "LITTLE"] = "BIG"


class InfluxConfig(BaseModel):
    """Configuration for InfluxDB output sink."""

    enabled: bool = True
    url: str
    org: str
    bucket: str
    token: str | None = None
    token_env: str | None = None


class HAOriginConfig(BaseModel):
    """Metadata describing the software that publishes discovery payloads."""

    name: str = "modbus-telemetry-bridge"
    sw_version: str | None = None
    support_url: str | None = None


class MQTTConfig(BaseModel):
    """Configuration for MQTT output and Home Assistant discovery."""

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
    origin: HAOriginConfig | None = None
    entity_overrides: dict[str, dict[str, Any]] = Field(default_factory=dict)
    devices: dict[str, HADeviceConfig] = Field(default_factory=dict)


class HADeviceConfig(BaseModel):
    """Home Assistant discovery device metadata overrides."""

    name: str
    manufacturer: str | None = None
    model: str | None = None
    sw_version: str | None = None
    hw_version: str | None = None
    via_device: str | None = None
    identifiers: list[str] | None = None


HASensorDeviceClass = Literal[
    "absolute_humidity",
    "aqi",
    "apparent_power",
    "area",
    "atmospheric_pressure",
    "battery",
    "blood_glucose_concentration",
    "co",
    "co2",
    "conductivity",
    "current",
    "data_rate",
    "data_size",
    "date",
    "distance",
    "duration",
    "energy",
    "energy_distance",
    "energy_storage",
    "enum",
    "frequency",
    "gas",
    "humidity",
    "illuminance",
    "irradiance",
    "moisture",
    "monetary",
    "nitrogen_dioxide",
    "nitrogen_monoxide",
    "nitrous_oxide",
    "ozone",
    "ph",
    "pm1",
    "pm10",
    "pm25",
    "pm4",
    "power",
    "power_factor",
    "precipitation",
    "precipitation_intensity",
    "pressure",
    "reactive_energy",
    "reactive_power",
    "signal_strength",
    "sound_pressure",
    "speed",
    "sulphur_dioxide",
    "temperature",
    "temperature_delta",
    "timestamp",
    "volatile_organic_compounds",
    "volatile_organic_compounds_parts",
    "voltage",
    "volume",
    "volume_flow_rate",
    "volume_storage",
    "water",
    "weight",
    "wind_direction",
    "wind_speed",
]

HASensorStateClass = Literal[
    "measurement",
    "measurement_angle",
    "total",
    "total_increasing",
]

_NO_UNIT = "<none>"

_HA_SENSOR_ALLOWED_UNITS_BY_DEVICE_CLASS: dict[str, set[str]] = {
    "absolute_humidity": {"g/m\u00b3", "mg/m\u00b3"},
    "aqi": {_NO_UNIT},
    "apparent_power": {"mVA", "VA", "kVA"},
    "area": {
        "m\u00b2",
        "cm\u00b2",
        "km\u00b2",
        "mm\u00b2",
        "in\u00b2",
        "ft\u00b2",
        "yd\u00b2",
        "mi\u00b2",
        "ac",
        "ha",
    },
    "atmospheric_pressure": {
        "cbar",
        "bar",
        "hPa",
        "mmHg",
        "mmHG",
        "inHg",
        "inH\u2082O",
        "kPa",
        "mbar",
        "Pa",
        "psi",
    },
    "battery": {"%"},
    "blood_glucose_concentration": {"mg/dL", "mmol/L"},
    "co": {"ppb", "ppm", "\u00b5g/m\u00b3", "mg/m\u00b3"},
    "co2": {"ppm"},
    "conductivity": {"S/cm", "mS/cm", "\u00b5S/cm"},
    "current": {"A", "mA", "\u00b5A"},
    "data_rate": {
        "bit/s",
        "kbit/s",
        "Mbit/s",
        "Gbit/s",
        "B/s",
        "kB/s",
        "MB/s",
        "GB/s",
        "KiB/s",
        "MiB/s",
        "GiB/s",
    },
    "data_size": {
        "bit",
        "kbit",
        "Mbit",
        "Gbit",
        "B",
        "kB",
        "MB",
        "GB",
        "TB",
        "PB",
        "EB",
        "ZB",
        "YB",
        "KiB",
        "MiB",
        "GiB",
        "TiB",
        "PiB",
        "EiB",
        "ZiB",
        "YiB",
    },
    "date": {_NO_UNIT},
    "distance": {"km", "m", "cm", "mm", "mi", "nmi", "yd", "in"},
    "duration": {"d", "h", "min", "s", "ms", "\u00b5s"},
    "energy": {
        "J",
        "kJ",
        "MJ",
        "GJ",
        "mWh",
        "Wh",
        "kWh",
        "MWh",
        "GWh",
        "TWh",
        "cal",
        "kcal",
        "Mcal",
        "Gcal",
    },
    "energy_distance": {"kWh/100km", "Wh/km", "mi/kWh", "km/kWh"},
    "energy_storage": {
        "J",
        "kJ",
        "MJ",
        "GJ",
        "mWh",
        "Wh",
        "kWh",
        "MWh",
        "GWh",
        "TWh",
        "cal",
        "kcal",
        "Mcal",
        "Gcal",
    },
    "enum": {_NO_UNIT},
    "frequency": {"mHz", "Hz", "kHz", "MHz", "GHz"},
    "gas": {"L", "m\u00b3", "ft\u00b3", "CCF", "MCF"},
    "humidity": {"%"},
    "illuminance": {"lx"},
    "irradiance": {"W/m\u00b2", "BTU/(h\u22c5ft\u00b2)"},
    "moisture": {"%"},
    "monetary": {_NO_UNIT},
    "nitrogen_dioxide": {"ppb", "ppm", "\u00b5g/m\u00b3"},
    "nitrogen_monoxide": {"ppb", "\u00b5g/m\u00b3"},
    "nitrous_oxide": {"\u00b5g/m\u00b3"},
    "ozone": {"ppb", "ppm", "\u00b5g/m\u00b3"},
    "ph": {_NO_UNIT},
    "pm1": {"\u00b5g/m\u00b3"},
    "pm10": {"\u00b5g/m\u00b3"},
    "pm25": {"\u00b5g/m\u00b3"},
    "pm4": {"\u00b5g/m\u00b3"},
    "power": {"mW", "W", "kW", "MW", "GW", "TW"},
    "power_factor": {"%", _NO_UNIT},
    "precipitation": {"cm", "in", "mm"},
    "precipitation_intensity": {"in/d", "in/h", "mm/d", "mm/h"},
    "pressure": {"cbar", "bar", "hPa", "mmHg", "inHg", "kPa", "mbar", "Pa", "psi", "mPa"},
    "reactive_energy": {"varh", "kvarh"},
    "reactive_power": {"mvar", "var", "kvar"},
    "signal_strength": {"dB", "dBm"},
    "sound_pressure": {"dB", "dBA"},
    "speed": {"ft/s", "in/d", "in/h", "in/s", "km/h", "kn", "m/s", "mph", "mm/d", "mm/s"},
    "sulphur_dioxide": {"ppb", "\u00b5g/m\u00b3"},
    "temperature": {"\u00b0C", "\u00b0F", "K"},
    "temperature_delta": {"\u00b0C", "\u00b0F", "K"},
    "timestamp": {_NO_UNIT},
    "volatile_organic_compounds": {"\u00b5g/m\u00b3", "mg/m\u00b3"},
    "volatile_organic_compounds_parts": {"ppm", "ppb"},
    "voltage": {"V", "mV", "\u00b5V", "kV", "MV"},
    "volume": {"L", "mL", "gal", "fl. oz.", "m\u00b3", "ft\u00b3", "CCF", "MCF"},
    "volume_flow_rate": {
        "m\u00b3/h",
        "m\u00b3/min",
        "m\u00b3/s",
        "ft\u00b3/min",
        "L/h",
        "L/min",
        "L/s",
        "gal/d",
        "gal/h",
        "gal/min",
        "mL/s",
    },
    "volume_storage": {"L", "mL", "gal", "fl. oz.", "m\u00b3", "ft\u00b3", "CCF", "MCF"},
    "water": {"L", "gal", "m\u00b3", "ft\u00b3", "CCF", "MCF"},
    "weight": {"kg", "g", "mg", "\u00b5g", "oz", "lb", "st"},
    "wind_direction": {"\u00b0"},
    "wind_speed": {"ft/s", "km/h", "kn", "m/s", "mph"},
}


class HATagConfig(BaseModel):
    """Home Assistant metadata overrides attached to an individual tag."""

    device_id: str | None = None
    component: Literal["sensor", "binary_sensor", "number", "select"] = "sensor"
    object_id: str | None = None
    entity_category: Literal["config", "diagnostic"] | None = None
    enabled_by_default: bool | None = None
    device_class: str | None = None
    state_class: HASensorStateClass | None = None
    command_topic: str | None = None
    options: list[str] | None = None
    payload_on: str | None = None
    payload_off: str | None = None
    min: float | None = None
    max: float | None = None
    step: float | None = None
    mode: Literal["auto", "box", "slider"] | None = None


class TagConfig(BaseModel):
    """One tag definition describing where and how to read a value."""

    name: str
    address: int
    count: int = 1
    type: Literal["holding", "input"]
    engineering_unit: str = ""
    sourced_data_type: str = "uint"
    scaling_factor: float = 1.0
    enum_values: dict[str, str] = Field(default_factory=dict)
    ha: HATagConfig | None = None

    @model_validator(mode="after")
    def validate_ha_sensor_units(self) -> TagConfig:
        """Validate engineering_unit compatibility with selected HA sensor device_class."""
        if self.ha is None:
            return self

        if self.ha.component == "sensor" and self.ha.entity_category == "config":
            raise ValueError(
                f"Tag '{self.name}' uses entity_category 'config' for sensor component, "
                "but Home Assistant MQTT sensors only allow 'diagnostic'."
            )

        if self.ha.component != "sensor" and self.ha.state_class is not None:
            raise ValueError(
                f"Tag '{self.name}' sets ha.state_class for component '{self.ha.component}'. "
                "state_class is only valid for sensor components."
            )

        if self.ha.component == "number" and not self.ha.command_topic:
            raise ValueError(
                f"Tag '{self.name}' sets component 'number' but does not define ha.command_topic."
            )

        if self.ha.component == "select":
            if not self.ha.command_topic:
                raise ValueError(
                    f"Tag '{self.name}' sets component 'select' but does not define "
                    "ha.command_topic."
                )
            if self.ha.options is None:
                raise ValueError(
                    f"Tag '{self.name}' sets component 'select' but does not define ha.options."
                )

        if self.ha.component != "sensor" or self.ha.device_class is None:
            return self

        if self.ha.device_class not in _HA_SENSOR_ALLOWED_UNITS_BY_DEVICE_CLASS:
            allowed = ", ".join(sorted(_HA_SENSOR_ALLOWED_UNITS_BY_DEVICE_CLASS))
            raise ValueError(
                f"Tag '{self.name}' has unsupported sensor device_class '{self.ha.device_class}'. "
                f"Allowed values: {allowed}"
            )

        allowed_units = _HA_SENSOR_ALLOWED_UNITS_BY_DEVICE_CLASS.get(self.ha.device_class)
        if not allowed_units:
            return self

        if self.ha.device_class == "enum" and self.ha.state_class is not None:
            raise ValueError(
                f"Tag '{self.name}' uses sensor device_class 'enum' but also sets "
                "ha.state_class, which is not allowed for enum sensors."
            )

        if self.ha.device_class == "enum" and not self.enum_values and not self.ha.options:
            raise ValueError(
                f"Tag '{self.name}' uses sensor device_class 'enum' "
                "but defines neither enum_values nor ha.options."
            )

        raw_unit = self.engineering_unit.strip()
        normalized_unit = _NO_UNIT if raw_unit == "" or raw_unit.lower() == "none" else raw_unit
        if normalized_unit in allowed_units:
            return self

        readable_units = sorted(unit for unit in allowed_units if unit != _NO_UNIT)
        if _NO_UNIT in allowed_units:
            readable_units.append("(no unit)")

        raise ValueError(
            f"Tag '{self.name}' has engineering_unit '{self.engineering_unit}' which is not valid "
            f"for HA sensor device_class '{self.ha.device_class}'. "
            f"Allowed units: {', '.join(readable_units)}"
        )


class AppConfig(BaseModel):
    """Top-level application configuration model."""

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
        """Ensure exactly one Modbus endpoint configuration is provided."""
        if self.modbusRTU is None and self.modbusTCP is None:
            raise ValueError("One of modbusRTU or modbusTCP is required")
        if self.modbusRTU is not None and self.modbusTCP is not None:
            raise ValueError("Only one of modbusRTU or modbusTCP should be configured")
        return self


def validate_config_dict(data: dict[str, Any]) -> None:
    """Validate a raw config dictionary against the app schema."""
    AppConfig.model_validate(data)


def format_validation_error(error: ValidationError) -> str:
    """Format a pydantic validation error as indented JSON."""
    return error.json(indent=2)
