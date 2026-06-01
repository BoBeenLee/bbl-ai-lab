# `recruit-analyze` flow

`recruit-collect` 가 적재한 raw JD JSONL 을 주간 단위로 읽어, Gemini 로 per-JD 구조화 추출 → Python 집계(skill top-N, 직군×권역, WoW) → 주간 트렌드 리포트를 `recruit-report` 라벨 GitHub Issue 로 발행한다. 이 단계에서만 LLM 을 호출한다.

이슈 #16 / 플랜 [`docs/plans/16-recruit-market-data-collection.md`](plans/16-recruit-market-data-collection.md) 의 PoC 분석부 (수집부는 [recruit-collect.md](recruit-collect.md)).

## 트리거

| 입력 형태 | 예시 | 비고 |
|-----------|------|------|
| cron | 매주 월 00:00 UTC (= 09:00 KST) | 최근 7일 윈도우 |
| `workflow_dispatch` | `gh workflow run recruit-analyze.yml -f since=2026-05-26 -f until=2026-06-01` | 수동/E2E |
| `repository_dispatch` | event_type **`recruit-analyze`** | 텔레그램 `/recruit report` (worker 라우팅, 후속 라운드) |

## 파이프라인 (`scripts/recruit-analyze.sh`)

1. **load + dedup** — `[SINCE,UNTIL]`(기본 최근 7일) 의 `data/recruit/<date>/<region>/<platform>.jsonl` 글롭 → `(platform, external_id)` 로 dedup(최신 `collected_at` 유지) → `jd_id = "<platform>:<external_id>"` 부여.
2. **샘플 캡** — LLM 호출 예산(`MAX_LLM_CALLS`)에서 JD 상한 산출(`(MAX_LLM_CALLS-1)*BATCH_SIZE`). 초과 시 권역→플랫폼 라운드로빈 stratified 샘플 (로그 `샘플링: N중 M`).
3. **batch 추출** — `BATCH_SIZE`(기본 15) JD/콜. `gemini-2.5-flash` 시도 → 출력이 유효 JSON 배열이 아니면 `gemini-3-pro-preview` 폴백. 출력→JD 매핑은 echo 된 `jd_id` set 재조정(인덱스 미사용): 환각/누락/enum위반은 실패로 카운트.
4. **집계 + WoW** — `aggregate.py` 가 정규화 사전 적용 후 집계. `UNTIL` 직전 최신 스냅샷을 baseline 으로 주간 변화 계산.
5. **리포트** — `gemini-3-pro-preview` 가 집계 JSON → 마크다운 리포트. 본문 끝에 **스크립트 소유 메트릭 푸터**(기간/JD수/추출 성공·실패/LLM 호출 수/unknown_skills) 부착 — LLM 이 못 지어내는 권위 수치.
6. **이슈 + 스냅샷** — `gh issue create --label recruit-report`. `aggregate.json` 을 `data/recruit/_analysis/<UNTIL>.json` 로 커밋(다음 주 WoW baseline).

JD 0건이면 LLM 을 건너뛰고 "수집 데이터 없음" 짧은 이슈만 발행한다.

## per-JD 추출 스키마

```jsonc
{
  "jd_id": "<platform>:<external_id>",   // 입력 echo
  "role_category": "engineer|pm|designer|data|ml|devops|qa|security|other",
  "seniority": "intern|junior|mid|senior|lead|head",
  "skills_required": ["..."],
  "skills_preferred": ["..."],
  "domain": "fintech|commerce|saas|...",
  "work_mode": "onsite|hybrid|remote|unspecified",
  "compensation_hint": "...|null"
}
```

스킬은 원문 표기 그대로 추출하고, 동의어 통합은 `aggregate.py` 가 `skills/recruit-market-analysis.SKILL.md` 의 정규화 사전으로 후처리한다. 사전에 없는 토큰은 `unknown_skills` 로 누적되어 리포트/스냅샷에 남고 주기적으로 사람이 사전에 반영한다.

## 구성 파일

| 경로 | 역할 |
|------|------|
| `.github/workflows/recruit-analyze.yml` | cron + dispatch, OAuth 복원, `contents:write`+`issues:write` |
| `scripts/recruit-analyze.sh` | 오케스트레이터 |
| `scripts/recruit/aggregate.py` | load/dedup/sample + batch + reconcile + aggregate (stdlib) |
| `scripts/prompts/recruit-extract.md` | per-JD 추출 프롬프트 |
| `scripts/prompts/recruit-analyze.md` | 주간 리포트 프롬프트 |
| `skills/recruit-market-analysis.SKILL.md` | 도메인 컨텍스트 + 스킬 정규화 사전 |

## 환경변수

`SINCE`/`UNTIL`(기본 최근 7일 KST), `GEMINI_EXTRACT_MODEL`(기본 `gemini-2.5-flash`), `GEMINI_MODEL`(기본 `gemini-3-pro-preview`, 리포트+폴백), `BATCH_SIZE`(15), `MAX_LLM_CALLS`(200), `MAX_JDS`(0=예산 자동), `NO_COMMIT=1`(스냅샷 커밋 생략), `NO_ISSUE=1`(이슈 대신 `ISSUE_OUT` 파일 기록), `RECRUIT_DATA_DIR`(데이터 경로 override, 테스트용).

## 로컬 검증 (오프라인, 실 Gemini 불필요)

PATH 에 가짜 `gemini`(호출 카운트 + jd_id echo 배열 반환) 를 두고:

```bash
# 더미 7일치 생성 후
RECRUIT_DATA_DIR=/tmp/dd NO_COMMIT=1 NO_ISSUE=1 ISSUE_OUT=/tmp/r.md \
  SINCE=2026-05-26 UNTIL=2026-06-01 BATCH_SIZE=2 bash scripts/recruit-analyze.sh
```

검증 항목: ≤200 호출(`ceil(unique/BATCH)+1`), 비용가드(`MAX_LLM_CALLS=2 BATCH_SIZE=1` → `샘플링` 로그), 추출 실패 카운트(bad-enum 유도), flash→pro 폴백(`gemini-2.5-flash` 만 exit 1), WoW(`_analysis/` 에 이전 스냅샷). `aggregate.py` 각 서브커맨드는 fixture 로 단독 테스트 가능.

## 후속 (이번 라운드 미포함)

- worker 텔레그램 sub-command 라우팅 (`/recruit collect`, `/recruit report`) + `README.md` flow 표.
- `gemini-2.5-flash` OAuth 계정 접근 가능 여부 실측 (현재는 pro 폴백이 보험).
