#!/usr/bin/env python3
"""HackerNews "Who is hiring?" fetcher — HN Firebase API.

흐름: user/whoishiring -> 최신 "Ask HN: Who is hiring?" story -> kids(댓글) = 개별 JD.
JD 댓글은 자유텍스트(회사/역할/위치/스킬 미구조화) -> analyze 단계 Gemini 가 구조화.

Usage:
    python scripts/recruit/fetchers/hn_hiring.py --out /tmp/out.jsonl --max 50
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from normalize import (  # noqa: E402
    epoch_to_date,
    http_get_json,
    log,
    make_record,
    now_iso,
    run_fetcher,
    strip_html,
)

HN = "https://hacker-news.firebaseio.com/v0"
SLEEP = 0.05  # 댓글당 호출 간 약간의 텀 (Firebase 는 관대하나 예의)


def latest_hiring_thread() -> dict | None:
    user = http_get_json(f"{HN}/user/whoishiring.json")
    for sid in user.get("submitted", [])[:12]:
        it = http_get_json(f"{HN}/item/{sid}.json")
        if it and it.get("title", "").startswith("Ask HN: Who is hiring"):
            return it
    return None


def fetch(args) -> list[dict]:
    stamp = now_iso()
    thread = latest_hiring_thread()
    if not thread:
        log("hn-hiring: latest 'Who is hiring' thread not found — skipping")
        return []
    log(f"hn-hiring: thread '{thread.get('title')}' id={thread.get('id')} kids={len(thread.get('kids', []))}")

    out: list[dict] = []
    for kid in thread.get("kids", []):
        if len(out) >= args.max:
            break
        try:
            c = http_get_json(f"{HN}/item/{kid}.json")
        except Exception as e:  # 단건 실패는 건너뛴다
            log(f"hn-hiring: item {kid} failed: {type(e).__name__}: {e}")
            continue
        if not c or c.get("dead") or c.get("deleted") or not c.get("text"):
            continue
        text = strip_html(c["text"])
        if not text:
            continue
        head = text.split("\n", 1)[0][:120]
        out.append(
            make_record(
                platform="hn-hiring",
                region="GLOBAL",
                external_id=c["id"],
                title=head,
                company=None,  # 자유텍스트 -> analyze 단계 추출
                location=None,
                description=text,
                skills_raw=[],
                url=f"https://news.ycombinator.com/item?id={c['id']}",
                posted_at=epoch_to_date(c.get("time")),
                collected_at=stamp,
            )
        )
        time.sleep(SLEEP)
    log(f"hn-hiring: {len(out)} records")
    return out


if __name__ == "__main__":
    run_fetcher(fetch, "HackerNews Who-is-hiring fetcher", default_max=400)
