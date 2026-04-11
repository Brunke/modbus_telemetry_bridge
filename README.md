# Modbus Telemetry Bridge

A generic, mapping-driven Modbus telemetry service with pluggable outputs:
- InfluxDB write sink (optional)
- MQTT Home Assistant discovery sink (optional)

## Goals
- Keep Modbus mapping in JSON so users can adapt to other devices without code changes.
- Publish standardized telemetry from one polling loop.

## Quick Start (uv)

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

## Systemd

A service template is provided at:

- `deploy/systemd/modbus-telemetry.service`

Copy it to your systemd directory, update paths/user, then enable/start.

## Lint

```bash
uv run ruff check .
uv run ruff format .
```
