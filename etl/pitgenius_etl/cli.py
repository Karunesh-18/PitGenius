"""python -m pitgenius_etl run --season 2023 [--rounds 1,2,3]"""
from __future__ import annotations

import argparse
import logging

from .pipeline import run_season, run_season_bulk, run_telemetry_season, sync_season


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(prog="pitgenius_etl")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the ETL pipeline for a season")
    run_parser.add_argument("--season", type=int, required=True)
    run_parser.add_argument(
        "--rounds", type=str, default=None, help="Comma-separated round numbers, e.g. 1,2,3. Defaults to all rounds."
    )

    run_parser.add_argument(
        "--results-only", action="store_true", help="Jolpica only: skip FastF1 laps and track outlines (small, fast)."
    )

    telemetry_parser = subparsers.add_parser(
        "telemetry", help="Load per-driver fastest-lap telemetry for a season (run `run` first)"
    )
    telemetry_parser.add_argument("--season", type=int, required=True)
    telemetry_parser.add_argument(
        "--rounds", type=str, default=None, help="Comma-separated round numbers, e.g. 1,2,3. Defaults to all rounds."
    )

    sync_parser = subparsers.add_parser("sync", help="Load newly raced rounds for a season (no-op when up to date)")
    sync_parser.add_argument("--season", type=int, default=None, help="Defaults to the current year.")

    kaggle_parser = subparsers.add_parser(
        "import-kaggle", help="Import seasons from the Kaggle F1 CSV dump (no API limits; results, laps, pit laps)"
    )
    kaggle_parser.add_argument("--dir", required=True, help="Folder containing the dataset CSVs")
    kaggle_parser.add_argument("--seasons", required=True, help="Comma-separated, e.g. 2018,2019,2024")

    args = parser.parse_args()

    if args.command == "run":
        rounds = [int(r) for r in args.rounds.split(",")] if args.rounds else None
        if args.results_only and rounds is None:
            run_season_bulk(args.season)
        else:
            run_season(args.season, rounds=rounds, results_only=args.results_only)
    elif args.command == "telemetry":
        rounds = [int(r) for r in args.rounds.split(",")] if args.rounds else None
        run_telemetry_season(args.season, rounds=rounds)
    elif args.command == "import-kaggle":
        from .config import get_settings
        from .db import make_session_factory
        from .sources.kaggle_import import import_kaggle_season

        with make_session_factory(get_settings())() as db:
            for season in (int(x) for x in args.seasons.split(",")):
                import_kaggle_season(db, args.dir, season)
    elif args.command == "sync":
        import datetime as dt

        log = logging.getLogger("pitgenius_etl")
        log.info("synced rounds: %s", sync_season(args.season or dt.date.today().year))


if __name__ == "__main__":
    main()
