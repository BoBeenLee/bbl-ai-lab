# bbl-ai-lab Context

## Language

**Control MacBook**:
Codex Desktop session이 실행되는 작업자 측 MacBook. 대상 기기에 SSH 또는 화면 공유로 접속해 구축 작업을 수행하는 진입점이다.
_Avoid_: 맥북 클로드, 로컬 맥북

**Hermes MacBook**:
Hermes agent를 설치·운영할 대상 MacBook. 이 plan에서는 `BoBeenui-MacBookPro.local` 역할의 회사 지급 MacBook을 가리킨다.
_Avoid_: 다른 맥북, 대상 기기

**Hermes agent**:
Hermes MacBook에서 백그라운드로 실행될 자동화 에이전트. 구체 실행 바이너리, 권한, health check는 구현 단계에서 확정한다.

**Approved remote access path**:
회사 장비 보안 정책을 우회하지 않는 원격 접속 경로. 이 plan에서는 같은 신뢰 네트워크 안의 SSH 키 인증을 우선하며, 개인 Tailscale 같은 overlay network는 회사 승인 전에는 사용하지 않는다.
