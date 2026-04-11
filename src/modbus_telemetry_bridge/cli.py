from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .service import run_service


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the generic Modbus telemetry bridge")
    parser.add_argument("--config", default="config.json", help="Path to JSON config")
    parser.add_argument("--once", action="store_true", help="Run one polling cycle and exit")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))
    run_service(cfg, once=args.once)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
