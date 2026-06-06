# bbl-ai-lab Context

## Language

**Automation flow hub**:
이 저장소의 주된 제품 형태. Telegram command를 Cloudflare Worker가 받아 GitHub repository_dispatch로 넘기고, GitHub Actions가 script/prompt/skill context를 실행해 Issue, 보고서, 문서 같은 산출물을 만드는 여러 automation flow의 집합이다.
_Avoid_: 단순 Worker, 봇 하나

**Automation flow**:
하나의 사용자 의도 또는 반복 작업을 처리하는 end-to-end 경로. command 또는 subcommand, repository_dispatch event type, workflow, script, prompt, docs가 함께 움직인다. 예: `idea-elaborate`.
_Avoid_: workflow만, script만

**Flow registry**:
`worker/src/flows.ts`에 있는 automation flow manifest와 routing helper. Telegram command/subcommand, event type, usage/ack text, adapter file path를 한 interface에 모아 drift를 검증 가능하게 만든다.
_Avoid_: FLOWS 테이블, 라우팅 배열

**Flow adapter files**:
Flow registry entry가 가리키는 concrete files. 현재는 GitHub Actions workflow, runtime script, Gemini prompt, flow docs를 뜻한다.
_Avoid_: 관련 파일들

**Legacy event type**:
Flow registry 도입 전부터 운영되어 `<flow>-<action>` naming rule을 따르지 않는 repository_dispatch event type. 현재 허용된 값은 `idea-submitted`뿐이다.
_Avoid_: 예외 이벤트

**Subcommand flow**:
하나의 top-level Telegram command 아래 여러 action을 두는 automation flow. 형식은 `/command subcommand body`이며, 각 subcommand가 별도 event type과 flow adapter files를 가진다. 예: 예정된 `/recruit collect`.
_Avoid_: nested command, 하위 명령

**Control MacBook**:
Codex Desktop session이 실행되는 작업자 측 MacBook. 대상 기기에 SSH 또는 화면 공유로 접속해 구축 작업을 수행하는 진입점이다.
_Avoid_: 맥북 클로드, 로컬 맥북

**Hermes MacBook**:
Hermes agent를 설치·운영할 대상 MacBook. 이 plan에서는 `BoBeenui-MacBookPro.local` 역할의 회사 지급 MacBook을 가리킨다.
_Avoid_: 다른 맥북, 대상 기기

**Hermes agent**:
Hermes MacBook에서 설치·검증할 NousResearch/hermes-agent 기반 자동화 에이전트. 공식 per-user layout (`~/.hermes/hermes-agent`, `~/.hermes`, `~/.local/bin/hermes`)을 따른다.

**Approved remote access path**:
회사 장비 보안 정책을 우회하지 않는 원격 접속 경로. 이 plan에서는 같은 신뢰 네트워크 안의 SSH 키 인증을 우선하며, 개인 Tailscale 같은 overlay network는 회사 승인 전에는 사용하지 않는다.
