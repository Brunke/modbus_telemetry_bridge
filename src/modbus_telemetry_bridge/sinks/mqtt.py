"""MQTT sink with Home Assistant discovery support."""

from __future__ import annotations

import json
import logging
from typing import Any

import paho.mqtt.client as mqtt

from ..decoder import topic_safe
from ..mapping import TagSample

_LOG = logging.getLogger(__name__)

_ALLOWED_HA_COMPONENTS = {
    "sensor",
    "binary_sensor",
    "number",
    "select",
}


def _ha_device_class(unit: str) -> str | None:
    """Infer a Home Assistant sensor device class from unit text."""
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


def _default_state_class(sample: TagSample) -> str | None:
    """Infer a default HA state class for numeric samples."""
    if not isinstance(sample.value, (int, float)):
        return None

    unit = (sample.unit or "").lower()
    name = sample.name.lower()
    if unit in {"wh", "kwh"}:
        if any(token in name for token in {"total", "lifetime", "running", "cumulative"}):
            return "total_increasing"
        return "measurement"

    return "measurement"


class MqttDiscoverySink:
    """Publish telemetry values and Home Assistant discovery metadata to MQTT."""

    def __init__(self, cfg: dict, node_id: str = "modbus_bridge"):
        """Initialize MQTT client and sink configuration."""
        self._cfg = cfg
        self._node_id = topic_safe(node_id)
        self._prefix = cfg.get("discovery_prefix", "homeassistant")
        self._state_prefix = cfg.get("state_prefix", "modbus_telemetry")
        self._origin_cfg: dict[str, Any] = cfg.get("origin") or {"name": "modbus-telemetry-bridge"}
        self._devices_cfg: dict[str, dict[str, Any]] = {
            topic_safe(key): value for key, value in cfg.get("devices", {}).items()
        }

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        username = cfg.get("username")
        password = cfg.get("password")
        if username:
            client.username_pw_set(username, password)

        client.connect(cfg.get("host", "localhost"), int(cfg.get("port", 1883)), 60)
        client.loop_start()

        self._client = client
        self._published_discovery: set[str] = set()

    def _state_topic(self, entity_object_id: str) -> str:
        """Build the retained state topic for one entity."""
        return f"{self._state_prefix}/{self._node_id}/{entity_object_id}/state"

    def _discovery_topic(self, component: str, entity_object_id: str) -> str:
        """Build the Home Assistant discovery topic for one entity."""
        return f"{self._prefix}/{component}/{self._node_id}/{entity_object_id}/config"

    def _resolved_component(self, sample: TagSample) -> str:
        """Resolve a valid Home Assistant component for a sample."""
        component = (sample.mapping.ha_component or "sensor").strip().lower()
        if component not in _ALLOWED_HA_COMPONENTS:
            return "sensor"
        return component

    def _resolved_device_key(self, sample: TagSample) -> str:
        """Resolve which configured HA device group a sample belongs to."""
        if not sample.mapping.ha_device_id:
            return "root"
        return topic_safe(sample.mapping.ha_device_id)

    def _entity_object_id(self, sample: TagSample, device_key: str) -> str:
        """Build an object id that is stable and unique across device groups."""
        base_object_id = topic_safe(sample.mapping.ha_object_id or sample.name)
        if device_key == "root":
            return base_object_id
        return f"{device_key}_{base_object_id}"

    def _root_device_payload(self) -> dict[str, Any]:
        """Build default discovery device metadata for the root bridge device."""
        return {
            "identifiers": [self._node_id],
            "name": self._cfg.get("device_name", "Modbus Bridge"),
            "manufacturer": self._cfg.get("manufacturer", "Custom"),
            "model": self._cfg.get("model", "Modbus Mapping"),
        }

    def _device_payload(self, sample: TagSample, device_key: str) -> dict[str, Any]:
        """Build discovery device metadata for the sample's target device."""
        if device_key == "root":
            return self._root_device_payload()

        root_payload = self._root_device_payload()
        raw_device = self._devices_cfg.get(device_key, {})
        identifiers = raw_device.get("identifiers") or [f"{self._node_id}_{device_key}"]

        payload: dict[str, Any] = {
            "identifiers": identifiers,
            "name": raw_device.get("name", sample.mapping.ha_device_id or device_key),
            "manufacturer": raw_device.get("manufacturer") or root_payload.get("manufacturer"),
            "model": raw_device.get("model") or root_payload.get("model"),
        }

        if raw_device.get("sw_version"):
            payload["sw_version"] = raw_device["sw_version"]
        if raw_device.get("hw_version"):
            payload["hw_version"] = raw_device["hw_version"]

        via_device = raw_device.get("via_device")
        if via_device:
            via_key = topic_safe(str(via_device))
            if via_key == "root":
                payload["via_device"] = self._node_id
            elif via_key in self._devices_cfg:
                via_identifiers = self._devices_cfg[via_key].get("identifiers")
                payload["via_device"] = (
                    via_identifiers[0] if via_identifiers else f"{self._node_id}_{via_key}"
                )
            else:
                payload["via_device"] = str(via_device)

        return payload

    def _publish_discovery(self, sample: TagSample) -> None:
        """Publish retained discovery metadata for one sample if not already published."""
        device_key = self._resolved_device_key(sample)
        component = self._resolved_component(sample)
        entity_object_id = self._entity_object_id(sample, device_key)
        discovery_key = f"{component}:{entity_object_id}"
        if discovery_key in self._published_discovery:
            return

        overrides = self._cfg.get("entity_overrides", {})
        bare_object_id = topic_safe(sample.mapping.ha_object_id or sample.name)
        override_candidates = [
            sample.name,
            bare_object_id,
            entity_object_id,
            f"{device_key}.{bare_object_id}",
        ]
        entity_override = {}
        for candidate in override_candidates:
            if candidate in overrides:
                entity_override = overrides[candidate]
                break

        payload = {
            "name": sample.name,
            "unique_id": f"{self._node_id}_{entity_object_id}",
            "state_topic": self._state_topic(entity_object_id),
            "availability_topic": f"{self._state_prefix}/{self._node_id}/availability",
            "payload_available": "online",
            "payload_not_available": "offline",
            "device": self._device_payload(sample, device_key),
            "origin": self._origin_cfg,
        }

        if sample.mapping.ha_entity_category:
            payload["entity_category"] = sample.mapping.ha_entity_category
        if sample.mapping.ha_enabled_by_default is not None:
            payload["enabled_by_default"] = sample.mapping.ha_enabled_by_default

        if sample.mapping.ha_command_topic:
            payload["command_topic"] = sample.mapping.ha_command_topic

        if sample.mapping.ha_device_class:
            payload["device_class"] = sample.mapping.ha_device_class

        if component == "binary_sensor":
            if sample.mapping.ha_payload_on is not None:
                payload["payload_on"] = sample.mapping.ha_payload_on
            if sample.mapping.ha_payload_off is not None:
                payload["payload_off"] = sample.mapping.ha_payload_off

        if component == "number":
            if sample.mapping.ha_min is not None:
                payload["min"] = sample.mapping.ha_min
            if sample.mapping.ha_max is not None:
                payload["max"] = sample.mapping.ha_max
            if sample.mapping.ha_step is not None:
                payload["step"] = sample.mapping.ha_step
            if sample.mapping.ha_mode is not None:
                payload["mode"] = sample.mapping.ha_mode

        if component == "select" and sample.mapping.ha_options:
            payload["options"] = sample.mapping.ha_options

        if (
            component == "sensor"
            and payload.get("device_class") == "enum"
            and "options" not in payload
        ):
            if sample.mapping.ha_options:
                payload["options"] = sample.mapping.ha_options
            elif sample.mapping.enum_values:
                payload["options"] = list(dict.fromkeys(sample.mapping.enum_values.values()))

        if sample.unit and sample.unit.lower() != "none":
            payload["unit_of_measurement"] = sample.unit
            if component == "sensor":
                device_class = payload.get("device_class") or _ha_device_class(sample.unit)
                if device_class:
                    payload["device_class"] = device_class

        if component == "sensor":
            state_class = sample.mapping.ha_state_class
            if state_class is None and payload.get("device_class") != "enum":
                state_class = _default_state_class(sample)
            if state_class:
                payload["state_class"] = state_class

        for key in ("device_class", "state_class"):
            override_value = entity_override.get(key)
            if override_value is None:
                continue
            payload_value = payload.get(key)
            if payload_value is not None and payload_value != override_value:
                _LOG.warning(
                    "Entity override for '%s' on '%s' replaced payload value '%s' with '%s'",
                    key,
                    sample.name,
                    payload_value,
                    override_value,
                )

        for key, value in entity_override.items():
            payload[key] = value

        self._client.publish(
            self._discovery_topic(component, entity_object_id),
            json.dumps(payload),
            retain=True,
        )
        self._published_discovery.add(discovery_key)

    def publish(self, samples: list[TagSample]) -> None:
        """Publish availability, discovery payloads, and retained states."""
        self._client.publish(
            f"{self._state_prefix}/{self._node_id}/availability",
            "online",
            retain=True,
        )

        for sample in samples:
            self._publish_discovery(sample)
            entity_object_id = self._entity_object_id(sample, self._resolved_device_key(sample))
            self._client.publish(
                self._state_topic(entity_object_id), str(sample.value), retain=True
            )

    def close(self) -> None:
        """Publish offline availability and close the MQTT client."""
        self._client.publish(
            f"{self._state_prefix}/{self._node_id}/availability",
            "offline",
            retain=True,
        )
        self._client.loop_stop()
        self._client.disconnect()
