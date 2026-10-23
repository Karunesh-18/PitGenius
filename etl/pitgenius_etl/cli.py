"""python -m pitgenius_etl run --season 2023 [--rounds 1,2,3]"""
from __future__ import annotations

import argparse
import logging

from .pipeline import run_season, run_telemetry_season


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(prog="pitgenius_etl")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the ETL pipeline for a season")
    run_parser.add_argument("--season", type=int, required=True)
    run_parser.add_argument(
        "--rounds", type=str, default=None, help="Comma-separated round numbers, e.g. 1,2,3. Defaults to all rounds."
    )

    telemetry_parser = subparsers.add_parser(
        "telemetry", help="Load per-driver fastest-lap telemetry for a season (run `run` first)"
    )
    telemetry_parser.add_argument("--season", type=int, required=True)
    telemetry_parser.add_argument(
        "--rounds", type=str, default=None, help="Comma-separated round numbers, e.g. 1,2,3. Defaults to all rounds."
    )

    args = parser.parse_args()

    if args.command == "run":
        rounds = [int(r) for r in args.rounds.split(",")] if args.rounds else None
        run_season(args.season, rounds=rounds)
    elif args.command == "telemetry":
        rounds = [int(r) for r in args.rounds.split(",")] if args.rounds else None
        run_telemetry_season(args.season, rounds=rounds)


if __name__ == "__main__":
    main()
