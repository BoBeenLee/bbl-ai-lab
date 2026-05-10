# skills/

Brainstorming/구체화에 사용할 스킬 정의를 모아두는 디렉토리.

Gemini CLI(GitHub Action 안)에서 컨텍스트 파일로 attach 한다.

## 현재 등록된 스킬

| 파일 | 출처 | 용도 |
|------|------|------|
| `office-hours.SKILL.md` | [garrytan/gstack](https://github.com/garrytan/gstack) `office-hours/SKILL.md` | YC office-hours / builder-mode brainstorming. 아이디어를 forcing question으로 압박하고 design doc을 뽑아냄. |

## 추가/교체 방법

1. 새 스킬의 `SKILL.md`를 이 디렉토리에 `<name>.SKILL.md`로 복사한다.
2. `scripts/elaborate.sh`의 `SKILL_FILE` 변수를 가리키게 바꾸거나, 다중 스킬 라우팅 단계로 확장한다.
