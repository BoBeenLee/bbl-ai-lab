#!/usr/bin/env python3
"""RemoteOK fetcher — 공개 JSON API `https://remoteok.com/api`.

ToS: 결과 활용 시 RemoteOK 출처 링크백(follow) 필요. record 의 `url` 이 원본 링크.
robots.txt: `/api` 허용 (`?action=get_jobs` AJAX 만 Disallow), Crawl-delay 1.

Usage:
    python scripts/recruit/fetchers/remoteok.py --out /tmp/out.jsonl --max-pages 1
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from normalize import http_get_json, log, make_record, now_iso, run_fetcher, strip_html  # noqa: E402

API = "https://remoteok.com/api"
PAGE_SIZE = 100  # /api 는 1회 호출로 ~100건 반환


def _salary(j: dict) -> str | None:
    lo, hi = j.get("salary_min"), j.get("salary_max")
    if lo and hi:
        return f"{lo}-{hi}"
    return str(lo or hi) if (lo or hi) else None


def fetch(args) -> list[dict]:
    stamp = now_iso()
    # --max-pages 와 --max 중 작은 쪽을 상한으로. /api 는 단일 응답이라 page>1 이면 그대로.
    cap = args.max
    if getattr(args, "max_pages", None):
        cap = min(cap, args.max_pages * PAGE_SIZE)

    data = http_get_json(API)
    out: list[dict] = []
    for j in data:
        if not isinstance(j, dict):
            continue
        # record[0] 은 legal/메타 (id/position 없음) -> skip
        if j.get("legal") is not None or not j.get("id") or not j.get("position"):
            continue
        out.append(
            make_record(
                platform="remoteok",
                region="GLOBAL",
                external_id=j.get("id"),
                title=j.get("position"),
                company=j.get("company"),
                location=j.get("location"),
                description=strip_html(j.get("description")),
                skills_raw=j.get("tags") or [],
                url=j.get("url"),
                posted_at=(j.get("date") or "")[:10] or None,
                salary=_salary(j),
                collected_at=stamp,
            )
        )
        if len(out) >= cap:
            break
    log(f"remoteok: {len(out)} records")
    return out


if __name__ == "__main__":
    run_fetcher(fetch, "RemoteOK fetcher", extra=lambda p: p.add_argument(
        "--max-pages", type=int, default=None, help="page cap (1 page = 100)"))
