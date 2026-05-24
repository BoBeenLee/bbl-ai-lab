#!/usr/bin/env python3
"""
이슈 본문 in-place 갱신 헬퍼. idea-grill.sh 가 호출.

사용:
    python3 scripts/_idea_grill_body.py \
        BODY_PATH JSON_PATH NEXT_ROUND GRILL_LEVEL CHAT_ID MSG_ID [MANUAL_FOCUS]

STDOUT 에 갱신된 마크다운 본문을 출력한다.
입력:
    BODY_PATH    현재 이슈 본문 마크다운 파일
    JSON_PATH    idea-grill 프롬프트의 Gemini 출력 JSON 파일
    NEXT_ROUND   이번 라운드 번호 (integer)
    GRILL_LEVEL  현재 grill_level (보존)
    CHAT_ID      Telegram chat id (grill-meta 보존)
    MSG_ID       Telegram message id (grill-meta 보존)
    MANUAL_FOCUS (옵션) /grill <focus> 인자. 배너 focus 갱신에 사용.
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


def make_banner(round_num: int, grill_level: str, focus: str) -> str:
    """idea-elaborate.sh 의 초기 배너와 동일한 포맷. 매 라운드마다 갱신된다."""
    focus_suffix = f" · 다음 권장 focus: **{focus}**" if focus else ""
    return (
        f"> 🔥 **Grilling round {round_num}** (level: {grill_level}{focus_suffix})\n"
        ">\n"
        "> **이슈 진행 방법:**\n"
        "> 1. 아래 **Open Questions** 중 답할 수 있는 것부터 자유 형식 코멘트로 답변. 한 코멘트에 여러 질문 답해도 OK.\n"
        "> 2. 답변이 끝나면 **새 코멘트 첫 줄**에 `/grill` 입력 → 다음 grilling 라운드 자동 트리거.\n"
        ">    - 특정 영역만 집중하려면 `/grill <focus>` (예: `/grill 성공 지표`).\n"
        "> 3. `/grill` 없는 일반 코멘트는 워크플로가 무시합니다 (비용 0).\n"
        "> 4. 라운드는 무한 반복 가능. `needs_clarification` 이 false 가 되면 `grilled` 라벨이 붙고 ✅ 완료 배너가 추가됩니다. 그 시점 또는 그 전이라도 plan PR 작성으로 넘어가도 됩니다.\n"
    )


def main():
    args = sys.argv[1:]
    if len(args) < 6:
        print("usage: _idea_grill_body.py BODY JSON ROUND LEVEL CHAT MSG [FOCUS]", file=sys.stderr)
        sys.exit(2)
    body_path, json_path, next_round_s, grill_level, chat_id, msg_id = args[:6]
    manual_focus = args[6].strip() if len(args) >= 7 else ""
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

    # 2.5) 배너 교체: 매 라운드마다 round / focus 를 최신으로 갱신
    #     manual_focus(이번 /grill <focus>) > LLM 의 round_summary 에 명시된 focus > 빈 문자열 순으로 우선.
    focus = manual_focus or ""
    new_banner = make_banner(next_round, grill_level, focus)
    banner_pat = re.compile(
        r"^>\s*🔥\s*\*\*Grilling round\b[^\n]*(?:\n>[^\n]*)*\n?",
        re.MULTILINE,
    )
    if banner_pat.search(body):
        body = banner_pat.sub(lambda m: new_banner, body, count=1)
    else:
        # 배너가 사라진 경우 (수동 편집 등) → Open Questions 헤더 직전에 삽입
        body = re.sub(
            r"(^##\s*Open Questions\b)",
            new_banner + r"\n\1",
            body,
            count=1,
            flags=re.MULTILINE,
        )

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
