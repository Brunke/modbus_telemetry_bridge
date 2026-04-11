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
cp config.example.json modbus_config.json
```

3. Run:

```bash
uv run modbus-telemetry --config modbus_config.json
```

## Lint

```bash
uv run ruff check .
uv run ruff format .
```
