from __future__ import annotations

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.rest import ApiException

from ..mapping import TagSample


class InfluxSink:
    def __init__(self, cfg: dict):
        self._org = cfg["org"]
        self._bucket = cfg["bucket"]
        self._client = InfluxDBClient(url=cfg["url"], token=cfg["token"], org=self._org)
        self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
        self._type_cache: dict[str, str] = {}

    def _existing_type(self, measurement: str) -> str | None:
        if measurement in self._type_cache:
            return self._type_cache[measurement]

        query = f'''from(bucket: "{self._bucket}")
  |> range(start: -3650d)
  |> filter(fn: (r) => r._measurement == "{measurement}" and r._field == "value")
  |> last()'''

        rows = list(self._client.query_api().query_stream(query, org=self._org))
        if not rows:
            return None

        value = rows[0].get_value()
        if isinstance(value, float):
            self._type_cache[measurement] = "float"
        elif isinstance(value, int):
            self._type_cache[measurement] = "integer"
        else:
            return None

        return self._type_cache[measurement]

    @staticmethod
    def _coerce(value: int | float, target_type: str | None) -> int | float:
        if target_type == "float":
            return float(value)
        if target_type == "integer":
            return int(round(float(value)))
        return value

    def _write_sample(self, sample: TagSample, value: int | float) -> None:
        point = Point(sample.name).tag("unit", sample.unit or "").field("value", value)
        self._write_api.write(bucket=self._bucket, org=self._org, record=point)

    def publish(self, samples: list[TagSample]) -> None:
        for sample in samples:
            if not isinstance(sample.value, (int, float)):
                continue

            target_type = self._existing_type(sample.name)
            value = self._coerce(sample.value, target_type)

            try:
                self._write_sample(sample, value)
            except ApiException as exc:
                message = str(exc)
                if "already exists as type float" in message:
                    self._type_cache[sample.name] = "float"
                    self._write_sample(sample, float(sample.value))
                elif "already exists as type integer" in message:
                    self._type_cache[sample.name] = "integer"
                    self._write_sample(sample, int(round(float(sample.value))))
                else:
                    raise

    def close(self) -> None:
        self._client.close()
