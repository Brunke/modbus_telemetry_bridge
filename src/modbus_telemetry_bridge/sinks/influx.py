from __future__ import annotations

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from ..mapping import TagSample


class InfluxSink:
    def __init__(self, cfg: dict):
        self._org = cfg["org"]
        self._bucket = cfg["bucket"]
        self._client = InfluxDBClient(url=cfg["url"], token=cfg["token"], org=self._org)
        self._write_api = self._client.write_api(write_options=SYNCHRONOUS)

    def publish(self, samples: list[TagSample]) -> None:
        for sample in samples:
            if not isinstance(sample.value, (int, float)):
                continue

            point = (
                Point(sample.name)
                .tag("unit", sample.unit or "")
                .field("value", float(sample.value))
            )
            self._write_api.write(bucket=self._bucket, org=self._org, record=point)

    def close(self) -> None:
        self._client.close()
