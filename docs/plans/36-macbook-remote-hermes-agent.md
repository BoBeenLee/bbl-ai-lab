---
issue: 36
issue_url: https://github.com/BoBeenLee/bbl-ai-lab/issues/36
title: MacBook SSH 원격 접속 기반 Hermes agent 구축
status: active
owner: BoBeenLee
created: 2026-06-03
updated: 2026-06-03
revisions:
  - { date: 2026-06-03, pr: 0, note: "initial draft — SSH 접속 경로 확정 + Hermes agent 구축 성공 기준 정의" }
  - { date: 2026-06-03, pr: 0, note: "active — NousResearch hermes-agent 공식 설치 경로 기반 doctor-first 구현" }
---

# MacBook SSH 원격 접속 기반 Hermes agent 구축

## Context

이슈 #36은 "맥북 클로드에 원격으로 접속하여 다른 맥북에 Hermes agent를 구축한다"는 메모에서 출발했다. 원문은 접속 대상, 보안 경계, agent 성공 기준이 비어 있어 `needs-clarification` 상태였지만, 2026-06-03 세션에서 실제 접속 경로를 검증하며 실행 가능한 범위를 좁혔다.

현재 확정된 실행 모델은 Control MacBook에서 Codex Desktop을 사용하고, Hermes MacBook(`BoBeenui-MacBookPro.local`)에 SSH 키 인증으로 접속해 NousResearch/hermes-agent 설치·검증 작업을 수행하는 방식이다. Hermes MacBook은 회사 지급 장비이므로 개인 Tailscale 같은 별도 overlay network는 승인 전 사용하지 않고, 같은 신뢰 네트워크에서 열린 SSH 경로를 우선한다.

실측 결과:
- Hermes MacBook 사용자: `bobeenlee`
- Hermes MacBook 호스트명: `BoBeenui-MacBookPro.local`
- 현재 접속 IP: `192.168.0.8`
- SSH 접속 확인: `ssh -i ~/.ssh/id_ed25519_bobeenlee_nopass -o IdentitiesOnly=yes bobeenlee@192.168.0.8`
- 원격 확인 결과: `whoami=bobeenlee`, `hostname=BoBeenui-MacBookPro.local`, `pwd=/Users/bobeenlee`, `sw_vers -productVersion=26.2`
- 디버그 결과: 최초 등록한 passphrase 있는 key는 서버가 public key를 인정했지만, Codex 비대화형 SSH 세션에서 private key passphrase를 풀 수 없어 인증이 최종 실패했다. 따라서 Codex 자동화 전용 no-pass key를 별도로 발급해 Hermes MacBook의 `authorized_keys`에 추가했다.
- 구현 결과: `scripts/hermes/install.sh`로 Hermes agent를 공식 path에 설치했고, `scripts/hermes/doctor.sh` 기준 `~/.hermes/hermes-agent`, `~/.local/bin/hermes`, managed `uv`, managed Node/npm이 확인된다. 모델 기본값은 OpenRouter `openrouter/free`로 설정했고, `OPENROUTER_API_KEY` 구성 후 smoke test가 통과했다. user-level launchd gateway는 loaded 상태다.

## Approach

1. **접속 경로를 SSH 키 인증으로 고정한다.** Control MacBook에는 Codex 전용 passphrase 없는 ED25519 key를 두고, Hermes MacBook의 `~/.ssh/authorized_keys`에는 해당 public key를 등록한다. Codex 자동화는 항상 `-i ~/.ssh/id_ed25519_bobeenlee_nopass -o IdentitiesOnly=yes`를 붙여 의도한 키만 사용한다. 기존 passphrase 있는 key는 사람이 직접 SSH할 때는 쓸 수 있지만 Codex의 `BatchMode=yes` 비대화형 실행에는 맞지 않는다.

   운영 가드:
   - private key 파일은 repo에 커밋하지 않고 Control MacBook의 `~/.ssh/`에만 둔다.
   - 접근 회수는 Hermes MacBook의 `~/.ssh/authorized_keys`에서 `codex-to-bobeenlee-nopass` 줄을 제거하는 방식으로 한다.
   - 구현 PR/문서에는 public key fingerprint까지만 남기고 private key, passphrase, secret은 기록하지 않는다.

2. **회사 장비 보안 경계를 plan의 가드레일로 둔다.** 개인 Tailscale, 개인 원격 데스크톱, 외부 tunnel은 기본 비채택이다. 회사 IT/보안팀이 승인한 tailnet/VPN/bastion이 있으면 별도 revision에서 대체 경로로 문서화한다.

3. **Hermes agent 구축은 공식 per-user layout을 따른다.** NousResearch/hermes-agent 공식 installer의 기본 경로를 사용해 code는 `~/.hermes/hermes-agent`, data/config/session/log는 `~/.hermes`, command는 `~/.local/bin/hermes`에 둔다. 설치 스크립트는 공식 installer를 원격에서 실행하고, setup wizard와 secret 입력은 자동화하지 않는다.

4. **운영화는 CLI-first launchd gateway까지 활성화한다.** 단기 검증은 `hermes doctor`와 foreground 명령으로 수행한다. 상시 실행은 Hermes 공식 `hermes gateway install/start/status` 명령으로 user-level `launchd` agent를 등록한다. Telegram/Discord 같은 messaging provider setup은 별도 후속 단계로 둔다.

5. **완료 기준은 "설치됨"이 아니라 "원격에서 재현 가능하게 진단됨"으로 둔다.** 이번 범위에서는 SSH 접속, 공식 설치 경로 확인, `hermes doctor`, OpenRouter/free model config, OpenRouter smoke test, gateway status/log 확인까지 통과해야 한다. OpenRouter API key는 secret이므로 Hermes MacBook의 `~/.hermes/.env`에만 저장한다.

## Critical files

| 경로 | 역할 | 신규/수정 |
|------|------|-----------|
| `CONTEXT.md` | Control MacBook, Hermes MacBook, Hermes agent, approved remote access path 용어 정의 | 신규 |
| `docs/plans/36-macbook-remote-hermes-agent.md` | 이슈 #36 실행 계획의 단일 진실원 | 신규 |
| `scripts/hermes/install.sh` | Hermes agent 설치/업데이트 스크립트 후보 | 신규 |
| `scripts/hermes/doctor.sh` | SSH 접속, 의존성, agent 실행 상태, 로그 상태 진단 후보 | 신규 |
| `docs/hermes-agent.md` | 수동 운영 절차, SSH 접속 명령, health check, rollback 정리 후보 | 신규 |
| `~/Library/LaunchAgents/ai.hermes.gateway.plist` | Hermes 공식 gateway launchd 설정. CLI-first gateway 운영을 위해 user-level로 등록한다 | 신규 후보 |

## Verification

| 단계 | 액션 | 기대 |
|------|------|------|
| SSH 연결 | `ssh -i ~/.ssh/id_ed25519_bobeenlee_nopass -o IdentitiesOnly=yes bobeenlee@192.168.0.8 'whoami && hostname && pwd'` | `bobeenlee`, `BoBeenui-MacBookPro.local`, `/Users/bobeenlee` 출력 |
| 권한/키 상태 | Hermes MacBook에서 `ssh-keygen -lf ~/.ssh/authorized_keys` | Codex 전용 public key fingerprint가 등록되어 있음 |
| no-pass key 확인 | Control MacBook에서 `ssh-keygen -y -f ~/.ssh/id_ed25519_bobeenlee_nopass >/dev/null` | passphrase prompt 없이 성공 |
| 네트워크 안정성 | Control MacBook에서 `nc -vz 192.168.0.8 22` | SSH port reachable |
| 설치 dry run | `scripts/hermes/install.sh --dry-run` | 공식 installer 실행 예정 항목 출력, secret/private key 미출력 |
| 설치 실행 | `scripts/hermes/install.sh` | `~/.hermes/hermes-agent`, `~/.local/bin/hermes` 생성 후 `hermes doctor` 실행 |
| agent foreground | Hermes MacBook에서 `~/.local/bin/hermes doctor` 실행 | command exits 0 또는 setup 필요 상태를 명확히 출력 |
| 로그 확인 | `scripts/hermes/doctor.sh` 또는 문서화된 log command 실행 | gateway log 존재 여부와 최근 상태 확인 |
| OpenRouter/free 설정 | `hermes config show` | `model.provider=openrouter`, `model.default=openrouter/free` 확인 |
| OpenRouter smoke test | `hermes --provider openrouter --model openrouter/free -z ...` | `OK` 응답 |
| launchd 등록 | `hermes gateway install/start/status` | `ai.hermes.gateway` service loaded |

실행 검증 결과:
- `scripts/hermes/install.sh --dry-run`: 통과
- `scripts/hermes/install.sh`: 공식 installer 완료, `~/.local/bin/hermes doctor` 실행
- `scripts/hermes/doctor.sh`: SSH, key fingerprint, official paths, managed runtime paths, `hermes doctor`, `hermes gateway status` 확인
- OpenRouter/free model config: `model.provider=openrouter`, `model.default=openrouter/free` 확인
- OpenRouter smoke test: `OK` 응답 확인
- gateway 상태: user-level launchd `ai.hermes.gateway` loaded
- 남은 blocker: 구현 PR merge 및 최종 shipped revision

## Open questions

- [x] Hermes agent의 실체: NousResearch/hermes-agent 공식 installer 기반 CLI/gateway agent.
- [x] Hermes agent의 health check: doctor-first 범위에서는 `hermes doctor`와 `hermes gateway status`를 성공 기준으로 본다.
- [x] 회사 장비 정책상 user-level launchd 등록과 Codex 전용 SSH key 사용이 허용되는가?
  - 현 실행에서는 user-level launchd (`ai.hermes.gateway`)와 Codex 전용 SSH key를 사용했다. system daemon, sudo, 개인 overlay network는 사용하지 않았다.
- [ ] IP `192.168.0.8`이 DHCP로 바뀔 때 사용할 안정 식별자는 `BoBeenui-MacBookPro.local`로 충분한가, 아니면 DHCP reservation/사내 DNS가 필요한가?
- [ ] agent 로그/작업 산출물에 회사 정보 또는 개인 정보가 포함될 수 있는가? 포함된다면 저장 위치와 보존 기간은?
- [x] 장애 시 rollback은 단순 process stop인지, plist unload + 파일 삭제 + key 회수까지 포함하는지?
  - 운영 rollback은 `hermes gateway stop`, launchd plist unload, 필요 시 `~/.hermes` 제거, 마지막으로 `authorized_keys`에서 `codex-to-bobeenlee-nopass` 제거 순서로 한다.

## Domain language updates

| 용어 | 정의 (1~2문장) | 액션 | 비고 |
|------|----------------|------|------|
| Control MacBook | Codex Desktop session이 실행되는 작업자 측 MacBook. 대상 기기에 SSH 또는 화면 공유로 접속해 구축 작업을 수행하는 진입점이다. | add | 이슈 본문의 "맥북 클로드"를 명확한 역할명으로 정리 |
| Hermes MacBook | Hermes agent를 설치·운영할 대상 MacBook. 이 plan에서는 `BoBeenui-MacBookPro.local` 역할의 회사 지급 MacBook을 가리킨다. | add | 이슈 본문의 "다른 맥북"을 명확한 역할명으로 정리 |
| Hermes agent | Hermes MacBook에서 설치·검증할 NousResearch/hermes-agent 기반 자동화 에이전트. 공식 per-user layout (`~/.hermes/hermes-agent`, `~/.hermes`, `~/.local/bin/hermes`)을 따른다. | update | 실체 확정 |
| Approved remote access path | 회사 장비 보안 정책을 우회하지 않는 원격 접속 경로. 같은 신뢰 네트워크 안의 SSH 키 인증을 우선하며 개인 overlay network는 승인 전 사용하지 않는다. | add | Tailscale 검토 중 보안 가드레일로 결정 |

## ADR proposals

ADR 만들지 않음 — 현재 결정은 운영 plan 수준의 가드레일이며 repo 전체 아키텍처를 hard-to-reverse하게 바꾸는 결정은 아니다. 회사 승인 원격 접속 방식이 별도 VPN/bastion으로 확정되거나 Hermes agent runtime을 repo 표준으로 고정하는 시점에 ADR을 재검토한다.

## Alternatives considered

- **개인 Tailscale tailnet**: 같은 Wi-Fi에서 client isolation이 있으면 빠르게 우회할 수 있지만, 회사 지급 MacBook을 개인 overlay network에 붙이는 것은 보안 정책 위반 또는 감사 리스크가 크다. 회사 관리 tailnet 또는 명시 승인 전에는 비채택.
- **macOS Screen Sharing/VNC 중심 운영**: GUI 조작에는 편하지만 반복 가능한 설치/검증 기록이 남기 어렵고 Codex 자동화와도 궁합이 낮다. 초기 설정 보조 수단으로만 둔다.
- **비밀번호 SSH 로그인**: 한 번 접속은 가능하지만 Codex 비대화형 자동화에 부적합하고 비밀번호 입력/보관 리스크가 있다. 키 인증을 채택.
- **passphrase 있는 SSH key 재사용**: 대상 서버는 키를 인정했지만 Codex 비대화형 세션에서 private key passphrase를 풀 수 없어 실패했다. 전용 no-pass key로 분리하고 해당 key의 scope를 Hermes MacBook 접속으로 제한한다.
- **root/system-level daemon**: 부팅 직후 상시 실행에는 강하지만 회사 장비의 보안 변경면이 커진다. user-level launchd로 충분한지 먼저 검증한다.
- **별도 관리 루트 (`~/Documents/mygit/hermes`)**: 관리 편의성은 좋지만 공식 installer의 기본 layout과 달라 향후 업데이트/문서 추적 비용이 생긴다. 공식 path를 우선한다.

## Revisions

- 2026-06-03 (#TBD): initial draft — SSH 접속 경로 확정 + Hermes agent 구축 성공 기준 정의
- 2026-06-03 (#TBD): active — NousResearch hermes-agent 공식 설치 경로 기반 doctor-first 구현
- 2026-06-03 (#TBD): active — OpenRouter/free 기본 모델 설정 + user-level launchd gateway 활성화
