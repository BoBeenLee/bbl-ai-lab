---
issue: 16
issue_url: https://github.com/BoBeenLee/bbl-ai-lab/issues/16
title: 채용 시장 데이터 수집/분석 파이프라인 (국내 + 국외)
status: draft
owner: BoBeenLee
created: 2026-05-24
updated: 2026-05-24
revisions:
  - { date: 2026-05-24, pr: 0, note: "initial draft — PoC 4개 플랫폼 (원티드/점핏/HN/RemoteOK) + 주간 리포트" }
---

# 채용 시장 데이터 수집/분석 파이프라인 (국내 + 국외)

## Context

이슈 #16 은 채용 시장의 요구 역량/트렌드를 수동 추적의 한계 없이 AI 로 정기 수집·구조화하여 시계열로 보고 싶다는 요구다. 이 plan 은 그 첫 PoC 의 실행 계획. 대시보드/UI 는 후속.

사용자 결정 (확정):
- 타겟 직군: **IT 전 직군 (개발 + 기획 + 디자인)**
- 출력: **raw JD 적재 + 주간 리포트** 둘 다
- 크롤링 방식 (공식 API only vs 정중 크롤링 vs 외부 벤더): 이번 plan 에서는 결정 보류. PoC 4 개 플랫폼이 모두 robots/API 친화적이라 보류 상태로 PoC 진행 가능.

## Approach

기존 [`idea-elaborate` flow](../idea-elaborate.md) 패턴 위에 같은 prefix 규칙으로 두 flow 신설:

- **`recruit-collect`** — 매일 03:00 KST cron + `repository_dispatch[recruit-collect]` + `workflow_dispatch`. 플랫폼별 fetcher 실행 → `data/recruit/<YYYY-MM-DD>/<region>/<platform>.jsonl` 로 git commit. fetcher 단계에서는 LLM 호출 없음.
- **`recruit-analyze`** — 매주 월 09:00 KST cron + `repository_dispatch[recruit-analyze]` + `workflow_dispatch(since/until)`. 최근 7 일치 JSONL 을 읽어 Gemini 로 per-JD 구조화 추출 (저렴한 `gemini-2.5-flash`), Python 으로 직군 × 권역 × WoW 집계, Gemini (`gemini-3-pro-preview`) 로 주간 리포트 마크다운 생성 후 `gh issue create --label recruit-report`.

PoC 시작 플랫폼 (★ 4 개, KR/GLOBAL 모두 robots/약관 친화적):

| 권역 | 플랫폼 | 접근 방식 |
|------|--------|-----------|
| KR | 원티드 | 페이지 내 JSON-LD `JobPosting` |
| KR | 점핏 | 페이지 JSON-LD, 개발자 특화 |
| GLOBAL | HackerNews "Who's Hiring" | HN Firebase API |
| GLOBAL | RemoteOK | `https://remoteok.com/api` 공개 JSON |

사람인/잡코리아/LinkedIn 확장은 [Alternatives considered](#alternatives-considered) 참고. 별도 결정 필요.

Worker (`worker/src/index.ts`) 의 `FLOWS` 에 `recruit` 추가하고 sub-command 라우팅 (`/recruit collect`/`/recruit report`) 으로 확장. `FlowDef` + `routeCommand` 만 살짝 변경.

Per-JD 추출 스키마:
```jsonc
{
  "role_category": "engineer|pm|designer|data|ml|devops|qa|security|other",
  "seniority": "intern|junior|mid|senior|lead|head",
  "skills_required": ["..."],
  "skills_preferred": ["..."],
  "domain": "fintech|commerce|saas|gaming|...",
  "work_mode": "onsite|hybrid|remote|unspecified",
  "compensation_hint": "...|null"
}
```

스킬 정규화 사전 (`react/reactjs/react.js → react` 등) 은 `skills/recruit-market-analysis.SKILL.md` 에 명시. 사전에 없는 토큰은 `unknown_skills` 로 분리 누적 → 주기적 사람 보강.

## Critical files

| 경로 | 역할 | 신규/수정 |
|------|------|-----------|
| `.github/workflows/recruit-collect.yml` | cron + dispatch, fetcher 실행 → commit | 신규 |
| `.github/workflows/recruit-analyze.yml` | cron + dispatch, Gemini 분석 → Issue | 신규 |
| `scripts/recruit-collect.sh` | fetcher 호출·집계·commit | 신규 |
| `scripts/recruit-analyze.sh` | 추출/집계/리포트 호출 | 신규 |
| `scripts/recruit/fetchers/{wanted,jumpit,hn_hiring,remoteok}.py` | 플랫폼별 fetcher | 신규 |
| `scripts/recruit/aggregate.py` | 집계 (skill top N, WoW diff) | 신규 |
| `scripts/prompts/recruit-extract.md` | per-JD 구조화 프롬프트 + JSON 스키마 | 신규 |
| `scripts/prompts/recruit-analyze.md` | 주간 리포트 프롬프트 | 신규 |
| `skills/recruit-market-analysis.SKILL.md` | 도메인 컨텍스트 + 스킬 정규화 사전 | 신규 |
| [worker/src/index.ts](../../worker/src/index.ts) | FLOWS 에 recruit 추가, sub-command 라우팅 | 수정 |
| `docs/recruit-collect.md`, `docs/recruit-analyze.md` | flow 문서 | 신규 |
| [README.md](../../README.md) | 등록된 flow 표에 2 줄 추가 | 수정 |

기존 패턴 재사용:
- [scripts/idea-elaborate.sh](../../scripts/idea-elaborate.sh) 의 Gemini 호출 + JSON 추출 + 1 회 재시도 패턴
- [.github/workflows/idea-elaborate.yml](../../.github/workflows/idea-elaborate.yml) 의 Gemini OAuth 복원 step
- [scripts/fetch-url-content.py](../../scripts/fetch-url-content.py) 의 trafilatura HTML→텍스트 변환

## Verification

| 단계 | 명령 / 액션 | 기대 |
|------|------|------|
| fetcher 단독 (로컬) | `python scripts/recruit/fetchers/remoteok.py --out /tmp/out.jsonl --max-pages 1` | `/tmp/out.jsonl` 에 ≥1 건 JSONL, 스키마 필드 모두 채움 |
| collect workflow (수동) | `gh workflow run recruit-collect.yml -f platforms="remoteok,hn-hiring"` | `data/recruit/<today>/GLOBAL/*.jsonl` 커밋 |
| analyze workflow (수동, 더미 7 일치) | `gh workflow run recruit-analyze.yml` | `recruit-report` 라벨 Issue + 직군별 표/skill top N |
| 텔레그램 라우팅 | `/recruit collect`, `/recruit report`, `/recruit`, `/recruit foo` | 각각 ack / ack / usageHint / 도움말 |
| cron | 다음 03:00 KST 자동 commit | git log 확인 |
| 스키마 위반 회복 | 일부 JD JSON 위반 | 해당 건 스킵, 나머지로 리포트, 본문에 "추출 실패 N건" |
| 비용 가드 | 일일 호출 수 | (수집 0) + (추출 N) ≤ 200 |

## Open questions

- [ ] 사람인/잡코리아/LinkedIn 확장 시 수집 방식 결정 (옵션 A: 공식 API only / B: 정중 크롤링 + JSON-LD / C: 외부 벤더)
- [ ] 일 JD 1,000 건 초과 시 sampling 전략 (직군별 max N? batched prompt? 추출 주 1 회?)
- [ ] `data/recruit/` 가 100MB 임계 도달 시 외부 스토리지 (Cloudflare R2 등) 이전 시점

## Alternatives considered

- **메이저 KR 플랫폼 (사람인/잡코리아) 우선**: robots 엄격 + 약관 위반 리스크 + UA 차단 강함. PoC 단계에서 의사결정 비용 큼 → 후순위로 분리.
- **LinkedIn / Indeed**: 공식 API 종료/제한적, 크롤링 차단 강함 → 비채택.
- **외부 데이터 벤더 (Apify/Bright Data)**: 운영 부담 ↓ but 월 비용, 데이터 신뢰성 별도 검증 필요 → PoC 이후 옵션.
- **추출까지 `gemini-3-pro-preview`**: 품질은 더 좋지만 일 JD 100 건 = 일 100 호출 시 비용/한도 압박. flash 로 충분 판단 → flash 채택.

## Revisions

- 2026-05-24 (#TBD): initial draft — PoC 4개 플랫폼 (원티드/점핏/HN/RemoteOK) + 주간 리포트
