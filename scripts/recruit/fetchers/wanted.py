#!/usr/bin/env python3
"""원티드(Wanted) fetcher — 상세 페이지 schema.org JobPosting JSON-LD.

흐름: 목록 API(`/api/v4/jobs`)로 최신 job id 수집 -> 상세 `/wd/{id}` 페이지의
`<script type="application/ld+json">` JobPosting 파싱.

주의(운영 리스크): 원티드는 CloudFront 뒤에 있어 데이터센터 IP(예: GitHub Actions)가
WAF 에 차단될 수 있다. 403/빈응답 시 해당 플랫폼을 graceful skip 하고 exit 0 한다
(전체 collect 파이프라인을 죽이지 않음).

Usage:
    python scripts/recruit/fetchers/wanted.py --out /tmp/out.jsonl --max 20
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from normalize import http_get, http_get_json, log, make_record, now_iso, run_fetcher, strip_html  # noqa: E402

LIST_API = (
    "https://www.wanted.co.kr/api/v4/jobs"
    "?country=kr&job_sort=job.latest_order&years=-1&locations=all&limit={limit}&offset={offset}"
)
DETAIL_URL = "https://www.wanted.co.kr/wd/{wid}"
PAGE = 20
SLEEP = 0.25  # 상세 페이지 호출 간 텀 (정중 크롤링)

_LD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)


def _extract_jobposting(html: str) -> dict | None:
    for block in _LD_RE.findall(html):
        try:
            obj = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("@type") == "JobPosting":
            return obj
    return None


def _record_from_jsonld(jp: dict, wid, stamp: str) -> dict:
    org = jp.get("hiringOrganization") or {}
    loc = jp.get("jobLocation") or {}
    addr = loc.get("address") if isinstance(loc, dict) else None
    locality = addr.get("addressLocality") if isinstance(addr, dict) else None
    salary = None
    bs = jp.get("baseSalary")
    if isinstance(bs, dict):
        val = bs.get("value")
        if isinstance(val, dict):
            salary = val.get("value") or val.get("minValue")
    return make_record(
        platform="wanted",
        region="KR",
        external_id=wid,  # /wd/{id} 의 정수 id (JSON-LD identifier 는 PropertyValue dict 라 비사용)
        title=jp.get("title"),
        company=org.get("name") if isinstance(org, dict) else None,
        location=locality,
        description=strip_html(jp.get("description")),
        skills_raw=[],  # 원티드 JSON-LD 는 스킬 미구조화 -> analyze 단계 추출
        url=jp.get("url") or DETAIL_URL.format(wid=wid),
        posted_at=jp.get("datePosted"),
        employment_type=jp.get("employmentType"),
        salary=str(salary) if salary else None,
        collected_at=stamp,
    )


def fetch(args) -> list[dict]:
    stamp = now_iso()
    out: list[dict] = []
    offset = 0
    try:
        while len(out) < args.max:
            lst = http_get_json(LIST_API.format(limit=PAGE, offset=offset))
            data = lst.get("data") or []
            if not data:
                break
            for j in data:
                if len(out) >= args.max:
                    break
                wid = j.get("id")
                try:
                    html = http_get(DETAIL_URL.format(wid=wid))
                except urllib.error.HTTPError as e:
                    if e.code == 403:
                        log(f"wanted: detail {wid} HTTP 403 (WAF) — blocked, skipping platform")
                        return out
                    log(f"wanted: detail {wid} HTTP {e.code} — skip item")
                    continue
                except Exception as e:
                    log(f"wanted: detail {wid} failed: {type(e).__name__} — skip item")
                    continue
                jp = _extract_jobposting(html)
                if not jp:
                    log(f"wanted: detail {wid} no JobPosting JSON-LD — skip item")
                    continue
                out.append(_record_from_jsonld(jp, wid, stamp))
                time.sleep(SLEEP)
            offset += PAGE
    except urllib.error.HTTPError as e:
        # 목록 API 차단 (403 등) -> graceful skip
        log(f"wanted: list API HTTP {e.code} — skipping platform (collected {len(out)} so far)")
    except Exception as e:
        log(f"wanted: failed: {type(e).__name__}: {e} — skipping platform")
    log(f"wanted: {len(out)} records")
    return out


if __name__ == "__main__":
    run_fetcher(fetch, "Wanted fetcher (JSON-LD)", default_max=20)
