from __future__ import annotations

import logging
from collections import defaultdict

from pymodbus import FramerType
from pymodbus.client import ModbusSerialClient, ModbusTcpClient

from .decoder import decode_registers
from .mapping import RegisterType, TagMapping, TagSample

_LOG = logging.getLogger(__name__)


class ModbusReader:
    def __init__(self, config: dict):
        self._cfg = config
        self._client = self._build_client(config)
        self._unit_id = self._resolve_unit_id(config)
        self._byteorder = self._resolve_byteorder(config)

    def _build_client(self, cfg: dict):
        if "modbusRTU" in cfg:
            c = cfg["modbusRTU"]
            method = str(c.get("method", "rtu")).lower()
            if method == "ascii":
                framer = FramerType.ASCII
            else:
                framer = FramerType.RTU

            return ModbusSerialClient(
                port=c["port"],
                framer=framer,
                baudrate=c.get("baudrate", 9600),
                parity=c.get("parity", "N"),
                stopbits=c.get("stopbits", 1),
                bytesize=c.get("bytesize", 8),
                timeout=c.get("timeout", 1),
            )

        if "modbusTCP" in cfg:
            c = cfg["modbusTCP"]
            return ModbusTcpClient(
                host=c["host"],
                port=c.get("port", 502),
                timeout=c.get("timeout", 1),
            )

        raise ValueError("No modbusRTU or modbusTCP block found in config")

    def _resolve_unit_id(self, cfg: dict) -> int:
        if "modbusRTU" in cfg:
            return int(cfg["modbusRTU"]["unit_id"])
        return int(cfg["modbusTCP"]["unit_id"])

    def _resolve_byteorder(self, cfg: dict) -> str:
        if "modbusRTU" in cfg:
            return str(cfg["modbusRTU"].get("endianness", "BIG"))
        return str(cfg["modbusTCP"].get("endianness", "BIG"))

    def connect(self) -> bool:
        return bool(self._client.connect())

    def close(self) -> None:
        self._client.close()

    def _is_socket_open(self) -> bool:
        return bool(getattr(self._client, "is_socket_open", lambda: True)())

    def reconnect(self, attempts: int = 3) -> bool:
        for idx in range(1, attempts + 1):
            _LOG.warning("Reconnect attempt %s", idx)
            if self.connect():
                return True
        return False

    @staticmethod
    def _group_tags(
        tags: list[TagMapping],
        span_gaps: bool,
        max_length: int,
    ) -> list[list[TagMapping]]:
        grouped: list[list[TagMapping]] = []
        by_register: dict[str, list[TagMapping]] = defaultdict(list)

        for tag in tags:
            by_register[tag.register_type].append(tag)

        for register_type, group_tags in by_register.items():
            sorted_tags = sorted(group_tags, key=lambda t: t.address)
            current = [sorted_tags[0]]
            last_address = sorted_tags[0].address
            last_count = sorted_tags[0].count

            for tag in sorted_tags[1:]:
                group_size = (tag.address - current[0].address) + tag.count

                if span_gaps:
                    contiguous = group_size <= max_length
                else:
                    contiguous = (
                        tag.address == (last_address + last_count) and group_size <= max_length
                    )

                if contiguous:
                    current.append(tag)
                    last_address = tag.address
                    last_count = tag.count
                else:
                    grouped.append(current)
                    current = [tag]
                    last_address = tag.address
                    last_count = tag.count

            grouped.append(current)
            _LOG.debug("Grouped %s tags for register_type=%s", len(group_tags), register_type)

        return grouped

    def read(self, tags: list[TagMapping], span_gaps: bool, max_length: int) -> list[TagSample]:
        if not self._is_socket_open() and not self.reconnect():
            raise ConnectionError("Modbus client disconnected and reconnect failed")

        groups = self._group_tags(tags, span_gaps, max_length)
        samples: list[TagSample] = []

        for group in groups:
            min_address = group[0].address
            max_address = group[-1].address + group[-1].count - 1
            total_registers = max_address - min_address + 1

            register_type = group[0].register_type
            if register_type == RegisterType.INPUT:
                try:
                    result = self._client.read_input_registers(
                        min_address,
                        count=total_registers,
                        device_id=self._unit_id,
                    )
                except TypeError:
                    result = self._client.read_input_registers(
                        min_address,
                        total_registers,
                        slave=self._unit_id,
                    )
            else:
                try:
                    result = self._client.read_holding_registers(
                        min_address,
                        count=total_registers,
                        device_id=self._unit_id,
                    )
                except TypeError:
                    result = self._client.read_holding_registers(
                        min_address,
                        total_registers,
                        slave=self._unit_id,
                    )

            if result.isError():
                _LOG.error(
                    "Error reading %s registers %s-%s",
                    register_type,
                    min_address,
                    max_address,
                )
                continue

            for tag in group:
                start = tag.address - min_address
                end = start + tag.count
                value = decode_registers(tag, result.registers[start:end], self._byteorder)
                samples.append(TagSample(mapping=tag, value=value))

        return samples
