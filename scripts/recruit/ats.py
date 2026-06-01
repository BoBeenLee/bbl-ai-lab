#!/usr/bin/env python3
"""글로벌 ATS 공개 job board 공통 fetcher (Greenhouse / Ashby / Lever).

세 ATS 모두 무인증 공개 API. 모델은 "회사별 조회" — `ats_companies.json` 의
슬러그 목록을 순회한다. 없는 슬러그/빈 응답은 graceful skip.
스킬은 구조화 신호가 없어 skills_raw=[] (analyze 단계 Gemini 가 description 에서 추출).
region 은 GLOBAL 로 통일(대부분 글로벌 HQ).

provider 엔드포인트:
  greenhouse  https://boards-api.greenhouse.io/v1/boards/<slug>/jobs?content=true
  ashby       https://api.ashbyhq.com/posting-api/job-board/<slug>
  lever       https://api.lever.co/v0/postings/<slug>?mode=json
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from normalize import http_get_json, log, make_record, now_iso, strip_html  # noqa: E402

CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ats_companies.json")
COMPANY_SLEEP = 0.3


def _epoch_ms_to_date(ms) -> str | None:
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).date().isoformat()
    except (ValueError, TypeError, OSError, OverflowError):
        return None


def _greenhouse(co: str, per_company: int, stamp: str) -> list[dict]:
    data = http_get_json(f"https://boards-api.greenhouse.io/v1/boards/{co}/jobs?content=true")
    out = []
    for j in (data.get("jobs") or [])[:per_company]:
        loc = j.get("location") or {}
        out.append(make_record(
            platform="greenhouse", region="GLOBAL", external_id=j.get("id"),
            title=j.get("title"), company=j.get("company_name") or co,
            location=loc.get("name") if isinstance(loc, dict) else None,
            description=strip_html(j.get("content")), skills_raw=[],
            url=j.get("absolute_url"), posted_at=(j.get("updated_at") or "")[:10] or None,
            collected_at=stamp))
    return out


def _ashby(co: str, per_company: int, stamp: str) -> list[dict]:
    data = http_get_json(f"https://api.ashbyhq.com/posting-api/job-board/{co}")
    out = []
    for j in (data.get("jobs") or [])[:per_company]:
        out.append(make_record(
            platform="ashby", region="GLOBAL", external_id=j.get("id"),
            title=j.get("title"), company=co,
            location=j.get("location"),
            description=strip_html(j.get("descriptionPlain") or j.get("descriptionHtml")),
            skills_raw=[], url=j.get("jobUrl") or j.get("applyUrl"),
            posted_at=(j.get("publishedAt") or "")[:10] or None,
            employment_type=j.get("employmentType"), collected_at=stamp))
    return out


def _lever(co: str, per_company: int, stamp: str) -> list[dict]:
    data = http_get_json(f"https://api.lever.co/v0/postings/{co}?mode=json")
    out = []
    if not isinstance(data, list):
        return out
    for j in data[:per_company]:
        cats = j.get("categories") or {}
        out.append(make_record(
            platform="lever", region="GLOBAL", external_id=j.get("id"),
            title=j.get("text"), company=co, location=cats.get("location"),
            description=j.get("descriptionPlain") or strip_html(j.get("description")),
            skills_raw=[], url=j.get("hostedUrl") or j.get("applyUrl"),
            posted_at=_epoch_ms_to_date(j.get("createdAt")),
            employment_type=cats.get("commitment"), collected_at=stamp))
    return out


_PROVIDERS = {"greenhouse": _greenhouse, "ashby": _ashby, "lever": _lever}


def fetch(provider: str, args) -> list[dict]:
    """provider 의 회사 목록을 순회해 정규화 레코드 리스트 반환. args: .max, .per_company."""
    import json

    fn = _PROVIDERS[provider]
    with open(CONFIG, encoding="utf-8") as f:
        companies = json.load(f).get(provider, [])
    per_company = getattr(args, "per_company", 40)
    stamp = now_iso()
    out: list[dict] = []
    for co in companies:
        if len(out) >= args.max:
            break
        try:
            recs = fn(co, per_company, stamp)
        except Exception as e:  # 없는 슬러그/네트워크 오류 → skip
            log(f"{provider}: {co} failed: {type(e).__name__} — skip")
            continue
        log(f"{provider}: {co} -> {len(recs)} jobs")
        out.extend(recs)
        time.sleep(COMPANY_SLEEP)
    log(f"{provider}: total {min(len(out), args.max)} records ({len(companies)} companies)")
    return out[: args.max]
