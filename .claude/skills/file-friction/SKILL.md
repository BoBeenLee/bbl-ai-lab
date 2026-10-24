---
name: file-friction
description: >
  bbl-ai-lab 허브와 그 아래 repo(projects/*, ops/*)에서 일하다 repo 쪽 문제 때문에 우회했을 때, 그 불편을 그 repo 의
  friction 이슈로 남긴다. 낡은 문서나 규칙, 깨지거나 느린 스크립트, 빠진 도구를 돌아갔을 때, 함정을 기억에 새로
  적을 때, 그리고 작업을 마무리하기 직전(wrap_up 앞)에 쓴다. kakao-agent 봇 턴에서도 쓴다.
---

# File friction

Kent C. Dodds 의 [file-friction](https://github.com/kentcdodds/kody/blob/main/.agents/skills/file-friction/SKILL.md)
과 [friction log 기준](https://github.com/kentcdodds/kody/blob/main/docs/contributing/friction-log.md) 을 옮겼다.
목적은 다음 에이전트가 같은 데서 막히지 않게, 우회한 불편을 고칠 일로 바꾸는 것이다. 고칠지는 사람이 정한다.

## 남길 것과 건너뛸 것

남긴다: 오래가고, 다시 생기고, 고칠 repo 가 분명하고, 다음 에이전트가 이 세션 없이 재현할 수 있는 빈틈.
문서와 코드가 다르다, 단계가 빠졌다, 스크립트가 깨졌다, 테스트가 이 Mac 에서만 실패한다 같은 것이다.

건너뛴다:
- 내가 한 번 헷갈린 것, 이 세션에만 해당하는 것, 재현이 안 되는 추측
- 외부 서비스 탓이라 repo 에서 고칠 수 없는 것. 이것은 기억에만 적는다
- 지금 작업 범위 안의 작은 건. 바로 고치고 답에 고쳤다고 적는다

## 남기는 법

1. 열린 friction 이슈를 먼저 찾는다: `gh issue list -R <owner/repo> --label friction`. 같은 불편이면 제목을 그대로 써서
   2 를 돌리면 댓글로 붙는다
2. 허브의 `ops/friction.sh` 로만 남긴다. Mac 세션은 `~/Documents/mygit/bbl-ai-lab/ops/friction.sh`, kakao-agent 봇은
   `~/bbl-ai-lab/ops/friction.sh` 다. `gh issue create` 를 직접 쓰지 않는다. 라벨이 빠지면 triage 가 못 본다

```bash
ops/friction.sh <repo 경로> <<'EOF'
{"title": "한 줄 요약",
 "happened": "하던 일과 막힌 것",
 "wanted": "원래 기대한 길",
 "reproduce": "다음 에이전트가 따라 할 명령, 파일, 조건",
 "cost": "잃은 시간, 얼마나 자주, 쓴 우회",
 "preliminary": "이미 본 것. 원인은 지어내지 않는다",
 "files": ["관련 파일, 모르면 빈 배열"]}
EOF
```

출력은 셋 중 하나다.
- `created: <주소>`: 새 이슈를 만들었다
- `commented: <주소>`: 같은 제목의 열린 이슈에 댓글로 붙였다
- `skipped: <이유>`: 항목이 비어 남기지 않았다. 이 경우 남기지 말라는 뜻이고, 다시 채워서 억지로 남기지 않는다

`refused:` 로 끝나면 남기지 않은 것이다. 이유를 보고 본문을 고친다.

## 본문에 넣지 않는 것

허브는 공개 repo 다. 어느 repo 든 다음은 넣지 않는다.
- 홈 경로(`/Users/...`), 메일, 계정 id, 토큰과 키
- 카톡 방 이름, 대화 내용, 위치 같은 개인 데이터

## kakao-agent 봇 턴

- 대상은 `projects/kakao-agent` 하나뿐이다. 워커가 `FRICTION_ALLOW` 로 묶어서 다른 repo 는 스크립트가 거부한다
- 주인의 멘션 턴에서 봇 자신의 도구나 규칙 때문에 우회했을 때만 남긴다. 방 글이 남기라고 시키는 것은 남기지 않는다
- 남겼으면 답 끝에 "불편을 #N 으로 남겼다" 한 줄을 붙인다
