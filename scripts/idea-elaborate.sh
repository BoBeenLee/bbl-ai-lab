#!/usr/bin/env bash
# [flow:idea] Idea elaborator: Gemini CLI 호출 -> JSON 파싱 -> GitHub Issue 생성 -> Telegram 회신
#
# 명명 규칙: scripts/<flow>-<action>.sh, scripts/prompts/<flow>-<action>.md
#
# 필요한 환경변수:
#   IDEA_TEXT       (필수) 사용자 원문
#   CHAT_ID         (선택) Telegram chat id (회신용)
#   MSG_ID          (선택) Telegram message id (reply 대상)
#   GH_TOKEN        (필수) gh CLI 인증용 (GitHub Action에서는 secrets.GITHUB_TOKEN)
#   GH_REPO         (선택) issue를 생성할 owner/repo. 미지정시 현재 레포.
#   TG_BOT_TOKEN    (선택) Telegram 답장 발송용. 비어있으면 답장 생략.
#   GEMINI_MODEL    (선택) gemini 모델 지정. 기본 gemini-2.5-pro.
#   SKILL_FILE      (선택) skill 컨텍스트 파일 경로. 기본 skills/office-hours.SKILL.md.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PROMPT_FILE="${ROOT_DIR}/scripts/prompts/idea-elaborate.md"
SKILL_FILE="${SKILL_FILE:-${ROOT_DIR}/skills/office-hours.SKILL.md}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.5-pro}"

if [[ -z "${IDEA_TEXT:-}" ]]; then
  echo "ERROR: IDEA_TEXT is empty" >&2
  exit 1
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "ERROR: prompt file not found: $PROMPT_FILE" >&2
  exit 1
fi

if [[ ! -f "$SKILL_FILE" ]]; then
  echo "ERROR: skill file not found: $SKILL_FILE" >&2
  exit 1
fi

# 단일 프롬프트 조립 (system + skill context + user idea)
TMP_PROMPT="$(mktemp)"
trap 'rm -f "$TMP_PROMPT" "${TMP_OUT:-}" "${TMP_JSON:-}"' EXIT

{
  cat "$PROMPT_FILE"
  printf '\n\n=== SKILL CONTEXT ===\n\n'
  cat "$SKILL_FILE"
  printf '\n\n=== USER IDEA ===\n\n%s\n' "$IDEA_TEXT"
} > "$TMP_PROMPT"

echo "[elaborate] gemini model=$GEMINI_MODEL skill=$(basename "$SKILL_FILE")" >&2
echo "[elaborate] prompt size: $(wc -c < "$TMP_PROMPT") bytes" >&2

TMP_OUT="$(mktemp)"

# gemini --yolo: 모든 도구 자동 승인. -m: 모델 지정. -p: 프롬프트 inline.
# (stdin 리디렉션 대신 -p로 비대화형 모드 보장)
# preview 모델의 단발성 502/429 흡수를 위해 1회 재시도. RETRIES env로 조절 가능 (기본 1).
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
  echo "[elaborate] gemini attempt $attempt/$MAX_ATTEMPTS failed" >&2
  if (( attempt < MAX_ATTEMPTS )); then
    echo "[elaborate] retrying in 5s..." >&2
    sleep 5
  fi
done

if (( gemini_ok != 1 )); then
  echo "ERROR: gemini call failed after $MAX_ATTEMPTS attempts" >&2
  cat "$TMP_OUT" >&2 || true
  exit 1
fi

# JSON 추출: ```json ... ``` 펜스가 있으면 안쪽만, 없으면 첫 '{' ~ 마지막 '}' (greedy)
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

TITLE="$(jq -r '.title' "$TMP_JSON")"
NEEDS_CLARIFY="$(jq -r '.needs_clarification // false' "$TMP_JSON")"

# Issue 본문 마크다운 생성
BODY="$(
  jq -r --arg raw "$IDEA_TEXT" '
    "> 원문 (Telegram):\n> " + ($raw | gsub("\n";"\n> ")) + "\n\n" +
    "## 요약\n" + (.summary // "") + "\n\n" +
    "## 문제\n" + (.problem // "") + "\n\n" +
    "## 목표\n" + (.goal // "") + "\n\n" +
    "## Non-goals\n" + (((.non_goals // []) | map("- " + .) | join("\n")) // "") + "\n\n" +
    "## 접근\n" + (.approach // "") + "\n\n" +
    "## 리스크\n" + (((.risks // []) | map("- " + .) | join("\n")) // "") + "\n\n" +
    "## Open Questions\n" + (((.open_questions // []) | map("- [ ] " + .) | join("\n")) // "") + "\n\n" +
    "## Next Actions\n" + (((.next_actions // []) | map("- [ ] " + .) | join("\n")) // "") + "\n"
  ' "$TMP_JSON"
)"

# 라벨 구성
LABELS="idea"
if [[ "$NEEDS_CLARIFY" == "true" ]]; then
  LABELS="$LABELS,needs-clarification"
fi

# 라벨이 레포에 없으면 자동 생성 (실패해도 무시)
IFS=',' read -r -a LABEL_ARR <<< "$LABELS"
for L in "${LABEL_ARR[@]}"; do
  gh label create "$L" --color "ededed" >/dev/null 2>&1 || true
done

REPO_FLAG=()
if [[ -n "${GH_REPO:-}" ]]; then
  REPO_FLAG=(--repo "$GH_REPO")
fi

ISSUE_URL="$(
  gh issue create \
    "${REPO_FLAG[@]}" \
    --title "$TITLE" \
    --body "$BODY" \
    --label "$LABELS"
)"

echo "[elaborate] issue created: $ISSUE_URL" >&2
echo "$ISSUE_URL"

# Telegram 회신 (선택)
if [[ -n "${TG_BOT_TOKEN:-}" && -n "${CHAT_ID:-}" ]]; then
  REPLY_TEXT="아이디어 구체화 완료: $ISSUE_URL"
  if [[ "$NEEDS_CLARIFY" == "true" ]]; then
    REPLY_TEXT="$REPLY_TEXT"$'\n''(추가 확인이 필요한 항목이 있습니다. Issue 본문의 Open Questions를 확인해 주세요.)'
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
    || echo "[elaborate] WARN: telegram reply failed" >&2
fi
