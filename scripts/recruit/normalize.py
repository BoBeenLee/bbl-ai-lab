#!/usr/bin/env python3
"""recruit fetcher 공통 유틸 (stdlib only).

- http_get / http_get_json : 브라우저 UA + 타임아웃 (fetch-url-content.py 관용구 차용)
- make_record              : 플랫폼 공통 정규화 스키마
- write_jsonl              : JSONL 적재
- strip_html / unescape    : HTML 본문 평문화
- now_iso / epoch_to_date  : 타임스탬프
- log                      : stderr 진단 로그

fetcher 는 LLM 을 호출하지 않는다. raw JD 를 정규화해 JSONL 로 적재만 한다.
구조화 추출(role_category/skills 정규화 등)은 analyze 단계(Gemini)의 책임.
"""

from __future__ import annotations

import html as _html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

# fetch-url-content.py 와 동일 계열의 브라우저 UA. 일부 플랫폼(KR)이 기본 UA 를 거를 수 있어 사용.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
HTTP_TIMEOUT = 20
DESCRIPTION_MAX = 4000

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t\f\v]+")


def log(msg: str) -> None:
    """stderr 진단 로그 (stdout 은 JSONL/카운트 전용)."""
    sys.stderr.write(f"[recruit] {msg}\n")
    sys.stderr.flush()


def http_get(url: str, timeout: int = HTTP_TIMEOUT, headers: dict | None = None) -> str:
    h = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def http_get_json(url: str, timeout: int = HTTP_TIMEOUT, headers: dict | None = None):
    return json.loads(http_get(url, timeout=timeout, headers=headers))


def strip_html(text: str | None) -> str:
    """HTML 태그 제거 + 엔티티 디코드 + 공백 정리."""
    if not text:
        return ""
    t = _html.unescape(text)
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.IGNORECASE)
    t = re.sub(r"</p\s*>", "\n\n", t, flags=re.IGNORECASE)
    t = _TAG_RE.sub("", t)
    t = _WS_RE.sub(" ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def unescape(text: str | None) -> str:
    return _html.unescape(text) if text else ""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def epoch_to_date(epoch) -> str | None:
    """unix epoch(초) -> ISO 날짜. None/오류 시 None."""
    if not epoch:
        return None
    try:
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).date().isoformat()
    except (ValueError, OSError, OverflowError):
        return None


def _clean(v):
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


def make_record(
    *,
    platform: str,
    region: str,
    external_id,
    title: str | None,
    company: str | None = None,
    location: str | None = None,
    description: str | None = None,
    skills_raw: list | None = None,
    url: str | None = None,
    posted_at: str | None = None,
    employment_type: str | None = None,
    salary: str | None = None,
    collected_at: str | None = None,
) -> dict:
    """플랫폼 공통 정규화 스키마. analyze 단계가 이 raw JSONL 을 소비한다."""
    desc = (description or "").strip()
    if len(desc) > DESCRIPTION_MAX:
        desc = desc[:DESCRIPTION_MAX]
    return {
        "platform": platform,
        "region": region,
        "external_id": str(external_id) if external_id is not None else None,
        "title": _clean(title),
        "company": _clean(company),
        "location": _clean(location),
        "description": desc or None,
        "skills_raw": [s for s in (skills_raw or []) if s],
        "url": _clean(url),
        "posted_at": _clean(posted_at),
        "employment_type": _clean(employment_type),
        "salary": _clean(salary),
        "collected_at": collected_at or now_iso(),
    }


def write_jsonl(path: str, records) -> int:
    """records 를 JSONL 로 기록. 디렉터리 자동 생성. 적재 건수 반환."""
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    n = 0
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    return n


def run_fetcher(fetch_fn, description: str, *, default_max: int = 200, extra=None):
    """fetcher 공통 CLI 엔트리. --out 필수, --max 선택. fetch_fn(max_records)->records.

    extra: argparse 에 추가 인자를 등록하는 콜백 (parser) -> None. fetch_fn 에 args 로 전달.
    """
    import argparse

    p = argparse.ArgumentParser(description=description)
    p.add_argument("--out", required=True, help="output JSONL path")
    p.add_argument("--max", type=int, default=default_max, help="max records (default %(default)s)")
    if extra:
        extra(p)
    args = p.parse_args()

    records = fetch_fn(args)
    n = write_jsonl(args.out, records)
    log(f"wrote {n} records -> {args.out}")
    print(n)
    return n
