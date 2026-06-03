---
issue: 36
issue_url: https://github.com/BoBeenLee/bbl-ai-lab/issues/36
title: MacBook SSH 원격 접속 기반 Hermes agent 구축
status: draft
owner: BoBeenLee
created: 2026-06-03
updated: 2026-06-03
revisions:
  - { date: 2026-06-03, pr: 0, note: "initial draft — SSH 접속 경로 확정 + Hermes agent 구축 성공 기준 정의" }
---

# MacBook SSH 원격 접속 기반 Hermes agent 구축

## Context

이슈 #36은 "맥북 클로드에 원격으로 접속하여 다른 맥북에 Hermes agent를 구축한다"는 메모에서 출발했다. 원문은 접속 대상, 보안 경계, agent 성공 기준이 비어 있어 `needs-clarification` 상태였지만, 2026-06-03 세션에서 실제 접속 경로를 검증하며 실행 가능한 범위를 좁혔다.

현재 확정된 실행 모델은 Control MacBook에서 Codex Desktop을 사용하고, Hermes MacBook(`BoBeenui-MacBookPro.local`)에 SSH 키 인증으로 접속해 설치·검증 작업을 수행하는 방식이다. Hermes MacBook은 회사 지급 장비이므로 개인 Tailscale 같은 별도 overlay network는 승인 전 사용하지 않고, 같은 신뢰 네트워크에서 열린 SSH 경로를 우선한다.

실측 결과:
- Hermes MacBook 사용자: `bobeenlee`
- Hermes MacBook 호스트명: `BoBeenui-MacBookPro.local`
- 현재 접속 IP: `192.168.0.8`
- SSH 접속 확인: `ssh -i ~/.ssh/id_ed25519_bobeenlee_nopass -o IdentitiesOnly=yes bobeenlee@192.168.0.8`
- 원격 확인 결과: `whoami=bobeenlee`, `hostname=BoBeenui-MacBookPro.local`, `pwd=/Users/bobeenlee`, `sw_vers -productVersion=26.2`
- 디버그 결과: 최초 등록한 passphrase 있는 key는 서버가 public key를 인정했지만, Codex 비대화형 SSH 세션에서 private key passphrase를 풀 수 없어 인증이 최종 실패했다. 따라서 Codex 자동화 전용 no-pass key를 별도로 발급해 Hermes MacBook의 `authorized_keys`에 추가했다.

## Approach

1. **접속 경로를 SSH 키 인증으로 고정한다.** Control MacBook에는 Codex 전용 passphrase 없는 ED25519 key를 두고, Hermes MacBook의 `~/.ssh/authorized_keys`에는 해당 public key를 등록한다. Codex 자동화는 항상 `-i ~/.ssh/id_ed25519_bobeenlee_nopass -o IdentitiesOnly=yes`를 붙여 의도한 키만 사용한다. 기존 passphrase 있는 key는 사람이 직접 SSH할 때는 쓸 수 있지만 Codex의 `BatchMode=yes` 비대화형 실행에는 맞지 않는다.

   운영 가드:
   - private key 파일은 repo에 커밋하지 않고 Control MacBook의 `~/.ssh/`에만 둔다.
   - 접근 회수는 Hermes MacBook의 `~/.ssh/authorized_keys`에서 `codex-to-bobeenlee-nopass` 줄을 제거하는 방식으로 한다.
   - 구현 PR/문서에는 public key fingerprint까지만 남기고 private key, passphrase, secret은 기록하지 않는다.

2. **회사 장비 보안 경계를 plan의 가드레일로 둔다.** 개인 Tailscale, 개인 원격 데스크톱, 외부 tunnel은 기본 비채택이다. 회사 IT/보안팀이 승인한 tailnet/VPN/bastion이 있으면 별도 revision에서 대체 경로로 문서화한다.

3. **Hermes agent 구축은 별도 isolated workspace에서 수행한다.** 원격 홈 아래 `~/Documents/mygit` 또는 승인된 작업 디렉터리에 repo/agent 소스를 배치하고, 설치 스크립트는 idempotent하게 만든다. 회사 장비의 전역 설정 변경은 최소화하고 필요한 경우 명령과 이유를 plan/PR에 남긴다.

4. **운영화는 launchd를 기본 후보로 둔다.** 단기 검증은 foreground 또는 `tmux`로 하고, 상시 실행이 필요하다고 확인되면 user-level `launchd` plist로 승격한다. plist 이름, 로그 경로, restart policy는 구현 PR에서 확정한다.

5. **완료 기준은 "설치됨"이 아니라 "원격에서 재현 가능하게 동작함"으로 둔다.** SSH 접속, agent 프로세스 실행, health check, 로그 확인, 재부팅/재로그인 후 복구 확인까지 통과해야 shipped 후보가 된다.

## Critical files

| 경로 | 역할 | 신규/수정 |
|------|------|-----------|
| `CONTEXT.md` | Control MacBook, Hermes MacBook, Hermes agent, approved remote access path 용어 정의 | 신규 |
| `docs/plans/36-macbook-remote-hermes-agent.md` | 이슈 #36 실행 계획의 단일 진실원 | 신규 |
| `scripts/hermes/install.sh` | Hermes agent 설치/업데이트 스크립트 후보 | 신규 |
| `scripts/hermes/doctor.sh` | SSH 접속, 의존성, agent 실행 상태, 로그 상태 진단 후보 | 신규 |
| `docs/hermes-agent.md` | 수동 운영 절차, SSH 접속 명령, health check, rollback 정리 후보 | 신규 |
| `~/Library/LaunchAgents/<agent-id>.plist` | Hermes MacBook user-level 상시 실행 설정 후보. repo에는 템플릿만 둔다 | 신규 후보 |

## Verification

| 단계 | 액션 | 기대 |
|------|------|------|
| SSH 연결 | `ssh -i ~/.ssh/id_ed25519_bobeenlee_nopass -o IdentitiesOnly=yes bobeenlee@192.168.0.8 'whoami && hostname && pwd'` | `bobeenlee`, `BoBeenui-MacBookPro.local`, `/Users/bobeenlee` 출력 |
| 권한/키 상태 | Hermes MacBook에서 `ssh-keygen -lf ~/.ssh/authorized_keys` | Codex 전용 public key fingerprint가 등록되어 있음 |
| no-pass key 확인 | Control MacBook에서 `ssh-keygen -y -f ~/.ssh/id_ed25519_bobeenlee_nopass >/dev/null` | passphrase prompt 없이 성공 |
| 네트워크 안정성 | Control MacBook에서 `nc -vz 192.168.0.8 22` | SSH port reachable |
| 설치 dry run | `scripts/hermes/install.sh --dry-run` | 변경 예정 항목 출력, secret/private key 미출력 |
| agent foreground | Hermes MacBook에서 agent foreground 실행 | process exits 0 또는 health endpoint/status command 성공 |
| 로그 확인 | `scripts/hermes/doctor.sh` 또는 문서화된 log command 실행 | 최근 실행 로그와 오류 없음 확인 |
| launchd 등록 후보 | user-level plist load/unload dry run 또는 샘플 검증 | user 권한 범위에서만 동작, sudo/system daemon 불필요 |
| 재접속 회복 | SSH 세션 종료 후 재접속, agent status 재확인 | 접속과 status check 모두 재현 가능 |

## Open questions

- [ ] Hermes agent의 실체: 실행할 repo, binary/package, runtime(Node/Python/Claude Code/Codex/기타), 필요한 secret 범위는 무엇인가?
- [ ] Hermes agent의 health check: HTTP endpoint, CLI status, log heartbeat 중 무엇을 성공 기준으로 볼 것인가?
- [ ] 회사 장비 정책상 user-level launchd 등록과 Codex 전용 SSH key 사용이 허용되는가?
- [ ] IP `192.168.0.8`이 DHCP로 바뀔 때 사용할 안정 식별자는 `BoBeenui-MacBookPro.local`로 충분한가, 아니면 DHCP reservation/사내 DNS가 필요한가?
- [ ] agent 로그/작업 산출물에 회사 정보 또는 개인 정보가 포함될 수 있는가? 포함된다면 저장 위치와 보존 기간은?
- [ ] 장애 시 rollback은 단순 process stop인지, plist unload + 파일 삭제 + key 회수까지 포함하는지?

## Domain language updates

| 용어 | 정의 (1~2문장) | 액션 | 비고 |
|------|----------------|------|------|
| Control MacBook | Codex Desktop session이 실행되는 작업자 측 MacBook. 대상 기기에 SSH 또는 화면 공유로 접속해 구축 작업을 수행하는 진입점이다. | add | 이슈 본문의 "맥북 클로드"를 명확한 역할명으로 정리 |
| Hermes MacBook | Hermes agent를 설치·운영할 대상 MacBook. 이 plan에서는 `BoBeenui-MacBookPro.local` 역할의 회사 지급 MacBook을 가리킨다. | add | 이슈 본문의 "다른 맥북"을 명확한 역할명으로 정리 |
| Hermes agent | Hermes MacBook에서 백그라운드로 실행될 자동화 에이전트. 구체 실행 바이너리, 권한, health check는 구현 단계에서 확정한다. | add | 아직 실체 미확정이므로 open question 유지 |
| Approved remote access path | 회사 장비 보안 정책을 우회하지 않는 원격 접속 경로. 같은 신뢰 네트워크 안의 SSH 키 인증을 우선하며 개인 overlay network는 승인 전 사용하지 않는다. | add | Tailscale 검토 중 보안 가드레일로 결정 |

## ADR proposals

ADR 만들지 않음 — 현재 결정은 운영 plan 수준의 가드레일이며 repo 전체 아키텍처를 hard-to-reverse하게 바꾸는 결정은 아니다. 회사 승인 원격 접속 방식이 별도 VPN/bastion으로 확정되거나 Hermes agent runtime을 repo 표준으로 고정하는 시점에 ADR을 재검토한다.

## Alternatives considered

- **개인 Tailscale tailnet**: 같은 Wi-Fi에서 client isolation이 있으면 빠르게 우회할 수 있지만, 회사 지급 MacBook을 개인 overlay network에 붙이는 것은 보안 정책 위반 또는 감사 리스크가 크다. 회사 관리 tailnet 또는 명시 승인 전에는 비채택.
- **macOS Screen Sharing/VNC 중심 운영**: GUI 조작에는 편하지만 반복 가능한 설치/검증 기록이 남기 어렵고 Codex 자동화와도 궁합이 낮다. 초기 설정 보조 수단으로만 둔다.
- **비밀번호 SSH 로그인**: 한 번 접속은 가능하지만 Codex 비대화형 자동화에 부적합하고 비밀번호 입력/보관 리스크가 있다. 키 인증을 채택.
- **passphrase 있는 SSH key 재사용**: 대상 서버는 키를 인정했지만 Codex 비대화형 세션에서 private key passphrase를 풀 수 없어 실패했다. 전용 no-pass key로 분리하고 해당 key의 scope를 Hermes MacBook 접속으로 제한한다.
- **root/system-level daemon**: 부팅 직후 상시 실행에는 강하지만 회사 장비의 보안 변경면이 커진다. user-level launchd로 충분한지 먼저 검증한다.

## Revisions

- 2026-06-03 (#TBD): initial draft — SSH 접속 경로 확정 + Hermes agent 구축 성공 기준 정의
