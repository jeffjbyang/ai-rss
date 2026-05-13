from __future__ import annotations

import argparse
from pathlib import Path

from .collect import collect_to_candidates
from .notify import send_brief_to_feishu
from .timeutils import brief_date_for, parse_now


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-rss")
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect = subparsers.add_parser("collect", help="Collect sources and write candidate files.")
    collect.add_argument("--config", default="sources.yaml")
    collect.add_argument("--data-dir", default=".")
    collect.add_argument("--now", default=None)

    send = subparsers.add_parser("send", help="Send a daily brief to Feishu.")
    send.add_argument("--data-dir", default=".")
    send.add_argument("--date", default=None)
    send.add_argument("--now", default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "collect":
        collect_to_candidates(
            config_path=Path(args.config),
            data_dir=Path(args.data_dir),
            now=parse_now(args.now),
        )
        return 0

    if args.command == "send":
        brief_date = args.date or brief_date_for(parse_now(args.now))
        result = send_brief_to_feishu(data_dir=Path(args.data_dir), brief_date=brief_date)
        print(result.message)
        return 0 if result.ok else 1

    parser.error(f"Unknown command: {args.command}")
    return 2
