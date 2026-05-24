#!/usr/bin/env bash
# [flow:idea] Idea grilling followup: 이슈 코멘트에 /grill 이 들어왔을 때 다음 라운드 진행.
#
# 명명 규칙: scripts/<flow>-<action>.sh, scripts/prompts/<flow>-<action>.md
#
# 입력 (workflow 가 env 로 전달):
#   ISSUE_NUMBER          (필수) 대상 이슈 번호
#   TRIGGER_COMMENT_ID    (필수) /grill 코멘트의 id (중복 방지용)
#   TRIGGER_COMMENT_BODY  (필수) /grill 코멘트 본문 (첫 줄에서 manual_focus 파싱)
#   GH_TOKEN              (필수) gh CLI 인증
#   GH_REPO               (선택) owner/repo. 미지정시 GITHUB_REPOSITORY.
#   TG_BOT_TOKEN          (선택) 텔레그램 회신용. 비어 있으면 회신 생략.
#   GEMINI_MODEL          (선택) 기본 gemini-3-pro-preview.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PROMPT_FILE="${ROOT_DIR}/scripts/prompts/idea-grill.md"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-3-pro-preview}"
REPO_PATH="${GH_REPO:-${GITHUB_REPOSITORY:-BoBeenLee/bbl-ai-lab}}"

for v in ISSUE_NUMBER TRIGGER_COMMENT_ID TRIGGER_COMMENT_BODY; do
  if [[ -z "${!v:-}" ]]; then
    echo "ERROR: $v is empty" >&2
    exit 1
  fi
done

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "ERROR: prompt file not found: $PROMPT_FILE" >&2
  exit 1
fi

# /grill 첫 줄 파싱: ^/grill(\s+<focus>)?$
TRIGGER_FIRST_LINE="$(printf '%s' "$TRIGGER_COMMENT_BODY" | head -n 1)"
if [[ ! "$TRIGGER_FIRST_LINE" =~ ^/grill([[:space:]]+([^[:space:]].*))?[[:space:]]*$ ]]; then
  echo "[grill] trigger comment first line does not match /grill pattern — exiting" >&2
  echo "[grill] first_line: $TRIGGER_FIRST_LINE" >&2
  exit 0
fi
MANUAL_FOCUS="${BASH_REMATCH[2]:-}"
# trim
MANUAL_FOCUS="$(printf '%s' "$MANUAL_FOCUS" | sed -E 's/^[[:space:]]+//;s/[[:space:]]+$//')"

# trigger 코멘트 본문에서 첫 줄(=/grill ...) 제거한 나머지 = 추가 답변
TRIGGER_REST="$(printf '%s' "$TRIGGER_COMMENT_BODY" | tail -n +2)"

echo "[grill] issue=#${ISSUE_NUMBER} trigger_comment=${TRIGGER_COMMENT_ID} manual_focus='${MANUAL_FOCUS}'" >&2

# 이슈 상태 적재
TMP_ISSUE="$(mktemp)"
trap 'rm -f "$TMP_ISSUE" "${TMP_PROMPT:-}" "${TMP_OUT:-}" "${TMP_JSON:-}" "${TMP_BODY:-}"' EXIT

gh issue view "$ISSUE_NUMBER" \
  --repo "$REPO_PATH" \
  --json number,body,labels,comments,author \
  > "$TMP_ISSUE"

ISSUE_BODY="$(jq -r '.body' "$TMP_ISSUE")"

# grill-meta HTML 코멘트에서 round / chat_id / grill_level 파싱
META_JSON="$(python3 - "$TMP_ISSUE" <<'PY'
import json, re, sys

issue = json.load(open(sys.argv[1], "r", encoding="utf-8"))
body = issue.get("body") or ""
m = re.search(r"<!--\s*bbl-grill-meta\s*\n(.*?)\n-->", body, re.DOTALL)
meta = {"round": 1, "grill_level": "standard", "chat_id": "", "msg_id": ""}
if m:
    for line in m.group(1).splitlines():
        if ":" not in line: continue
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip()
try:
    meta["round"] = int(meta.get("round") or 1)
except Exception:
    meta["round"] = 1
print(json.dumps(meta))
PY
)"

PREV_ROUND="$(printf '%s' "$META_JSON" | jq -r '.round')"
CHAT_ID="$(printf '%s' "$META_JSON" | jq -r '.chat_id // ""')"
MSG_ID="$(printf '%s' "$META_JSON" | jq -r '.msg_id // ""')"
GRILL_LEVEL="$(printf '%s' "$META_JSON" | jq -r '.grill_level // "standard"')"
NEXT_ROUND=$(( PREV_ROUND + 1 ))

echo "[grill] prev_round=${PREV_ROUND} next_round=${NEXT_ROUND} grill_level=${GRILL_LEVEL}" >&2

# 이전 /grill 이후의 답변 코멘트 수집
# - 모든 코멘트를 시간순으로 보고
# - 직전 /grill 코멘트 다음부터 트리거 /grill 직전까지의 비-/grill 코멘트만 수집
ANSWERS_BLOCK="$(python3 - "$TMP_ISSUE" "$TRIGGER_COMMENT_ID" <<'PY'
import json, sys

issue = json.load(open(sys.argv[1], "r", encoding="utf-8"))
trigger_id = sys.argv[2]
# gh 가 주는 comment id 는 보통 GraphQL node id 또는 숫자. createdAt 순으로 정렬.
comments = sorted(issue.get("comments") or [], key=lambda c: c.get("createdAt", ""))

# trigger 코멘트 위치 찾기 (id 매칭은 부분 일치 — gh 가 다양한 형태로 주므로)
def is_trigger(c):
    cid = str(c.get("id") or c.get("databaseId") or "")
    return cid == trigger_id or cid.endswith(trigger_id) or trigger_id.endswith(cid)

trigger_idx = next((i for i, c in enumerate(comments) if is_trigger(c)), None)
if trigger_idx is None:
    # 트리거 코멘트가 listing 에 안 잡힌 경우 — 모든 코멘트 사용
    trigger_idx = len(comments)

# trigger 이전 코멘트 중 마지막 /grill 의 인덱스
prev_grill_idx = -1
for i in range(trigger_idx - 1, -1, -1):
    body = (comments[i].get("body") or "").lstrip()
    first = body.split("\n", 1)[0].strip()
    if first == "/grill" or first.startswith("/grill "):
        prev_grill_idx = i
        break

# (prev_grill_idx, trigger_idx) 사이의 비-/grill 코멘트
collected = []
for i in range(prev_grill_idx + 1, trigger_idx):
    c = comments[i]
    body = (c.get("body") or "")
    first = body.lstrip().split("\n", 1)[0].strip()
    if first == "/grill" or first.startswith("/grill "):
        continue  # 다른 /grill 이 사이에 있으면 스킵 (이중 트리거 방지)
    login = (c.get("author") or {}).get("login", "anonymous")
    ts = c.get("createdAt", "")
    collected.append(f"--- comment by {login} at {ts} ---\n{body}".rstrip())

print("\n\n".join(collected))
PY
)"

# previous open questions 파싱: "## Open Questions" 섹션의 "- [ ] ..." 라인
TMP_BODY_FILE="$(mktemp)"
printf '%s' "$ISSUE_BODY" > "$TMP_BODY_FILE"
PREV_OPEN_QS_JSON="$(python3 - "$TMP_BODY_FILE" <<'PY'
import json, re, sys
body = open(sys.argv[1], "r", encoding="utf-8").read()
m = re.search(r"^##\s*Open Questions\s*\n(.*?)(?=\n##\s|\n---\s*$|\Z)", body, re.MULTILINE | re.DOTALL)
qs = []
if m:
    for line in m.group(1).splitlines():
        mm = re.match(r"^\s*-\s*\[[ xX]\]\s+(.*?)\s*$", line)
        if mm and mm.group(1):
            qs.append(mm.group(1))
print(json.dumps(qs, ensure_ascii=False))
PY
)"
rm -f "$TMP_BODY_FILE"

echo "[grill] previous open_questions count: $(printf '%s' "$PREV_OPEN_QS_JSON" | jq 'length')" >&2

# 프롬프트 조립
TMP_PROMPT="$(mktemp)"
{
  cat "$PROMPT_FILE"
  printf '\n\n=== ISSUE BODY ===\n\n%s\n' "$ISSUE_BODY"
  printf '\n\n=== PREVIOUS OPEN QUESTIONS ===\n\n%s\n' "$PREV_OPEN_QS_JSON"
  printf '\n\n=== ANSWER COMMENTS ===\n\n'
  if [[ -n "$ANSWERS_BLOCK" ]]; then
    printf '%s\n' "$ANSWERS_BLOCK"
  fi
  if [[ -n "$TRIGGER_REST" ]]; then
    printf -- '--- additional context from /grill comment itself ---\n%s\n' "$TRIGGER_REST"
  fi
  printf '\n\n=== MANUAL FOCUS ===\n\n%s\n' "$MANUAL_FOCUS"
  printf '\n\n=== PREVIOUS ROUND ===\n\n%s\n' "$PREV_ROUND"
} > "$TMP_PROMPT"

echo "[grill] prompt size: $(wc -c < "$TMP_PROMPT") bytes" >&2

# Gemini 호출 (elaborate.sh 와 동일한 재시도 패턴)
TMP_OUT="$(mktemp)"
RETRIES="${RETRIES:-1}"
MAX_ATTEMPTS=$(( RETRIES + 1 ))
attempt=0
gemini_ok=0
while (( attempt < MAX_ATTEMPTS )); do
  attempt=$(( attempt + 1 ))
  if gemini --yolo -m "$GEMINI_MODEL" -p "$(cat "$TMP_PROMPT")" > "$TMP_OUT" 2> >(tee /dev/stderr); then
    gemini_ok=1
    break
  fi
  echo "[grill] gemini attempt $attempt/$MAX_ATTEMPTS failed" >&2
  if (( attempt < MAX_ATTEMPTS )); then
    echo "[grill] retrying in 5s..." >&2
    sleep 5
  fi
done

if (( gemini_ok != 1 )); then
  echo "ERROR: gemini call failed after $MAX_ATTEMPTS attempts" >&2
  cat "$TMP_OUT" >&2 || true
  exit 1
fi

# JSON 추출
TMP_JSON="$(mktemp)"
python3 - "$TMP_OUT" > "$TMP_JSON" <<'PY'
import re, sys
raw = open(sys.argv[1], "r", encoding="utf-8").read()
m = re.search(r"```json\s*(.*?)```", raw, re.DOTALL)
if m:
    sys.stdout.write(m.group(1))
else:
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        sys.stdout.write(m.group(0))
    else:
        sys.stdout.write(raw)
PY

if ! jq empty "$TMP_JSON" 2>/dev/null; then
  echo "ERROR: gemini did not return valid JSON. raw output:" >&2
  cat "$TMP_OUT" >&2
  exit 1
fi

NEEDS_CLARIFY="$(jq -r '.needs_clarification // true' "$TMP_JSON")"
ROUND_SUMMARY="$(jq -r '.round_summary // ""' "$TMP_JSON")"

echo "[grill] needs_clarification=${NEEDS_CLARIFY} round=${NEXT_ROUND}" >&2

# 이슈 본문 in-place 갱신: 모든 마크다운 조작은 scripts/_idea_grill_body.py 에 위임
TMP_BODY="$(mktemp)"
printf '%s' "$ISSUE_BODY" > "$TMP_BODY"

NEW_BODY="$(python3 "${ROOT_DIR}/scripts/_idea_grill_body.py" \
  "$TMP_BODY" "$TMP_JSON" "$NEXT_ROUND" "$GRILL_LEVEL" "$CHAT_ID" "$MSG_ID" "$MANUAL_FOCUS")"

if [[ -z "$NEW_BODY" ]]; then
  echo "ERROR: body manipulation produced empty output" >&2
  exit 1
fi

# 본문 갱신
gh issue edit "$ISSUE_NUMBER" \
  --repo "$REPO_PATH" \
  --body "$NEW_BODY"

echo "[grill] issue body updated (round $NEXT_ROUND)" >&2

# 라벨 전환
if [[ "$NEEDS_CLARIFY" == "false" ]]; then
  gh label create grilled --repo "$REPO_PATH" --color "0e8a16" --description "Idea has been grilled to closure" >/dev/null 2>&1 || true
  gh issue edit "$ISSUE_NUMBER" --repo "$REPO_PATH" --remove-label needs-clarification >/dev/null 2>&1 || true
  gh issue edit "$ISSUE_NUMBER" --repo "$REPO_PATH" --add-label grilled >/dev/null 2>&1 || true
fi

# 남은 Open Questions 수 (remaining + new)
OPEN_Q_LEFT="$(jq -r '((.remaining_questions // []) + (.new_questions // [])) | length' "$TMP_JSON")"

# Round 진행 알림 코멘트 — 다음 단계 안내 포함
if [[ "$NEEDS_CLARIFY" == "false" ]]; then
  ROUND_COMMENT="✅ Grilling round ${NEXT_ROUND} 완료 — 모든 핵심 질문이 정리되었습니다."
  if [[ -n "$ROUND_SUMMARY" ]]; then
    ROUND_COMMENT="$ROUND_COMMENT"$'\n\n'"$ROUND_SUMMARY"
  fi
  ROUND_COMMENT="$ROUND_COMMENT"$'\n\n'"**다음 단계:**"$'\n'"- 이슈 본문의 **글로사리 후보** → \`CONTEXT.md\`, **ADR 후보** → \`docs/adr/000N-*.md\` 로 옮기는 plan PR 을 작성하세요."$'\n'"- plan PR 작성 가이드: [docs/plans/README.md](https://github.com/${REPO_PATH}/blob/main/docs/plans/README.md)"$'\n'"- 더 grilling 이 필요하다고 판단되면 언제든 새 코멘트 첫 줄에 \`/grill\` 으로 라운드 재개 가능."
else
  ROUND_COMMENT="🔥 Grilling round ${NEXT_ROUND} 완료 — 남은 Open Questions: **${OPEN_Q_LEFT}개**"
  if [[ -n "$ROUND_SUMMARY" ]]; then
    ROUND_COMMENT="$ROUND_COMMENT"$'\n\n'"$ROUND_SUMMARY"
  fi
  ROUND_COMMENT="$ROUND_COMMENT"$'\n\n'"**다음 단계:**"$'\n'"1. 위 이슈 본문의 갱신된 **## Open Questions** 를 확인하세요."$'\n'"2. 답할 수 있는 질문에 자유 형식 코멘트로 답변하세요 (질문 인용 / 한 코멘트에 여러 질문 답변 모두 OK)."$'\n'"3. 답변이 끝나면 **새 코멘트 첫 줄**에 \`/grill\` (특정 영역 집중은 \`/grill <focus>\`) → round $((NEXT_ROUND + 1)) 자동 시작."$'\n'"4. 충분하다 판단되면 \`/grill\` 없이 plan PR 작성으로 바로 넘어가도 됩니다."
fi

gh issue comment "$ISSUE_NUMBER" --repo "$REPO_PATH" --body "$ROUND_COMMENT" >/dev/null

# Telegram 회신 (옵션)
if [[ -n "${TG_BOT_TOKEN:-}" && -n "$CHAT_ID" ]]; then
  ISSUE_URL="https://github.com/${REPO_PATH}/issues/${ISSUE_NUMBER}"
  REPLY_TEXT="🔥 Grilling round ${NEXT_ROUND}: ${ISSUE_URL}"
  if [[ -n "$ROUND_SUMMARY" ]]; then
    REPLY_TEXT="$REPLY_TEXT"$'\n'"$ROUND_SUMMARY"
  fi
  if [[ "$NEEDS_CLARIFY" == "false" ]]; then
    REPLY_TEXT="$REPLY_TEXT"$'\n''(Grilling 완료 — 다음 단계: plan PR)'
  fi

  TG_PAYLOAD="$(
    jq -nc \
      --arg chat_id "$CHAT_ID" \
      --arg text "$REPLY_TEXT" \
      --arg reply_to "${MSG_ID:-}" \
      '{
        chat_id: ($chat_id | tonumber),
        text: $text,
        disable_web_page_preview: false
      } + (if ($reply_to | length) > 0 then { reply_to_message_id: ($reply_to | tonumber) } else {} end)'
  )"

  curl -fsS -X POST \
    "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
    -H "Content-Type: application/json" \
    -d "$TG_PAYLOAD" >/dev/null \
    || echo "[grill] WARN: telegram reply failed" >&2
fi

echo "[grill] done."
