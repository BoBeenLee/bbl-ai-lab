#!/usr/bin/env bash
# [flow:recruit] Recruit collector: 플랫폼별 fetcher 실행 -> JSONL 적재 -> git commit
#
# 명명 규칙: scripts/<flow>-<action>.sh, scripts/recruit/fetchers/<platform>.py
#
# fetcher 단계에서는 LLM 을 호출하지 않는다. raw JD 를 정규화해
#   data/recruit/<YYYY-MM-DD(KST)>/<region>/<platform>.jsonl
# 로 적재하고 커밋한다. 구조화/집계/리포트는 recruit-analyze 단계(별도)의 책임.
#
# 환경변수:
#   PLATFORMS   (선택) 콤마 구분. 기본 "remoteok,hn-hiring,wanted,jumpit"
#   MAX         (선택) 플랫폼당 최대 레코드. 기본 200
#   COLLECT_DATE(선택) 적재 날짜(YYYY-MM-DD). 기본 KST 오늘
#   NO_COMMIT   (선택) "1" 이면 git commit/push 생략 (로컬 dry-run)
#   GH_ACTIONS  (자동) Actions 환경이면 git author 를 봇으로 설정

set -uo pipefail  # -e 미사용: 단일 플랫폼 실패가 전체를 죽이지 않도록 개별 처리

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FETCH_DIR="${ROOT_DIR}/scripts/recruit/fetchers"

PLATFORMS="${PLATFORMS:-remoteok,hn-hiring,wanted,jumpit,jobkorea,greenhouse,ashby,lever}"
MAX="${MAX:-200}"
DATE="${COLLECT_DATE:-$(TZ=Asia/Seoul date +%F)}"

# platform slug -> "fetcher_file region"
platform_spec() {
  case "$1" in
    remoteok)   echo "remoteok.py GLOBAL" ;;
    hn-hiring)  echo "hn_hiring.py GLOBAL" ;;
    wanted)     echo "wanted.py KR" ;;
    jumpit)     echo "jumpit.py KR" ;;
    jobkorea)   echo "jobkorea.py KR" ;;
    greenhouse) echo "greenhouse.py GLOBAL" ;;
    ashby)      echo "ashby.py GLOBAL" ;;
    lever)      echo "lever.py GLOBAL" ;;
    *)          echo "" ;;
  esac
}

echo "[collect] date=$DATE platforms=$PLATFORMS max=$MAX" >&2

total=0
written_any=0
IFS=',' read -r -a PLAT_ARR <<< "$PLATFORMS"
for raw in "${PLAT_ARR[@]}"; do
  p="$(echo "$raw" | tr -d '[:space:]')"
  [[ -z "$p" ]] && continue
  spec="$(platform_spec "$p")"
  if [[ -z "$spec" ]]; then
    echo "[collect] WARN: unknown platform '$p' — skip" >&2
    continue
  fi
  read -r script region <<< "$spec"
  out="${ROOT_DIR}/data/recruit/${DATE}/${region}/${p}.jsonl"
  mkdir -p "$(dirname "$out")"

  echo "[collect] -> $p ($region) via $script" >&2
  if n="$(python3 "${FETCH_DIR}/${script}" --out "$out" --max "$MAX" 2>>/tmp/recruit-collect.log)"; then
    n="${n//[^0-9]/}"; n="${n:-0}"
    echo "[collect]    $p: $n records -> data/recruit/${DATE}/${region}/${p}.jsonl" >&2
    total=$(( total + n ))
    [[ "$n" -gt 0 ]] && written_any=1
    # 0건이면 빈 파일은 남기지 않는다 (커밋 노이즈 방지)
    [[ "$n" -eq 0 ]] && rm -f "$out"
  else
    echo "[collect] WARN: $p fetcher exited non-zero — skip (see /tmp/recruit-collect.log)" >&2
    rm -f "$out"
  fi
done

echo "[collect] total records: $total" >&2

if [[ "${NO_COMMIT:-}" == "1" ]]; then
  echo "[collect] NO_COMMIT=1 — skipping git commit" >&2
  exit 0
fi

if [[ "$written_any" -ne 1 ]]; then
  echo "[collect] nothing collected — no commit" >&2
  exit 0
fi

# git commit (신규 패턴: 기존 flow 와 달리 데이터를 레포에 적재)
cd "$ROOT_DIR"
if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
  git config user.name "github-actions[bot]"
  git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
fi
git add data/recruit/
if git diff --cached --quiet; then
  echo "[collect] no staged changes — nothing to commit" >&2
  exit 0
fi
git commit -m "chore(recruit): collect ${DATE} [${PLATFORMS}] (${total} JDs)" >&2
git push >&2
echo "[collect] committed & pushed ${total} JDs for ${DATE}" >&2
