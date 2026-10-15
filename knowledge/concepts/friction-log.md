---
type: Project Concept
title: Friction log
description: 에이전트가 일하다 우회한 repo 쪽 불편을 그 repo 의 friction 라벨 이슈로 남기고, daily triage 가 모아 사람에게 보여 주는 통로.
resource: ../../.claude/skills/file-friction/SKILL.md
tags: [friction, loop, daily-triage, kakao-agent]
timestamp: 2026-10-15T00:00:00+09:00
---

# Friction Log

에이전트는 느린 스크립트나 낡은 문서를 만나면 우회하고 넘어간다. 그 일은 그 세션에서 끝나고, 다음 에이전트가 같은 데서
또 막힌다. friction log 는 그 우회를 고칠 일 목록으로 바꾼다. Kent C. Dodds 가 kody 에서 쓰는 방식을 옮겼다
([기준 문서](https://github.com/kentcdodds/kody/blob/main/docs/contributing/friction-log.md)). 다만 그쪽은 Kody 서비스
패키지가 이슈를 만들고 매일 정리하는데, 여기서는 그 역할을 `gh` 를 감싼 스크립트와 기존 daily triage 루프가 나눠 맡는다.

# 흐름

1. 이 Mac 의 Claude Code 세션이나 kakao-agent 봇 턴이 repo 쪽 문제로 우회한다
2. `file-friction` 스킬이 남길 만한지 판단한다(오래가고, 다시 생기고, 고칠 repo 가 분명하고, 재현되는가)
3. `ops/friction.sh` 가 그 repo 에 `friction` 라벨 이슈를 만들거나, 같은 제목의 열린 이슈에 댓글로 붙인다
4. daily triage 가 모든 repo 의 열린 friction 이슈를 모아 `STATE.md` Watch List 에 올린다
5. 사람이 고칠 것을 골라 세션에 맡긴다. 제품 결정이 필요한 건은 `friction-skipped` 를 붙여 sweep 에서 뺀다

# 파일

| File | Role |
|------|------|
| `.claude/skills/file-friction/SKILL.md` | 남길 것과 건너뛸 것, 남기는 법. `~/.agents/skills` 에 설치해 Mac 세션과 봇이 같이 본다 |
| `ops/friction.sh` | 이슈 생성, 라벨 강제, 같은 제목이면 댓글, 빈 항목이면 건너뛰기, 비밀 값 거부 |
| `ops/friction.test.sh` | 가짜 `gh` 로 위 동작을 검증한다 |
| `.github/ISSUE_TEMPLATE/friction.yml` | 사람이 손으로 남길 때 쓰는 양식 |
| `.claude/skills/loop-triage/SKILL.md` | 매일 friction 이슈를 모은다 |

# Boundary

- 이슈를 남기기까지만 자동이다. 고치는 자동 에이전트는 없다. 루프는 L1 그대로 보고만 한다
- kakao-agent 봇은 `FRICTION_ALLOW` 로 자기 repo(private) 하나에만 남긴다. 허브는 공개라 방 글이 이슈 내용으로 새면 안 된다
- 외부 서비스 탓이라 repo 에서 못 고치는 것은 이슈가 아니라 기억에 둔다

Related: [Autonomous loop](autonomous-loop.md)
