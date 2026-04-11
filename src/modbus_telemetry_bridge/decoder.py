from __future__ import annotations

import re

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

from .mapping import TagMapping

_TOPIC_SAFE_RE = re.compile(r"[^a-zA-Z0-9_]+")


def decode_registers(
    mapping: TagMapping,
    registers: list[int],
    byteorder: str,
) -> float | int | str:
    order = Endian.BIG if byteorder.upper() == "BIG" else Endian.LITTLE
    decoder = BinaryPayloadDecoder.fromRegisters(registers, byteorder=order)

    if mapping.data_type == "float":
        raw: float | int | str = decoder.decode_32bit_float()
    elif mapping.data_type == "int":
        raw = decoder.decode_16bit_int()
    elif mapping.data_type == "uint":
        raw = decoder.decode_32bit_uint() if mapping.count == 2 else decoder.decode_16bit_uint()
    elif mapping.data_type == "int64":
        raw = decoder.decode_64bit_int()
    elif mapping.data_type == "uint64":
        raw = decoder.decode_64bit_uint()
    elif mapping.data_type == "string":
        raw = decoder.decode_string(mapping.count).decode("utf-8", errors="ignore").strip("\x00")
    elif mapping.data_type == "enum":
        enum_key = str(decoder.decode_16bit_uint())
        raw = mapping.enum_values.get(enum_key, enum_key)
    else:
        raw = registers[0]

    if mapping.data_type in {"enum", "string"}:
        return raw

    return float(raw) * mapping.scaling_factor


def topic_safe(value: str) -> str:
    return _TOPIC_SAFE_RE.sub("_", value.strip().lower()).strip("_")
