#!/usr/bin/env python3
"""recruit-analyze 데이터 처리 (stdlib only).

서브커맨드:
  load       7일 윈도우 글롭 → (platform, external_id) dedup(최신 collected_at)
             → 선택적 stratified 샘플 → deduped.jsonl + stats(JSON, stdout)
  batch      deduped.jsonl 을 BATCH_SIZE 단위 JSON 배열 파일로 분할(추출 프롬프트 입력)
  reconcile  한 배치의 LLM 출력(JSON 배열)을 expected jd_id 기준으로 검증·조인
             → 유효 extracted 레코드 append, {ok, fail} 카운트(stdout)
  aggregate  extracted.jsonl + SKILL 정규화 사전 + (선택)이전 스냅샷
             → aggregate.json (= WoW 스냅샷 그 자체)

LLM/네트워크 호출 없음. recruit-analyze.sh 가 단계 사이를 잇는다.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict, OrderedDict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
REGIONS = ("KR", "GLOBAL")
ROLE_ENUM = {"engineer", "pm", "designer", "data", "ml", "devops", "qa", "security", "other"}
SENIORITY_ENUM = {"intern", "junior", "mid", "senior", "lead", "head"}
WORKMODE_ENUM = {"onsite", "hybrid", "remote", "unspecified"}
JSON_FENCE_RE = re.compile(r"```json\s*(.*?)```", re.DOTALL)
BATCH_DESC_MAX = 1500
DEFAULT_TOP_N = 25


def log(msg: str) -> None:
    sys.stderr.write(f"[analyze] {msg}\n")
    sys.stderr.flush()


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


# ---------- load ----------

def daterange(since: date, until: date):
    d = since
    while d <= until:
        yield d
        d += timedelta(days=1)


def cmd_load(args) -> int:
    data_dir = Path(args.data_dir)
    until = datetime.strptime(args.until, "%Y-%m-%d").date() if args.until else datetime.now(KST).date()
    since = datetime.strptime(args.since, "%Y-%m-%d").date() if args.since else until - timedelta(days=6)

    # dedup: (platform, external_id) -> record (최신 collected_at 유지)
    best: dict[tuple, dict] = {}
    files_seen = 0
    for d in daterange(since, until):
        for region in REGIONS:
            ddir = data_dir / d.isoformat() / region
            if not ddir.is_dir():
                continue
            for fp in sorted(ddir.glob("*.jsonl")):
                files_seen += 1
                for rec in read_jsonl(fp):
                    pid = rec.get("platform")
                    eid = rec.get("external_id")
                    if not pid or eid is None:
                        continue
                    key = (pid, str(eid))
                    prev = best.get(key)
                    if prev is None or (rec.get("collected_at") or "") >= (prev.get("collected_at") or ""):
                        best[key] = rec

    records = list(best.values())
    for r in records:
        r["jd_id"] = f"{r['platform']}:{r['external_id']}"
    total = len(records)

    sampled = total
    if args.max_jds and total > args.max_jds:
        records = stratified_sample(records, args.max_jds)
        sampled = len(records)
        log(f"샘플링: {total}중 {sampled}")

    records.sort(key=lambda r: r["jd_id"])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    by_region = Counter(r["region"] for r in records)
    by_platform = Counter(r["platform"] for r in records)
    stats = {
        "since": since.isoformat(),
        "until": until.isoformat(),
        "files": files_seen,
        "total": total,
        "sampled": sampled,
        "truncated": sampled < total,
        "by_region": dict(by_region),
        "by_platform": dict(by_platform),
    }
    print(json.dumps(stats, ensure_ascii=False))
    log(f"load: files={files_seen} total={total} sampled={sampled} -> {out}")
    return 0


def stratified_sample(records: list[dict], cap: int) -> list[dict]:
    """권역→플랫폼 그룹 라운드로빈(jd_id 정렬)으로 cap 개 결정적 추출."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in records:
        groups[(r.get("region"), r.get("platform"))].append(r)
    for g in groups.values():
        g.sort(key=lambda r: r["jd_id"])
    ordered_keys = sorted(groups.keys(), key=lambda k: (str(k[0]), str(k[1])))
    picked: list[dict] = []
    idx = 0
    while len(picked) < cap:
        progressed = False
        for k in ordered_keys:
            g = groups[k]
            if idx < len(g):
                picked.append(g[idx])
                progressed = True
                if len(picked) >= cap:
                    break
        if not progressed:
            break
        idx += 1
    return picked


# ---------- batch ----------

def cmd_batch(args) -> int:
    records = list(read_jsonl(Path(args.infile)))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    size = args.size
    n_batches = 0
    for i in range(0, len(records), size):
        chunk = records[i : i + size]
        items = [
            {
                "jd_id": r["jd_id"],
                "platform": r["platform"],
                "region": r["region"],
                "title": r.get("title"),
                "company": r.get("company"),
                "location": r.get("location"),
                "skills_raw": r.get("skills_raw") or [],
                "description": (r.get("description") or "")[:BATCH_DESC_MAX],
            }
            for r in chunk
        ]
        bf = out_dir / f"batch_{n_batches:04d}.json"
        bf.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
        n_batches += 1
    print(n_batches)
    log(f"batch: {len(records)} JDs -> {n_batches} batches (size {size}) in {out_dir}")
    return 0


# ---------- reconcile ----------

def _extract_json_array(raw: str):
    """LLM 출력에서 JSON 배열 추출 (```json 펜스 또는 첫 '[' ~ 마지막 ']')."""
    m = JSON_FENCE_RE.search(raw)
    candidate = m.group(1) if m else None
    if candidate is None:
        m2 = re.search(r"\[.*\]", raw, re.DOTALL)
        candidate = m2.group(0) if m2 else raw
    try:
        val = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return val if isinstance(val, list) else None


def _valid_extraction(obj: dict) -> bool:
    if not isinstance(obj, dict):
        return False
    if obj.get("role_category") not in ROLE_ENUM:
        return False
    if obj.get("seniority") not in SENIORITY_ENUM:
        return False
    if obj.get("work_mode") not in WORKMODE_ENUM:
        return False
    if not isinstance(obj.get("skills_required", []), list):
        return False
    if not isinstance(obj.get("skills_preferred", []), list):
        return False
    return True


def cmd_validate_array(args) -> int:
    """LLM 출력 파일이 비어있지 않은 JSON 배열이면 exit 0, 아니면 1 (폴백 판단용)."""
    raw = Path(args.infile).read_text(encoding="utf-8")
    arr = _extract_json_array(raw)
    return 0 if (arr is not None and len(arr) > 0) else 1


def cmd_reconcile(args) -> int:
    batch_items = json.loads(Path(args.batch).read_text(encoding="utf-8"))
    expected = {it["jd_id"]: it for it in batch_items}

    raw = Path(args.llm_out).read_text(encoding="utf-8")
    arr = _extract_json_array(raw)

    ok, fail = 0, 0
    out_records = []
    if arr is None:
        # 배치 전체 파싱 실패 → expected 전부 실패 카운트
        fail = len(expected)
        log(f"reconcile: batch LLM output not a JSON array — {fail} JDs failed")
    else:
        by_id = {}
        for o in arr:
            if isinstance(o, dict) and o.get("jd_id") in expected and o["jd_id"] not in by_id:
                by_id[o["jd_id"]] = o  # 중복 echo 는 첫 번째만
        for jd_id, src in expected.items():
            obj = by_id.get(jd_id)
            if obj is None or not _valid_extraction(obj):
                fail += 1
                continue
            out_records.append(
                {
                    "jd_id": jd_id,
                    "platform": src["platform"],
                    "region": src["region"],
                    "role_category": obj["role_category"],
                    "seniority": obj["seniority"],
                    "skills_required": [str(s) for s in obj.get("skills_required", []) if s],
                    "skills_preferred": [str(s) for s in obj.get("skills_preferred", []) if s],
                    "domain": (obj.get("domain") or "").strip().lower() or None,
                    "work_mode": obj["work_mode"],
                    "compensation_hint": (obj.get("compensation_hint") or None),
                }
            )
            ok += 1

    with Path(args.out).open("a", encoding="utf-8") as f:
        for r in out_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"ok": ok, "fail": fail}))
    log(f"reconcile: ok={ok} fail={fail} (batch {Path(args.batch).name})")
    return 0


# ---------- aggregate ----------

def load_skill_dict(skill_file: Path) -> dict[str, str]:
    """SKILL.md 의 단일 ```json 펜스(canonical→aliases)를 alias(소문자)→canonical 로 역전."""
    text = skill_file.read_text(encoding="utf-8")
    fences = JSON_FENCE_RE.findall(text)
    if len(fences) != 1:
        raise SystemExit(
            f"ERROR: {skill_file} 에 ```json 펜스가 정확히 1개여야 함 (발견: {len(fences)})"
        )
    canon_map = json.loads(fences[0])
    alias_to_canon: dict[str, str] = {}
    for canon, aliases in canon_map.items():
        alias_to_canon[canon.lower()] = canon
        for a in aliases or []:
            alias_to_canon[str(a).lower()] = canon
    return alias_to_canon


def cmd_aggregate(args) -> int:
    alias_to_canon = load_skill_dict(Path(args.skill_file))
    records = list(read_jsonl(Path(args.infile))) if Path(args.infile).exists() else []

    skills_overall: Counter = Counter()
    skills_by_region: dict[str, Counter] = {r: Counter() for r in REGIONS}
    role_x_region: dict[str, Counter] = {r: Counter() for r in REGIONS}
    seniority_dist: Counter = Counter()
    work_mode_dist: Counter = Counter()
    domain_dist: Counter = Counter()
    unknown: Counter = Counter()
    by_region = Counter()
    by_platform = Counter()

    for rec in records:
        region = rec.get("region") if rec.get("region") in REGIONS else "GLOBAL"
        by_region[region] += 1
        by_platform[rec.get("platform", "?")] += 1
        role_x_region[region][rec.get("role_category", "other")] += 1
        seniority_dist[rec.get("seniority", "mid")] += 1
        work_mode_dist[rec.get("work_mode", "unspecified")] += 1
        if rec.get("domain"):
            domain_dist[rec["domain"]] += 1

        # 한 JD 내 distinct canonical 스킬만 1회 카운트
        seen_canon = set()
        for s in (rec.get("skills_required") or []) + (rec.get("skills_preferred") or []):
            tok = str(s).strip().lower()
            if not tok:
                continue
            canon = alias_to_canon.get(tok)
            if canon is None:
                unknown[tok] += 1
                continue
            seen_canon.add(canon)
        for c in seen_canon:
            skills_overall[c] += 1
            skills_by_region[region][c] += 1

    top_n = args.top_n
    agg = {
        "meta": {
            "since": args.since,
            "until": args.until,
            "jd_count": len(records),
            "by_region": dict(by_region),
            "by_platform": dict(by_platform),
        },
        "skills_top": _counter_top(skills_overall, top_n),
        "skills_top_by_region": {r: _counter_top(skills_by_region[r], top_n) for r in REGIONS},
        "role_x_region": {r: dict(role_x_region[r]) for r in REGIONS},
        "seniority_dist": dict(seniority_dist),
        "work_mode_dist": dict(work_mode_dist),
        "domain_top": _counter_top(domain_dist, top_n),
        "unknown_skills": {
            "distinct": len(unknown),
            "top": _counter_top(unknown, 30),
        },
        "wow": None,
    }

    if args.prev:
        prev_path = Path(args.prev)
        if prev_path.exists():
            try:
                prev = json.loads(prev_path.read_text(encoding="utf-8"))
                agg["wow"] = compute_wow(agg, prev)
            except (json.JSONDecodeError, KeyError) as e:
                log(f"WoW: prev snapshot 파싱 실패 ({type(e).__name__}) — wow=null")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(agg, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"aggregate: jd={len(records)} skills_distinct={len(skills_overall)} unknown={len(unknown)} -> {out}")
    return 0


def _counter_top(c: Counter, n: int):
    # 동률은 토큰 알파벳 순으로 안정 정렬
    return [{"name": k, "count": v} for k, v in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:n]]


def compute_wow(curr: dict, prev: dict) -> dict:
    def rank_map(top_list):
        return {item["name"]: (i, item["count"]) for i, item in enumerate(top_list)}

    cur_top = curr["skills_top"]
    prev_top = prev.get("skills_top", [])
    cur_rank = rank_map(cur_top)
    prev_rank = rank_map(prev_top)

    movements = []
    for name, (ci, cc) in cur_rank.items():
        if name in prev_rank:
            pi, pc = prev_rank[name]
            movements.append(
                {"name": name, "count": cc, "count_delta": cc - pc, "rank_delta": pi - ci}
            )
    new_skills = [n for n in cur_rank if n not in prev_rank]
    dropped = [n for n in prev_rank if n not in cur_rank]
    return {
        "prev_until": prev.get("meta", {}).get("until"),
        "jd_count_delta": curr["meta"]["jd_count"] - prev.get("meta", {}).get("jd_count", 0),
        "skill_movements": sorted(movements, key=lambda m: -abs(m["rank_delta"]))[:15],
        "new_skills": new_skills[:15],
        "dropped_skills": dropped[:15],
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="recruit-analyze data processor")
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("load")
    pl.add_argument("--data-dir", default="data/recruit")
    pl.add_argument("--since")
    pl.add_argument("--until")
    pl.add_argument("--max-jds", type=int, default=0)
    pl.add_argument("--out", required=True)
    pl.set_defaults(func=cmd_load)

    pb = sub.add_parser("batch")
    pb.add_argument("--in", dest="infile", required=True)
    pb.add_argument("--size", type=int, default=15)
    pb.add_argument("--out-dir", required=True)
    pb.set_defaults(func=cmd_batch)

    pv = sub.add_parser("validate-array")
    pv.add_argument("--in", dest="infile", required=True)
    pv.set_defaults(func=cmd_validate_array)

    pr = sub.add_parser("reconcile")
    pr.add_argument("--batch", required=True)
    pr.add_argument("--llm-out", required=True)
    pr.add_argument("--out", required=True)
    pr.set_defaults(func=cmd_reconcile)

    pa = sub.add_parser("aggregate")
    pa.add_argument("--in", dest="infile", required=True)
    pa.add_argument("--skill-file", required=True)
    pa.add_argument("--prev", default="")
    pa.add_argument("--since", default="")
    pa.add_argument("--until", default="")
    pa.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    pa.add_argument("--out", required=True)
    pa.set_defaults(func=cmd_aggregate)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
