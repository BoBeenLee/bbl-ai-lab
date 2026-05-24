#!/usr/bin/env python3
"""
이슈 본문 in-place 갱신 헬퍼. idea-grill.sh 가 호출.

사용:
    python3 scripts/_idea_grill_body.py BODY_PATH JSON_PATH NEXT_ROUND GRILL_LEVEL CHAT_ID MSG_ID

STDOUT 에 갱신된 마크다운 본문을 출력한다.
입력:
    BODY_PATH    현재 이슈 본문 마크다운 파일
    JSON_PATH    idea-grill 프롬프트의 Gemini 출력 JSON 파일
    NEXT_ROUND   이번 라운드 번호 (integer)
    GRILL_LEVEL  현재 grill_level (보존)
    CHAT_ID      Telegram chat id (grill-meta 보존)
    MSG_ID       Telegram message id (grill-meta 보존)
"""
import json
import re
import sys
from datetime import datetime, timezone


def replace_section(body: str, header: str, new_content: str) -> str:
    pat = re.compile(
        rf"(^{re.escape(header)}\s*\n)(.*?)(?=\n##\s|\n>\s|\n---\s*$|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    if not pat.search(body):
        return body
    return pat.sub(lambda m: m.group(1) + new_content.rstrip() + "\n", body, count=1)


def append_to_section(body: str, header: str, new_lines: list) -> str:
    if not new_lines:
        return body
    pat = re.compile(
        rf"(^{re.escape(header)}\s*\n)(.*?)(?=\n##\s|\n---\s*$|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pat.search(body)
    if not m:
        block = header + "\n" + "\n".join(new_lines) + "\n\n"
        return body.rstrip() + "\n\n" + block
    existing = m.group(2).strip()
    placeholder = "_없음 — grilling 라운드에서 채워집니다._"
    if existing == "" or existing == placeholder:
        new_section = "\n".join(new_lines) + "\n"
    else:
        new_section = existing + "\n" + "\n".join(new_lines) + "\n"
    return pat.sub(lambda mm: mm.group(1) + new_section, body, count=1)


def main():
    body_path, json_path, next_round_s, grill_level, chat_id, msg_id = sys.argv[1:7]
    body = open(body_path, "r", encoding="utf-8").read()
    data = json.load(open(json_path, "r", encoding="utf-8"))
    next_round = int(next_round_s)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 1) grill-meta 블록 교체 (라운드 카운터만 증가, chat_id/msg_id/grill_level 보존)
    meta = (
        "<!-- bbl-grill-meta\n"
        f"round: {next_round}\n"
        f"grill_level: {grill_level}\n"
        f"chat_id: {chat_id}\n"
        f"msg_id: {msg_id}\n"
        "-->"
    )
    meta_pat = re.compile(r"<!--\s*bbl-grill-meta\s*\n.*?\n-->", re.DOTALL)
    if meta_pat.search(body):
        body = meta_pat.sub(lambda m: meta, body, count=1)
    else:
        body = meta + "\n\n" + body

    # 2) updated_sections 반영
    string_sections = {
        "summary":  "## 요약",
        "problem":  "## 문제",
        "goal":     "## 목표",
        "approach": "## 접근",
    }
    list_sections = {
        "non_goals": "## Non-goals",
        "risks":    "## 리스크",
    }
    us = data.get("updated_sections") or {}
    for key, header in string_sections.items():
        val = us.get(key)
        if isinstance(val, str) and val.strip():
            body = replace_section(body, header, val.strip() + "\n")
    for key, header in list_sections.items():
        val = us.get(key)
        if isinstance(val, list):
            if val:
                content = "\n".join(f"- {x}" for x in val) + "\n"
            else:
                content = "_없음_\n"
            body = replace_section(body, header, content)

    # 3) Open Questions = remaining + new
    remaining = data.get("remaining_questions") or []
    new_qs = data.get("new_questions") or []
    merged_qs = list(remaining) + list(new_qs)
    if merged_qs:
        qs_block = "\n".join(f"- [ ] {q}" for q in merged_qs) + "\n"
    else:
        qs_block = "_(모두 해소되었습니다.)_\n"
    body = replace_section(body, "## Open Questions", qs_block)

    # 4) Grilling Rounds 로그 누적
    resolved = data.get("resolved_questions") or []
    needs_c = data.get("needs_clarification", True)
    lines = [
        "<details>",
        f"<summary>Round {next_round} ({today}) — needs_clarification: {str(needs_c).lower()}</summary>",
        "",
    ]
    if data.get("round_summary"):
        lines += [f"_요약_: {data['round_summary']}", ""]
    if resolved:
        lines.append("**해소된 질문:**")
        for q in resolved:
            lines.append(f"- ~~{q}~~")
        lines.append("")
    if new_qs:
        lines.append("**새로 떠오른 질문:**")
        for q in new_qs:
            lines.append(f"- {q}")
        lines.append("")
    gd = data.get("glossary_diff") or []
    if gd:
        lines.append("**글로사리 변화:**")
        for g in gd:
            before = g.get("before")
            after = g.get("after") or ""
            term = g.get("term", "?")
            if before:
                lines.append(f"- **{term}**: ~~{before}~~ → {after}")
            else:
                lines.append(f"- **{term}**: {after}")
        lines.append("")
    ad = data.get("adr_diff") or []
    if ad:
        lines.append("**ADR 변화:**")
        for a in ad:
            lines.append(
                f"- _{a.get('status', 'proposed')}_ **{a.get('title', '?')}** — {a.get('body', '')}"
            )
        lines.append("")
    lines.append("</details>")
    rounds_entry = "\n".join(lines) + "\n"

    rounds_header = "## 🔥 Grilling Rounds"
    if rounds_header in body:
        body = re.sub(
            rf"({re.escape(rounds_header)}\s*\n)",
            lambda m: m.group(1) + "\n" + rounds_entry + "\n",
            body,
            count=1,
        )
    else:
        block = f"\n{rounds_header}\n\n{rounds_entry}\n"
        anchors = [
            "## ADR 후보 (docs/adr/ 반영 예정)",
            "## 글로사리 후보 (CONTEXT.md 반영 예정)",
            "## Next Actions",
        ]
        inserted = False
        for anchor in anchors:
            pat = re.compile(
                rf"(^{re.escape(anchor)}\s*\n.*?)(?=\n##\s|\n---\s*$|\Z)",
                re.MULTILINE | re.DOTALL,
            )
            m = pat.search(body)
            if m:
                body = body[: m.end()] + block + body[m.end():]
                inserted = True
                break
        if not inserted:
            body = body.rstrip() + "\n\n" + block

    # 5) 글로사리 후보 / ADR 후보 누적
    glossary_lines = []
    for g in gd:
        term = g.get("term", "?")
        after = g.get("after") or ""
        src = g.get("source")
        src_tag = f" _(round {next_round}" + (f" · {src}" if src else "") + ")_"
        glossary_lines.append(f"- **{term}**: {after}{src_tag}")
    body = append_to_section(body, "## 글로사리 후보 (CONTEXT.md 반영 예정)", glossary_lines)

    adr_lines = []
    for a in ad:
        adr_lines.append(
            f"- **{a.get('title', '?')}** ({a.get('status', 'proposed')}) — {a.get('body', '')} _(round {next_round})_"
        )
    body = append_to_section(body, "## ADR 후보 (docs/adr/ 반영 예정)", adr_lines)

    # 6) needs_clarification = false 면 완료 배너
    done_banner = (
        "✅ **Grilling complete** — `needs_clarification` 가 false 로 도달했습니다. "
        "다음 단계: `docs/plans/<#>-<slug>.md` PR 작성."
    )
    if not data.get("needs_clarification", True) and done_banner not in body:
        body = body.rstrip() + "\n\n---\n\n" + done_banner + "\n"

    sys.stdout.write(body)


if __name__ == "__main__":
    main()
