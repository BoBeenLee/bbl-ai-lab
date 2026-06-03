#!/usr/bin/env python3
"""Ashby ATS fetcher — 공개 posting-api (무인증). 회사 목록은 ats_companies.json.

Usage:
    python scripts/recruit/fetchers/ashby.py --out /tmp/out.jsonl --max 50 --per-company 40
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ats  # noqa: E402
from normalize import run_fetcher  # noqa: E402

if __name__ == "__main__":
    run_fetcher(
        lambda args: ats.fetch("ashby", args),
        "Ashby ATS fetcher",
        extra=lambda p: p.add_argument("--per-company", type=int, default=40),
    )
