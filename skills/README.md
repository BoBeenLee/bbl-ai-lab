# skills/

Brainstorming/구체화에 사용할 스킬 정의를 모아두는 디렉토리.

Gemini CLI(GitHub Action 안)에서 컨텍스트 파일로 attach 한다.

## 현재 등록된 스킬

| 파일 | 출처 | 용도 |
|------|------|------|
| `product-brainstorming.md` | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) `product-management/skills/product-brainstorming/SKILL.md` | Problem Exploration / Solution Ideation / Assumption Testing 모드 + HMW·JTBD 프레임워크. 단발 Gemini 호출로 idea → issue 구체화에 적합. |

## 추가/교체 방법

1. 새 스킬의 `SKILL.md`를 이 디렉토리에 `<name>.SKILL.md`로 복사한다.
2. 해당 flow 스크립트(예: `scripts/idea-elaborate.sh`)의 `SKILL_FILE` 변수를 가리키게 바꾸거나, 다중 스킬 라우팅 단계로 확장한다.
