#!/usr/bin/env bash
# [flow:recruit] Recruit analyzer: 최근 7일 JSONL -> Gemini per-JD 추출 -> 집계 -> 주간 리포트 Issue
#
# 명명 규칙: scripts/<flow>-<action>.sh, scripts/prompts/<flow>-<action>.md
#
# 파이프라인 (A-H): load+dedup -> batch -> 추출(flash->pro 폴백) -> reconcile
#   -> 집계+WoW -> 리포트(pro) -> gh issue create(recruit-report) -> 스냅샷 커밋.
# fetcher 단계(recruit-collect)와 달리 여기서만 LLM 을 호출한다.
#
# 환경변수:
#   SINCE / UNTIL          (선택) 분석 윈도우(YYYY-MM-DD). 기본 KST 오늘 기준 최근 7일.
#   GEMINI_EXTRACT_MODEL   (선택) 추출 모델. 기본 gemini-2.5-flash.
#   GEMINI_MODEL           (선택) 리포트+폴백 모델. 기본 gemini-3-pro-preview.
#   BATCH_SIZE             (선택) 배치당 JD 수. 기본 15.
#   MAX_LLM_CALLS          (선택) 런당 LLM 호출 상한. 기본 200.
#   MAX_JDS                (선택) JD 상한(추가 샘플 캡). 0=예산에서 자동 산출.
#   RETRIES                (선택) 모델별 재시도. 기본 1.
#   GH_REPO                (선택) issue 생성 대상 owner/repo.
#   NO_COMMIT=1            (선택) 스냅샷 git commit/push 생략 (로컬).
#   NO_ISSUE=1             (선택) gh issue 대신 ISSUE_OUT(기본 /tmp/recruit-report.md)로 본문 기록.

set -uo pipefail  # -e 미사용: 단계 실패가 전체를 죽이지 않게 개별 처리

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGG="${ROOT_DIR}/scripts/recruit/aggregate.py"
EXTRACT_PROMPT="${ROOT_DIR}/scripts/prompts/recruit-extract.md"
REPORT_PROMPT="${ROOT_DIR}/scripts/prompts/recruit-analyze.md"
SKILL_FILE="${ROOT_DIR}/skills/recruit-market-analysis.SKILL.md"
DATA_DIR="${RECRUIT_DATA_DIR:-${ROOT_DIR}/data/recruit}"  # 테스트 시 임시 경로로 override
ANALYSIS_DIR="${DATA_DIR}/_analysis"

EXTRACT_MODEL="${GEMINI_EXTRACT_MODEL:-gemini-2.5-flash}"
REPORT_MODEL="${GEMINI_MODEL:-gemini-3-pro-preview}"
BATCH_SIZE="${BATCH_SIZE:-15}"
MAX_LLM_CALLS="${MAX_LLM_CALLS:-200}"
MAX_JDS="${MAX_JDS:-0}"
RETRIES="${RETRIES:-1}"

for f in "$AGG" "$EXTRACT_PROMPT" "$REPORT_PROMPT" "$SKILL_FILE"; do
  [[ -f "$f" ]] || { echo "ERROR: missing $f" >&2; exit 1; }
done

# 윈도우 계산 (이식성: GNU date -d 대신 python3)
UNTIL="${UNTIL:-$(python3 -c 'from datetime import datetime,timezone,timedelta; print(datetime.now(timezone(timedelta(hours=9))).date())')}"
SINCE="${SINCE:-$(python3 -c "from datetime import date,timedelta; print(date.fromisoformat('$UNTIL')-timedelta(days=6))")}"

RUN_DIR="$(mktemp -d)"
trap 'rm -rf "$RUN_DIR"' EXIT

LLM_CALLS=0
USED_FLASH=0
USED_PRO=0

# 모델 리스트 (추출: flash 우선 -> pro 폴백; 동일하면 1개)
EXTRACT_MODELS=("$EXTRACT_MODEL")
[[ "$REPORT_MODEL" != "$EXTRACT_MODEL" ]] && EXTRACT_MODELS+=("$REPORT_MODEL")

# 단일 gemini 호출 + 모델별 재시도. 성공 시 0.
gemini_call() {  # $1=model $2=prompt_file $3=out_file
  local model="$1" pf="$2" of="$3" attempt=0 max=$(( RETRIES + 1 ))
  while (( attempt < max )); do
    attempt=$(( attempt + 1 ))
    LLM_CALLS=$(( LLM_CALLS + 1 ))
    if gemini --yolo -m "$model" -p "$(cat "$pf")" > "$of" 2> >(tee /dev/stderr); then
      return 0
    fi
    echo "[analyze] gemini($model) attempt $attempt/$max failed" >&2
    (( attempt < max )) && sleep 5
  done
  return 1
}

# 추출: flash 시도(JSON 배열 검증) -> 실패 시 pro. 성공 시 0.
extract_batch() {  # $1=prompt_file $2=out_file
  local pf="$1" of="$2" model
  for model in "${EXTRACT_MODELS[@]}"; do
    if gemini_call "$model" "$pf" "$of" && python3 "$AGG" validate-array --in "$of"; then
      [[ "$model" == "$EXTRACT_MODEL" ]] && USED_FLASH=1 || USED_PRO=1
      return 0
    fi
    echo "[analyze] extract via $model unusable — fallback" >&2
  done
  return 1
}

jq_get() { python3 -c "import sys,json; print(json.load(sys.stdin).get('$1',''))"; }

create_issue() {  # $1=title $2=body ; echoes URL/path
  local title="$1" body="$2"
  if [[ "${NO_ISSUE:-}" == "1" ]]; then
    local out="${ISSUE_OUT:-/tmp/recruit-report.md}"
    { printf '# %s\n\n' "$title"; printf '%s\n' "$body"; } > "$out"
    echo "[analyze] NO_ISSUE=1 — wrote report to $out" >&2
    echo "$out"; return 0
  fi
  gh label create recruit-report --color "1d76db" --description "주간 채용 트렌드 리포트" >/dev/null 2>&1 || true
  local repo_flag=()
  [[ -n "${GH_REPO:-}" ]] && repo_flag=(--repo "$GH_REPO")
  gh issue create "${repo_flag[@]}" --title "$title" --body "$body" --label recruit-report
}

# ---------- A. load + dedup (+예산 기반 샘플 캡) ----------
BUDGET_JDS=$(( (MAX_LLM_CALLS - 1) * BATCH_SIZE ))
EFFECTIVE_MAX_JDS="$MAX_JDS"
if [[ "$EFFECTIVE_MAX_JDS" -eq 0 || "$EFFECTIVE_MAX_JDS" -gt "$BUDGET_JDS" ]]; then
  EFFECTIVE_MAX_JDS="$BUDGET_JDS"
fi

echo "[analyze] window ${SINCE}~${UNTIL} | extract=$EXTRACT_MODEL report=$REPORT_MODEL batch=$BATCH_SIZE max_calls=$MAX_LLM_CALLS cap_jds=$EFFECTIVE_MAX_JDS" >&2

STATS="$(python3 "$AGG" load --data-dir "$DATA_DIR" --since "$SINCE" --until "$UNTIL" --max-jds "$EFFECTIVE_MAX_JDS" --out "$RUN_DIR/deduped.jsonl")" || {
  echo "ERROR: load failed" >&2; exit 1; }
TOTAL="$(echo "$STATS" | jq_get total)"
SAMPLED="$(echo "$STATS" | jq_get sampled)"
TRUNCATED="$(echo "$STATS" | jq_get truncated)"
echo "[analyze] load stats: $STATS" >&2

SAMPLE_NOTE=""
[[ "$TRUNCATED" == "True" ]] && SAMPLE_NOTE=" · 샘플링 ${SAMPLED}/${TOTAL}"

# 엣지: 수집 데이터 없음 -> LLM 스킵, 짧은 이슈
if [[ "${SAMPLED:-0}" -eq 0 ]]; then
  echo "[analyze] no JDs in window — skipping LLM" >&2
  create_issue "채용 트렌드 주간 리포트 (${SINCE} ~ ${UNTIL})" \
    "이번 주 윈도우(**${SINCE} ~ ${UNTIL}**)에 수집된 JD 가 없습니다. \`recruit-collect\` 워크플로가 정상 동작했는지 확인하세요."
  exit 0
fi

# ---------- B. batch ----------
N_BATCHES="$(python3 "$AGG" batch --in "$RUN_DIR/deduped.jsonl" --size "$BATCH_SIZE" --out-dir "$RUN_DIR/batches")" || {
  echo "ERROR: batch failed" >&2; exit 1; }
echo "[analyze] batches: $N_BATCHES" >&2

# ---------- C/D. 배치 추출 + reconcile ----------
: > "$RUN_DIR/extracted.jsonl"
OK_TOTAL=0; FAIL_TOTAL=0; UNPROCESSED=0
for bf in "$RUN_DIR"/batches/batch_*.json; do
  [[ -f "$bf" ]] || continue
  batch_n="$(python3 -c "import json,sys; print(len(json.load(open('$bf'))))")"
  if (( LLM_CALLS >= MAX_LLM_CALLS - 1 )); then
    echo "[analyze] LLM 예산 도달 ($LLM_CALLS/$MAX_LLM_CALLS) — 남은 배치 미처리" >&2
    UNPROCESSED=$(( UNPROCESSED + batch_n ))
    continue
  fi
  PF="$RUN_DIR/prompt_$(basename "$bf" .json).txt"
  {
    cat "$EXTRACT_PROMPT"
    printf '\n\n=== SKILL CONTEXT ===\n\n'; cat "$SKILL_FILE"
    printf '\n\n=== JD BATCH (JSON) ===\n\n'; cat "$bf"
  } > "$PF"
  OF="$RUN_DIR/out_$(basename "$bf" .json).txt"
  if extract_batch "$PF" "$OF"; then
    RES="$(python3 "$AGG" reconcile --batch "$bf" --llm-out "$OF" --out "$RUN_DIR/extracted.jsonl")"
    OK_TOTAL=$(( OK_TOTAL + $(echo "$RES" | jq_get ok) ))
    FAIL_TOTAL=$(( FAIL_TOTAL + $(echo "$RES" | jq_get fail) ))
  else
    echo "[analyze] batch $(basename "$bf") 전체 실패 ($batch_n JDs)" >&2
    FAIL_TOTAL=$(( FAIL_TOTAL + batch_n ))
  fi
done
echo "[analyze] extract done: ok=$OK_TOTAL fail=$FAIL_TOTAL unprocessed=$UNPROCESSED llm_calls=$LLM_CALLS" >&2

# ---------- E. 집계 + WoW ----------
PREV="$(python3 -c "
import glob,os
u='$UNTIL'
cands=[f for f in sorted(glob.glob('$ANALYSIS_DIR/*.json')) if os.path.basename(f)[:-5] < u]
print(cands[-1] if cands else '')
")"
[[ -n "$PREV" ]] && echo "[analyze] WoW prev: $PREV" >&2
python3 "$AGG" aggregate --in "$RUN_DIR/extracted.jsonl" --skill-file "$SKILL_FILE" \
  --prev "$PREV" --since "$SINCE" --until "$UNTIL" --out "$RUN_DIR/aggregate.json" || {
  echo "ERROR: aggregate failed" >&2; exit 1; }

JD_COUNT="$(python3 -c "import json; print(json.load(open('$RUN_DIR/aggregate.json'))['meta']['jd_count'])")"
UNKNOWN_N="$(python3 -c "import json; print(json.load(open('$RUN_DIR/aggregate.json'))['unknown_skills']['distinct'])")"

# ---------- F. 리포트 (pro) ----------
RPF="$RUN_DIR/report_prompt.txt"
{
  cat "$REPORT_PROMPT"
  printf '\n\n=== SKILL CONTEXT ===\n\n'; cat "$SKILL_FILE"
  printf '\n\n=== AGGREGATE (JSON) ===\n\n'; cat "$RUN_DIR/aggregate.json"
} > "$RPF"
ROF="$RUN_DIR/report.md"
if ! gemini_call "$REPORT_MODEL" "$RPF" "$ROF" || [[ ! -s "$ROF" ]]; then
  echo "[analyze] WARN: report 생성 실패 — 집계 원본으로 대체" >&2
  {
    printf '## 리포트 생성 실패\n\nGemini 리포트 단계가 실패했습니다. 아래는 집계 원본입니다.\n\n```json\n'
    cat "$RUN_DIR/aggregate.json"
    printf '\n```\n'
  } > "$ROF"
fi

# ---------- G. 이슈 (스크립트 소유 메트릭 푸터) ----------
MODEL_USED="flash→pro"
if [[ "$USED_FLASH" == "1" && "$USED_PRO" == "0" ]]; then MODEL_USED="flash"
elif [[ "$USED_FLASH" == "0" && "$USED_PRO" == "1" ]]; then MODEL_USED="pro(폴백)"
elif [[ "$USED_FLASH" == "0" && "$USED_PRO" == "0" ]]; then MODEL_USED="없음"; fi
UNPROC_NOTE=""
[[ "$UNPROCESSED" -gt 0 ]] && UNPROC_NOTE=" · 미처리 ${UNPROCESSED}건(예산)"

FOOTER="$(printf '\n\n---\n_기간 %s ~ %s · JD %s건(수집 %s건%s) · 추출 성공 %s · 실패 %s건%s · LLM 호출 %s회(추출 %s) · unknown_skills %s종_' \
  "$SINCE" "$UNTIL" "$JD_COUNT" "$TOTAL" "$SAMPLE_NOTE" "$OK_TOTAL" "$FAIL_TOTAL" "$UNPROC_NOTE" "$LLM_CALLS" "$MODEL_USED" "$UNKNOWN_N")"

BODY="$(cat "$ROF")${FOOTER}"
ISSUE_REF="$(create_issue "채용 트렌드 주간 리포트 (${SINCE} ~ ${UNTIL})" "$BODY")"
echo "[analyze] report: $ISSUE_REF" >&2

# ---------- H. 스냅샷 커밋 (WoW 베이스라인) ----------
mkdir -p "$ANALYSIS_DIR"
cp "$RUN_DIR/aggregate.json" "$ANALYSIS_DIR/${UNTIL}.json"
if [[ "${NO_COMMIT:-}" == "1" ]]; then
  echo "[analyze] NO_COMMIT=1 — 스냅샷 로컬 저장만 ($ANALYSIS_DIR/${UNTIL}.json)" >&2
  exit 0
fi
cd "$ROOT_DIR"
if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
  git config user.name "github-actions[bot]"
  git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
fi
git add "data/recruit/_analysis/${UNTIL}.json"
if git diff --cached --quiet; then
  echo "[analyze] 스냅샷 변경 없음 — commit 생략" >&2
else
  git commit -m "chore(recruit): analyze snapshot ${UNTIL}" >&2
  git push >&2
  echo "[analyze] 스냅샷 commit/push 완료" >&2
fi
