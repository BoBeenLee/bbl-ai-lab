#!/usr/bin/env python3
"""잡코리아(JobKorea) fetcher — 목록 페이지 → 상세 schema.org JobPosting JSON-LD.

흐름: `/recruit/joblist` HTML 에서 `/Recruit/GI_Read/{rec_idx}` 링크 수집
  → 각 상세 `/Recruit/GI_Read/{id}` 페이지의 JSON-LD JobPosting 파싱 (원티드와 동일 패턴).
robots: AI/LLM 크롤러는 차단되나 일반 봇은 joblist/GI_Read 허용. fetcher 는 LLM 미사용.

주의: 잡코리아 JSON-LD 의 description 은 짧은 SEO 요약이라 스킬 신호가 약하다
(메타데이터/직군 위주). 본문 전체는 CSR 렌더 — PoC 범위 밖.

차단/오류 시 graceful skip(exit 0).

Usage:
    python scripts/recruit/fetchers/jobkorea.py --out /tmp/out.jsonl --max 20
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from normalize import http_get, log, make_record, now_iso, run_fetcher, strip_html  # noqa: E402

LIST_URL = "https://www.jobkorea.co.kr/recruit/joblist"
DETAIL_URL = "https://www.jobkorea.co.kr/Recruit/GI_Read/{rid}"
SLEEP = 0.25

_ID_RE = re.compile(r"/Recruit/GI_Read/(\d+)")
_LD_RE = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.DOTALL)


def _extract_jobposting(html: str) -> dict | None:
    for block in _LD_RE.findall(html):
        try:
            obj = json.loads(block)
        except json.JSONDecodeError:
            continue
        for it in (obj if isinstance(obj, list) else [obj]):
            if isinstance(it, dict) and it.get("@type") == "JobPosting":
                return it
    return None


def _locality(jp: dict) -> str | None:
    loc = jp.get("jobLocation") or {}
    addr = loc.get("address") if isinstance(loc, dict) else None
    if isinstance(addr, dict):
        return addr.get("addressLocality") or addr.get("addressRegion") or addr.get("streetAddress")
    return None


def fetch(args) -> list[dict]:
    stamp = now_iso()
    out: list[dict] = []
    try:
        listing = http_get(LIST_URL)
    except urllib.error.HTTPError as e:
        log(f"jobkorea: list HTTP {e.code} — skipping platform")
        return out
    except Exception as e:
        log(f"jobkorea: list failed: {type(e).__name__} — skipping platform")
        return out

    rids = list(dict.fromkeys(_ID_RE.findall(listing)))  # 등장 순서 유지 dedup
    log(f"jobkorea: {len(rids)} rec_idx from joblist")

    for rid in rids:
        if len(out) >= args.max:
            break
        try:
            html = http_get(DETAIL_URL.format(rid=rid))
        except urllib.error.HTTPError as e:
            if e.code == 403:
                log(f"jobkorea: detail {rid} HTTP 403 — blocked, skipping platform")
                return out
            log(f"jobkorea: detail {rid} HTTP {e.code} — skip item")
            continue
        except Exception as e:
            log(f"jobkorea: detail {rid} failed: {type(e).__name__} — skip item")
            continue
        jp = _extract_jobposting(html)
        if not jp:
            continue
        org = jp.get("hiringOrganization") or {}
        out.append(make_record(
            platform="jobkorea", region="KR", external_id=rid,
            title=jp.get("title"),
            company=org.get("name") if isinstance(org, dict) else None,
            location=_locality(jp),
            description=strip_html(jp.get("description")),
            skills_raw=[],  # JSON-LD 요약뿐 → analyze 가 title/요약에서 추출
            url=jp.get("url") or DETAIL_URL.format(rid=rid),
            posted_at=(jp.get("datePosted") or "")[:10] or None,
            employment_type=jp.get("employmentType"),
            collected_at=stamp))
        time.sleep(SLEEP)
    log(f"jobkorea: {len(out)} records")
    return out


if __name__ == "__main__":
    run_fetcher(fetch, "JobKorea fetcher (JSON-LD)", default_max=20)
