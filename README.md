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
