# Modbus Telemetry Bridge

A generic, mapping-driven Modbus telemetry service with pluggable outputs:
- InfluxDB write sink (optional)
- MQTT Home Assistant discovery sink (optional)

## Goals
- Keep Modbus mapping in JSON so users can adapt to other devices without code changes.
- Publish standardized telemetry from one polling loop.

## Quick Start (uv)

Python: 3.13+

1. Install deps:

```bash
uv sync
```

2. Copy and edit config:

```bash
cp config.example.json config.json
```

3. Run:

```bash
uv run modbus-telemetry --config config.json
```

## Device Templates

- Ready-to-use templates are under `config_templates/devices/`.
- The current inverter mapping is provided in:
	- `config_templates/devices/sungoldpower_sph10048p.json`
- Growatt template:
	- `config_templates/devices/growatt_spf_3000tl.json`
- Generic starter template:
	- `config_templates/devices/generic_modbus_tcp.json`

Example:

```bash
cp config_templates/devices/sungoldpower_sph10048p.json config.json
```

Then set secrets as environment variables before running:

```bash
export INFLUXDB_TOKEN='...'
export MQTT_USERNAME='...'
export MQTT_PASSWORD='...'
```

## MQTT Metadata Overrides

Set optional per-entity overrides in the `mqtt.entity_overrides` block in `config.json`.
Keys can be either the measurement name or topic-safe object id.

Example:

```json
"entity_overrides": {
	"Battery SOC": {
		"device_class": "battery",
		"state_class": "measurement"
	},
	"pv1_power": {
		"device_class": "power",
		"state_class": "measurement"
	}
}
```

## Home Assistant Device Grouping

By default, all discovered entities are grouped under a single MQTT discovery device.
You can optionally split entities into multiple Home Assistant devices.

Define grouped devices under `mqtt.devices` and point tags to those devices using `tags[].ha.device_id`.

Example:

```json
"mqtt": {
	"enabled": true,
	"node_id": "inverter_telemetry",
	"device_name": "PV Battery Inverter",
	"devices": {
		"battery": {
			"name": "Inverter Battery",
			"via_device": "root"
		},
		"pv": {
			"name": "PV Input",
			"via_device": "root"
		}
	}
}
```

Then annotate tags:

```json
{
	"name": "Battery SOC",
	"address": 256,
	"count": 1,
	"type": "holding",
	"engineering_unit": "%",
	"sourced_data_type": "uint",
	"ha": {
		"device_id": "battery",
		"component": "sensor",
		"object_id": "soc",
		"entity_category": "diagnostic",
		"device_class": "battery",
		"state_class": "measurement"
	}
}
```

Supported `tags[].ha.component` values are:
- `sensor`
- `binary_sensor`
- `number`
- `select`

If omitted, `component` defaults to `sensor`.

Component field reference:

| Component | Required `ha` fields | Optional `ha` fields | Notes |
| --- | --- | --- | --- |
| `sensor` | none | `device_id`, `object_id`, `entity_category`, `enabled_by_default`, `device_class`, `state_class`, `options` | `entity_category` only supports `diagnostic`. If `device_class` is `enum`, set `enum_values` or `ha.options` and do not set `state_class`. |
| `binary_sensor` | none | `device_id`, `object_id`, `entity_category`, `enabled_by_default`, `device_class`, `payload_on`, `payload_off` | State is read from Modbus value; `payload_on` and `payload_off` customize value mapping in discovery. |
| `number` | `command_topic` | `device_id`, `object_id`, `entity_category`, `enabled_by_default`, `device_class`, `min`, `max`, `step`, `mode` | `command_topic` is validated as required for HA discovery compatibility. |
| `select` | `command_topic`, `options` | `device_id`, `object_id`, `entity_category`, `enabled_by_default`, `device_class` | `options` is the selectable string list presented by Home Assistant. |

Publisher metadata can be included at `mqtt.origin` with:
- `name`
- `sw_version`
- `support_url`

For `sensor` components, you can explicitly set:
- `tags[].ha.device_class`
- `tags[].ha.state_class`

These values are validated in config and applied before automatic unit-based defaults.
When `tags[].ha.device_class` is set, `engineering_unit` is also validated against
the allowed Home Assistant units for that device class.
Use an empty string (or `"None"`) for classes that do not accept units.
If `mqtt.entity_overrides` also sets `device_class` or `state_class`, the override still wins
and a warning is logged when values conflict.

`mqtt.entity_overrides` still works and can target:
- measurement name (for example `Battery SOC`)
- object id (for example `soc`)
- resolved entity object id (for example `battery_soc`)
- `device_id.object_id` (for example `battery.soc`)

## Config Validation

Validate without running the poll loop:

```bash
uv run modbus-telemetry --config config.json --validate-config
```

## Systemd

A service template is provided at:

- `deploy/systemd/modbus-telemetry.service`
- `deploy/systemd/modbus-telemetry.service.example`

Use the `.example` file if you want placeholders and no machine-specific values.
Copy to your systemd directory, update user and paths, then enable/start.

## Lint

```bash
uv run ruff check .
uv run ruff format .
```
