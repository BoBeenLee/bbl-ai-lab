#!/usr/bin/env python3
"""점핏(Jumpit) fetcher — saramin 내부 API.

주의: 점핏 상세 페이지는 CSR(React) 라 JSON-LD / __NEXT_DATA__ 가 없다.
따라서 플랜 초안의 "페이지 JSON-LD" 대신 saramin 내부 API 를 사용한다:
  목록  GET https://jumpit-api.saramin.co.kr/api/positions?page=&size=
  상세  GET https://jumpit-api.saramin.co.kr/api/position/{id}  (techStacks 등)
robots(jumpit.saramin.co.kr): /position 허용, GPTBot 만 차단(fetcher 는 LLM 미사용).

Usage:
    python scripts/recruit/fetchers/jumpit.py --out /tmp/out.jsonl --max 20
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from normalize import http_get_json, log, make_record, now_iso, run_fetcher  # noqa: E402

LIST_API = "https://jumpit-api.saramin.co.kr/api/positions?sort=reg_dt&highlight=false&page={page}&size={size}"
DETAIL_API = "https://jumpit-api.saramin.co.kr/api/position/{pid}"
PAGE_SIZE = 16
SLEEP = 0.2


def _career(det: dict) -> str | None:
    lo, hi = det.get("minCareer"), det.get("maxCareer")
    if lo is None and hi is None:
        return None
    return f"{lo or 0}~{hi if hi is not None else ''}년"


def fetch(args) -> list[dict]:
    stamp = now_iso()
    out: list[dict] = []
    page = 0
    while len(out) < args.max:
        lst = http_get_json(LIST_API.format(page=page, size=PAGE_SIZE))
        positions = ((lst.get("result") or {}).get("positions")) or []
        if not positions:
            break
        for p in positions:
            if len(out) >= args.max:
                break
            pid = p.get("id")
            try:
                det = (http_get_json(DETAIL_API.format(pid=pid)).get("result")) or {}
            except Exception as e:
                log(f"jumpit: detail {pid} failed: {type(e).__name__} — skip item")
                continue
            skills = [s.get("stack") for s in (det.get("techStacks") or []) if s.get("stack")]
            desc = "\n\n".join(
                s for s in (det.get("responsibility"), det.get("qualifications"), det.get("preferredRequirements")) if s
            )
            out.append(
                make_record(
                    platform="jumpit",
                    region="KR",
                    external_id=pid,
                    title=det.get("title") or p.get("title"),
                    company=det.get("companyName") or p.get("companyName"),
                    location=det.get("location"),
                    description=desc,
                    skills_raw=skills,
                    url=f"https://jumpit.saramin.co.kr/position/{pid}",
                    posted_at=(det.get("publishedAt") or "")[:10] or None,
                    employment_type=_career(det),
                    collected_at=stamp,
                )
            )
            time.sleep(SLEEP)
        page += 1
    log(f"jumpit: {len(out)} records")
    return out


if __name__ == "__main__":
    run_fetcher(fetch, "Jumpit fetcher (saramin API)", default_max=20)
