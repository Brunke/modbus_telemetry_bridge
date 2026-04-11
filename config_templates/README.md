# Config Templates

This folder contains reusable config templates for known devices.

## Available

- `devices/sungoldpower_sph10048p.json`
  - Based on the current project register mapping.
  - Influx token is externalized via `token_env`.
- `devices/growatt_spf_3000tl.json`
  - Migrated from legacy Growatt mapping (49 tags).
  - Includes MQTT block and env-based secret references.
- `devices/generic_modbus_tcp.json`
  - Generic ModbusTCP starter profile.
  - Includes one sample tag users can replace.

## Usage

1. Copy a template to runtime config:

```bash
cp config_templates/devices/sungoldpower_sph10048p.json config.json
```

For Growatt SPF 3000TL:

```bash
cp config_templates/devices/growatt_spf_3000tl.json config.json
```

2. Add optional MQTT block from `config.example.json` if needed.

3. Export secrets:

```bash
export INFLUXDB_TOKEN='...'
export MQTT_USERNAME='...'
export MQTT_PASSWORD='...'
```
