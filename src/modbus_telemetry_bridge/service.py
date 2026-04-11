from __future__ import annotations

import logging
import time

from .config import load_mappings
from .modbus_client import ModbusReader
from .sinks.base import Sink
from .sinks.influx import InfluxSink
from .sinks.mqtt import MqttDiscoverySink

_LOG = logging.getLogger(__name__)


def build_sinks(cfg: dict) -> list[Sink]:
    sinks: list[Sink] = []

    influx_cfg = cfg.get("influxdb", {})
    if influx_cfg.get("enabled", True) and influx_cfg.get("token"):
        sinks.append(InfluxSink(influx_cfg))

    mqtt_cfg = cfg.get("mqtt", {})
    if mqtt_cfg.get("enabled", False):
        sinks.append(MqttDiscoverySink(mqtt_cfg, node_id=mqtt_cfg.get("node_id", "modbus_bridge")))

    return sinks


def run_service(cfg: dict, once: bool = False) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    mappings = load_mappings(cfg)
    reader = ModbusReader(cfg)
    sinks = build_sinks(cfg)

    span_gaps = bool(cfg.get("span_gaps", False))
    max_length = int(cfg.get("maximum_read_length", 64))
    poll_interval = float(cfg.get("poll_interval", 3.0))

    try:
        if not reader.connect():
            raise ConnectionError("Failed to connect to Modbus endpoint")

        while True:
            samples = reader.read(mappings, span_gaps=span_gaps, max_length=max_length)
            for sink in sinks:
                sink.publish(samples)

            _LOG.info("Polled %s samples", len(samples))

            if once:
                break

            time.sleep(poll_interval)

    finally:
        for sink in sinks:
            sink.close()
        reader.close()
