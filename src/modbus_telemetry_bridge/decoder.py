from __future__ import annotations

import re

from pymodbus.client import ModbusTcpClient

from .mapping import TagMapping

_TOPIC_SAFE_RE = re.compile(r"[^a-zA-Z0-9_]+")

_DATA_TYPE_MAP = {
    "float": ModbusTcpClient.DATATYPE.FLOAT32,
    "int": ModbusTcpClient.DATATYPE.INT16,
    "uint": ModbusTcpClient.DATATYPE.UINT16,
    "int64": ModbusTcpClient.DATATYPE.INT64,
    "uint64": ModbusTcpClient.DATATYPE.UINT64,
    "string": ModbusTcpClient.DATATYPE.STRING,
}


def decode_registers(
    mapping: TagMapping,
    registers: list[int],
    byteorder: str,
) -> float | int | str:
    word_order = "big" if byteorder.upper() == "BIG" else "little"

    if mapping.data_type == "enum":
        enum_raw = ModbusTcpClient.convert_from_registers(
            registers,
            data_type=ModbusTcpClient.DATATYPE.UINT16,
            word_order=word_order,
        )
        enum_key = str(enum_raw)
        raw = mapping.enum_values.get(enum_key, enum_key)
    else:
        data_type = _DATA_TYPE_MAP.get(mapping.data_type)
        if data_type is None:
            raw = registers[0]
        else:
            if mapping.data_type == "uint" and mapping.count == 2:
                data_type = ModbusTcpClient.DATATYPE.UINT32

            raw = ModbusTcpClient.convert_from_registers(
                registers,
                data_type=data_type,
                word_order=word_order,
            )

    if mapping.data_type in {"enum", "string"}:
        return raw

    return float(raw) * mapping.scaling_factor


def topic_safe(value: str) -> str:
    return _TOPIC_SAFE_RE.sub("_", value.strip().lower()).strip("_")
