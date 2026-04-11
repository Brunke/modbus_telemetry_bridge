from __future__ import annotations

import json

import paho.mqtt.client as mqtt

from ..decoder import topic_safe
from ..mapping import TagSample


def _ha_device_class(unit: str) -> str | None:
    normalized = unit.lower()
    return {
        "v": "voltage",
        "a": "current",
        "w": "power",
        "wh": "energy",
        "kwh": "energy",
        "%": "battery",
        "hz": "frequency",
        "°c": "temperature",
    }.get(normalized)


class MqttDiscoverySink:
    def __init__(self, cfg: dict, node_id: str = "modbus_bridge"):
        self._cfg = cfg
        self._node_id = topic_safe(node_id)
        self._prefix = cfg.get("discovery_prefix", "homeassistant")
        self._state_prefix = cfg.get("state_prefix", "modbus_telemetry")

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        username = cfg.get("username")
        password = cfg.get("password")
        if username:
            client.username_pw_set(username, password)

        client.connect(cfg.get("host", "localhost"), int(cfg.get("port", 1883)), 60)
        client.loop_start()

        self._client = client
        self._published_discovery: set[str] = set()

    def _state_topic(self, object_id: str) -> str:
        return f"{self._state_prefix}/{self._node_id}/{object_id}/state"

    def _discovery_topic(self, object_id: str) -> str:
        return f"{self._prefix}/sensor/{self._node_id}/{object_id}/config"

    def _publish_discovery(self, sample: TagSample) -> None:
        object_id = topic_safe(sample.name)
        if object_id in self._published_discovery:
            return

        payload = {
            "name": sample.name,
            "unique_id": f"{self._node_id}_{object_id}",
            "state_topic": self._state_topic(object_id),
            "availability_topic": f"{self._state_prefix}/{self._node_id}/availability",
            "payload_available": "online",
            "payload_not_available": "offline",
            "device": {
                "identifiers": [self._node_id],
                "name": self._cfg.get("device_name", "Modbus Bridge"),
                "manufacturer": self._cfg.get("manufacturer", "Custom"),
                "model": self._cfg.get("model", "Modbus Mapping"),
            },
        }

        if sample.unit and sample.unit.lower() != "none":
            payload["unit_of_measurement"] = sample.unit
            device_class = _ha_device_class(sample.unit)
            if device_class:
                payload["device_class"] = device_class

        if isinstance(sample.value, (int, float)):
            payload["state_class"] = "measurement"

        self._client.publish(self._discovery_topic(object_id), json.dumps(payload), retain=True)
        self._published_discovery.add(object_id)

    def publish(self, samples: list[TagSample]) -> None:
        self._client.publish(
            f"{self._state_prefix}/{self._node_id}/availability",
            "online",
            retain=True,
        )

        for sample in samples:
            self._publish_discovery(sample)
            object_id = topic_safe(sample.name)
            self._client.publish(self._state_topic(object_id), str(sample.value), retain=True)

    def close(self) -> None:
        self._client.publish(
            f"{self._state_prefix}/{self._node_id}/availability",
            "offline",
            retain=True,
        )
        self._client.loop_stop()
        self._client.disconnect()
