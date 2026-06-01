# `recruit-collect` flow

채용 시장 JD 를 플랫폼별로 정기 수집해 정규화 JSONL 로 레포에 적재한다. 이 단계는 **LLM 을 호출하지 않는다** (raw 적재 전용). 구조화 추출/집계/주간 리포트는 후속 `recruit-analyze` flow 의 책임.

이슈 #16 / 플랜 [`docs/plans/16-recruit-market-data-collection.md`](plans/16-recruit-market-data-collection.md) 의 PoC 수집부.

## 트리거

| 입력 형태 | 예시 | 비고 |
|-----------|------|------|
| cron | 매일 18:00 UTC (= 03:00 KST) | 4개 플랫폼 전체 수집 |
| `workflow_dispatch` | `gh workflow run recruit-collect.yml -f platforms="remoteok,hn-hiring"` | 수동/E2E |
| `repository_dispatch` | event_type **`recruit-collect`** | 텔레그램 `/recruit collect` (worker 라우팅, 후속 라운드) |

## 대상 플랫폼

| slug | 권역 | 접근 방식 | 스킬 필드 |
|------|------|-----------|-----------|
| `remoteok` | GLOBAL | 공개 JSON `https://remoteok.com/api` (출처 링크백 ToS, Crawl-delay 1) | `tags` → `skills_raw` |
| `hn-hiring` | GLOBAL | HN Firebase API: whoishiring → 최신 "Who is hiring" → kids 댓글 | 자유텍스트 (analyze 추출) |
| `wanted` | KR | 상세 페이지 `application/ld+json` JobPosting | 자유텍스트 (analyze 추출) |
| `jumpit` | KR | saramin 내부 API (`jumpit-api.saramin.co.kr`) — **JSON-LD 아님(CSR)** | `techStacks` → `skills_raw` |
| `jobkorea` | KR | `/recruit/joblist` HTML → 상세 `GI_Read` JSON-LD JobPosting (원티드 패턴) | 자유텍스트 (요약, analyze 추출) |
| `greenhouse` | GLOBAL | 공개 ATS API `boards-api.greenhouse.io/v1/boards/<co>/jobs?content=true` | 자유텍스트 (analyze 추출) |
| `ashby` | GLOBAL | 공개 ATS API `api.ashbyhq.com/posting-api/job-board/<co>` | 자유텍스트 (analyze 추출) |
| `lever` | GLOBAL | 공개 ATS API `api.lever.co/v0/postings/<co>?mode=json` | 자유텍스트 (analyze 추출) |

> **ATS(greenhouse/ashby/lever):** 무인증 공개 API. "회사별 조회" 모델이라 회사 슬러그 목록을 `scripts/recruit/ats_companies.json` 에서 큐레이션/확장한다. 없는 슬러그/빈 응답은 graceful skip. 한 회사가 데이터를 독식하지 않도록 fetcher 에 `--per-company` 캡(기본 40). 부서(department) 가 다양해 기획/디자인 직군 커버리지도 보완한다.
>
> **원티드 주의:** CloudFront 뒤에 있어 데이터센터 IP(GitHub Actions)가 WAF 에 차단될 수 있다. fetcher 는 403/빈응답 시 해당 플랫폼만 graceful skip(exit 0)하고 나머지로 진행한다 (jobkorea 도 동일 graceful skip).
>
> **잡코리아 주의:** 본문은 CSR 렌더라 JSON-LD `description` 은 짧은 SEO 요약이다(스킬 신호 약함, 메타데이터/직군 위주). AI/LLM 크롤러 UA 는 robots 차단 대상이나 fetcher 는 일반 UA + LLM 미사용.

## 적재 경로

```
data/recruit/<YYYY-MM-DD(KST)>/<region>/<platform>.jsonl
                                 │         └─ remoteok | hn-hiring | greenhouse | ashby | lever (GLOBAL)
                                 │            wanted | jumpit | jobkorea (KR)
                                 └─ GLOBAL | KR
```

레코드 정규화 스키마 (`scripts/recruit/normalize.py` `make_record`):

```jsonc
{
  "platform": "remoteok",            // 플랫폼 slug
  "region": "GLOBAL",                // GLOBAL | KR
  "external_id": "...",              // 플랫폼 내 고유 id
  "title": "...",
  "company": "...|null",
  "location": "...|null",
  "description": "...",              // 평문, 최대 4000자
  "skills_raw": ["react", "..."],    // 구조화 스킬(있으면), 없으면 []
  "url": "https://...",              // 원본 링크(출처 링크백)
  "posted_at": "YYYY-MM-DD|null",
  "employment_type": "...|null",
  "salary": "...|null",
  "collected_at": "ISO8601"
}
```

## 구성 파일

| 경로 | 역할 |
|------|------|
| `.github/workflows/recruit-collect.yml` | cron + dispatch, `permissions: contents: write`, collector 실행 |
| `scripts/recruit-collect.sh` | 플랫폼별 fetcher 실행 → JSONL 적재 → git commit/push |
| `scripts/recruit/fetchers/{remoteok,hn_hiring,wanted,jumpit,jobkorea,greenhouse,ashby,lever}.py` | 플랫폼별 fetcher (stdlib only) |
| `scripts/recruit/ats.py`, `ats_companies.json` | ATS 공통 모듈 + 회사 슬러그 시드 |
| `scripts/recruit/normalize.py` | http/정규화/JSONL 공통 유틸 |

## 로컬 실행

```bash
# 단일 fetcher
python scripts/recruit/fetchers/remoteok.py --out /tmp/out.jsonl --max-pages 1
python scripts/recruit/fetchers/jumpit.py   --out /tmp/out.jsonl --max 20

# 전체 수집 (커밋 없이 dry-run)
NO_COMMIT=1 MAX=20 bash scripts/recruit-collect.sh
```

환경변수: `PLATFORMS`(콤마 구분, 기본 4개 전체), `MAX`(플랫폼당 상한, 기본 200), `COLLECT_DATE`(기본 KST 오늘), `NO_COMMIT=1`(commit 생략).

## 검증 요약 (2026-06-01 실측)

| 플랫폼 | 결과 | 필드 커버리지 |
|--------|------|---------------|
| remoteok | OK (1회 ~95건) | title/company/desc/url/posted 100%, location 94%, skills 87% |
| hn-hiring | OK (최신 스레드 ~378댓글) | title/desc/url/posted 100% (company/skills 는 analyze) |
| wanted | OK (JSON-LD) | title/company/location/desc/url/posted 100% |
| jumpit | OK (saramin API) | 전 필드 100% (skills_raw 포함) |
| jobkorea | OK (joblist 63건/페이지 → JSON-LD) | title/company/location/desc/url/posted 100% (desc 는 요약) |
| greenhouse | OK (stripe/airbnb 등) | title/company/location/desc/url/posted 100% |
| ashby | OK (openai/notion 등) | 전 필드 100% (employment_type 포함) |
| lever | OK (mistral) | title/company/location/desc/url/posted 100% |

## 후속 (이번 라운드 미포함)

- `recruit-analyze` flow (Gemini per-JD 구조화 추출 + 직군×권역 WoW 집계 + 주간 리포트 Issue)
- worker 텔레그램 sub-command 라우팅 (`/recruit collect`, `/recruit report`)
