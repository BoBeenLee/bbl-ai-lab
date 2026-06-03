---
name: recruit-market-analysis
description: 채용 시장 JD(job description) 를 직군/역량/도메인으로 구조화하고 시계열 트렌드를 읽는 도메인 컨텍스트. recruit-analyze flow 가 per-JD 추출·집계·주간 리포트 생성 시 참조한다. 스킬 토큰 정규화 사전(canonical→aliases)을 단일 source-of-truth 로 보유.
---

# Recruit Market Analysis Skill

채용 공고(JD)에서 "어떤 직군이 어떤 역량을 요구하는가" 를 일관된 분류 체계로 뽑아, 주/권역 단위 트렌드로 집계하기 위한 도메인 지식. IT 전 직군(개발+기획+디자인)이 대상.

## 데이터 출처별 특성

| 플랫폼 | 권역 | 특성 | 스킬 신호 |
|--------|------|------|-----------|
| `wanted` | KR | 전 직군, JSON-LD 정제 텍스트 | description 에서 추출 |
| `jumpit` | KR | 개발 직군 특화 | `skills_raw` (techStacks) 신뢰도 높음 |
| `remoteok` | GLOBAL | 원격/개발 위주 | `skills_raw` (tags) 존재 |
| `hn-hiring` | GLOBAL | 자유 형식, 스타트업 다수 | description 전체에서 추출 |

`hn-hiring`/`wanted` 는 구조화 스킬이 없어 description 본문에서 역량을 읽어야 한다. `jumpit`/`remoteok` 은 `skills_raw` 가 1차 신호지만, description 의 추가 역량도 함께 본다.

## 직군 분류 (role_category)

- `engineer` — 일반 소프트웨어 개발(프론트/백/풀스택/모바일). 세부 영역이 아래로 분리되지 않을 때의 기본값.
- `data` — 데이터 엔지니어/분석가/사이언티스트(파이프라인·분석·BI).
- `ml` — ML/AI 엔지니어, 리서처(모델 학습·서빙·LLM).
- `devops` — 인프라/SRE/플랫폼/클라우드 운영.
- `qa` — 품질/테스트 자동화.
- `security` — 보안/시큐리티 엔지니어.
- `pm` — 프로덕트/프로젝트 기획, PO.
- `designer` — UX/UI/프로덕트 디자인.
- `other` — 위에 안 맞는 직군(영업/마케팅/HR 등).

경계 규칙: "AI/ML 모델" 중심이면 `ml`, "데이터 파이프라인/분석" 중심이면 `data`, 둘 다 모호하면 본문의 핵심 동사로 판정. 기획/디자인이 개발과 섞인 공고는 *주(主) 직무* 기준.

## 연차 (seniority)

`intern` < `junior`(0~2y) < `mid`(3~6y) < `senior`(7y+) < `lead`(팀 리드/테크리드) < `head`(조직장). 명시 없으면 본문 신호(요구 연차/직책)로 추정하되 근거 없으면 `mid` 로 추정하지 말고 가장 보수적으로 본문에 부합하는 값.

## 근무 형태 (work_mode)

`onsite` / `hybrid` / `remote` / `unspecified`. 원격 가능 여부가 본문에 없으면 `unspecified`(추측 금지). RemoteOK 는 기본 `remote` 성향이나 본문이 hybrid/onsite 를 명시하면 그것을 우선.

## 도메인 (domain)

`fintech, commerce, saas, gaming, healthcare, edtech, mobility, media, ai, b2b, b2c, ...` 등 자유 문자열(소문자). 회사 소개/제품 설명에서 추론. 불명확하면 비워둔다(빈 문자열).

## 스킬 정규화 사전 (skill normalization)

집계 시 동의어/표기 변형을 canonical 토큰으로 합친다. 아래 **단일 JSON 코드펜스**가 source-of-truth — `scripts/recruit/aggregate.py` 가 이 펜스를 파싱해 `alias(소문자) → canonical` 로 역전한다. (이 파일의 코드펜스는 정확히 1개만 유지할 것 — 파서가 1개를 가정한다. 사람이 직접 추가/보강한다.)

키 = canonical 토큰, 값 = 해당 canonical 로 합칠 alias 목록(canonical 자기 자신은 자동 포함, 매칭은 소문자 기준). 사전에 없는 토큰은 `unknown_skills` 로 누적되어 리포트/스냅샷에 남고, 주기적으로 사람이 이 사전에 반영한다.

```json
{
  "javascript": ["js", "ecmascript", "vanilla js"],
  "typescript": ["ts"],
  "react": ["reactjs", "react.js"],
  "next.js": ["nextjs", "next js"],
  "vue": ["vuejs", "vue.js"],
  "angular": ["angularjs"],
  "svelte": ["sveltekit"],
  "node.js": ["node", "nodejs"],
  "python": ["py"],
  "java": [],
  "kotlin": [],
  "go": ["golang"],
  "rust": [],
  "c++": ["cpp", "cplusplus"],
  "c#": ["csharp", "c sharp", ".net", "dotnet"],
  "php": [],
  "ruby": ["ruby on rails", "rails"],
  "scala": [],
  "swift": [],
  "spring": ["spring boot", "springboot"],
  "django": [],
  "fastapi": [],
  "flask": [],
  "express": ["express.js", "expressjs"],
  "nestjs": ["nest.js"],
  "graphql": [],
  "rest": ["rest api", "restful"],
  "postgresql": ["postgres", "psql"],
  "mysql": ["maria", "mariadb"],
  "mongodb": ["mongo"],
  "redis": [],
  "elasticsearch": ["elastic", "es"],
  "kafka": ["apache kafka"],
  "aws": ["amazon web services"],
  "gcp": ["google cloud", "google cloud platform"],
  "azure": ["microsoft azure"],
  "docker": [],
  "kubernetes": ["k8s"],
  "terraform": [],
  "airflow": ["apache airflow"],
  "spark": ["apache spark", "pyspark"],
  "pytorch": ["torch"],
  "tensorflow": ["tf"],
  "pandas": [],
  "sql": [],
  "git": [],
  "figma": [],
  "linux": []
}
```

## 리포트 관점 (집계 해석)

- skill top-N 은 *중복 제거된 JD 기준 빈도*(한 JD 가 같은 스킬을 여러 번 언급해도 1). 권역(KR/GLOBAL)별로 분리해 비교.
- WoW(week-over-week) 는 전주 스냅샷 대비 *순위 이동*과 *신규/이탈 스킬*이 핵심. 절대수보다 변화 방향을 본다.
- `unknown_skills` 가 누적되면 사전 갱신 신호 — 리포트에 상위 후보를 노출한다.
