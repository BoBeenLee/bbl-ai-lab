# "더 야심 차게" 방식(Altitude, Depth, Range)을 규칙이나 스킬로 둔 오픈소스 조사 (2026-10-23)

이 문서는 Felix Rieseberg 의 글 [How to be more ambitious](https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/)(2026-10-13)에 나온 방식을 매번 프롬프트로 붙이지 않고 규칙, 스킬, 훅으로 둘 때 무엇을 들이고 무엇을 만들지 고르기 위한 자료다. 쓰는 호스트는 Claude Code, Codex CLI, opencode 다. 각 항목은 GitHub API(별, 라이선스, 마지막 push 는 2026-10-23 기준), SKILL.md 와 소스 원문, 공식 문서로 확인했고, 원문을 열지 못한 것은 "미확인"으로 적었다. 계기는 이 글을 소개한 AI LABS 영상([92ZDgn8bgLM](https://www.youtube.com/watch?v=92ZDgn8bgLM))이다.

## 결론

- Felix 글이 나온 지 열흘 만에 이를 옮긴 스킬이 수십 개 나왔다. 대부분 Depth 프롬프트를 그대로 붙인 변형이다. 공식 Anthropic, OpenAI 스킬은 없다. AI LABS 의 유료 `be-ambitious` 는 공개본을 찾지 못했다.
- **Depth 는 새로 쓰지 말고 [OpenAgentsInc/openagents `better`](https://github.com/OpenAgentsInc/openagents/blob/main/.agents/skills/better/SKILL.md)(Apache-2.0)를 바탕으로 한다.** 앞서 구상한 `deeper` 와 모양이 같다. 새 프롬프트를 받으면 다시 쓰기만 하고 멈추고, 진행 중인 작업에 "얕다" 같은 피드백이 오면 brief 를 다시 쓴 뒤 원자료와 바깥 검증까지 돌린다. 범위, 돈, 권한이 바뀌면 묻는다. 다만 명시 호출 전용이라고 설명에만 적었을 뿐 frontmatter 로 막지 않았으니 두 호스트 설정을 더해야 한다.
- Altitude 와 Range 까지 한 스킬에 넣으려면 [sammcj `ambitious-model-use`](https://github.com/sammcj/agentic-coding/blob/d5c9cae02904270e37e0a374a0c819020c5fefc2/Skills/ambitious-model-use/SKILL.md)(Apache-2.0)가 가장 조심스럽다. 사용자 확인 뒤에만 실행하고, 명시 호출만 받고, 트리거 평가 파일이 있다. 반대로 robonuggets 판은 다시 쓴 뒤 바로 실행하므로 무인 봇 턴에 붙이면 안 된다.
- **바깥 판정자는 OpenAI 공식 [openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc)(Apache-2.0, 별 34,487)가 있다.** Claude Code 안에서 Codex 에게 read-only 리뷰를 맡기고, 원하면 Stop 훅으로 Codex 판정을 완료 게이트로 건다. 영상이 손으로 한 `codex exec -s read-only` 흐름이 공식 형태로 이미 있다. 다만 이 Mac 에는 지금 Codex CLI 가 설치돼 있지 않다. 코드가 OpenAI 로 나가므로 사내 코드에는 쓰지 않는다.
- Range 는 들일 것이 없다. 영상처럼 "분야 전문가 여럿을 순서대로, 각자 검사 통과 뒤 인계, 마지막에 사용자 레드팀"을 묶은 공개 저장소는 없다. 설계 본보기로는 [EveryInc `ce-code-review`](https://github.com/EveryInc/compound-engineering-plugin/tree/HEAD/skills/ce-code-review)(MIT)가 가장 낫다. 리뷰어를 직함이 아니라 "읽을 자료, 쓸 프레임워크, diff 에서 확인할 판정 조건"으로 정의하고, 해당 영역이 바뀌었을 때만 띄운다. 큰 에이전트 모음(VoltAgent, agency-agents, SuperClaude 패널, BMAD party mode)은 Felix 가 경계한 역할극 쪽이다.
- **배치는 앞서 낸 안(검증 한 줄은 규칙, Depth 는 명시 호출 스킬)이 공식 문서와 맞는다.** Claude Code 문서는 매번 지켜야 하는 규칙을 스킬이 건너뛰면 훅으로 옮기라고 하고, 규칙 파일은 강제가 아니라 맥락이라고 한다. 스킬 자동 선택은 보장이 없다(제3자 평가에서 56% 가 아예 호출되지 않았다). 출력 스타일은 일반 서브에이전트에 적용되지 않아 이 용도에 맞지 않는다.

## 조사 방법과 읽는 법

- 조사 에이전트 셋을 나눠 돌렸다: (1) Depth, Altitude 구현과 실행 전에 프롬프트를 다시 쓰는 도구, (2) 다른 모델이나 세션을 바깥 판정자로 쓰는 도구, (3) Range 구현과 규칙, 스킬, 훅 배치 근거. 후보는 `gh search code`, `gh search repos` 로 찾고 원문은 `gh api repos/.../contents` 로 읽었다.
- 상위 후보는 메인 세션에서 다시 확인했다. 표의 "직접 확인"이 그것이다. 별과 라이선스는 `gh api repos/<repo>` 의 `stargazers_count`, `license.spdx_id` 를 그대로 옮겼다. GitHub 가 `NOASSERTION` 으로 표시하는 것은 LICENSE 원문을 따로 적었다.
- 갈래 표기: A=Altitude, D=Depth, R=Range, J=바깥 판정자.
- 여러 스킬이 Felix 의 Depth 프롬프트 원문을 그대로 싣는다. 저장소 라이선스는 그 저장소 저자가 쓴 부분에 대한 것이고, 프롬프트 문장은 Felix 의 글이다. 공개 저장소에 옮길 때는 링크와 출처를 달거나 내 말로 다시 쓴다.

## 1. Depth, Altitude 를 옮긴 스킬

| 이름 | 형태 | 라이선스 | 별 | 마지막 push | 하는 일 | 갈래 | 확인 |
|---|---|---|---|---|---|---|---|
| [OpenAgentsInc/openagents `better`](https://github.com/OpenAgentsInc/openagents/blob/main/.agents/skills/better/SKILL.md) | 스킬(1.7KB) | Apache-2.0 | 458 | 10-22 | 새 프롬프트면 네 질문과 다시 쓴 프롬프트만 내고 멈춤. 진행 중 작업이면 다시 하고 바깥 검증까지 | D | 직접 확인 |
| [DannyMac180/skills `be-ambitious`](https://github.com/DannyMac180/skills/blob/7dc63b7a748b8bd14bf213c15ecddd4536409407/be-ambitious/SKILL.md) | 스킬(3.5KB) | MIT | 646 | 10-15 | 분야를 먼저 정하고 네 질문, 다시 쓴 뒤 멈춤. 설명의 NOT FOR 에 범위 확대를 적음 | D | 직접 확인 |
| [sammcj/agentic-coding `ambitious-model-use`](https://github.com/sammcj/agentic-coding/blob/d5c9cae02904270e37e0a374a0c819020c5fefc2/Skills/ambitious-model-use/SKILL.md) | 스킬(3.8KB) + references, evals | Apache-2.0 | 166 | 10-22 | 세 갈래 진단, brief 다시 쓰기, 필요한 접근 목록, 바깥 판정자 지정, 확인 뒤 실행 | A, D, R | 직접 확인 |
| [robonuggets/be-ambitious](https://github.com/robonuggets/be-ambitious/blob/dc116a3ebd8cf772e4d0930626f67369bd60399d/SKILL.md) | 스킬(10.8KB) | MIT | 100 | 10-17 | Altitude 3칸 사다리, Depth 프롬프트, Range 전문가 조합. 과제면 다시 쓴 뒤 바로 실행 | A, D, R | 라이선스 직접 확인 |
| [r3dlex/deepen-prompt](https://github.com/r3dlex/deepen-prompt/blob/ac80fc4a8568b5ad142719f9149ef45d5fe04ac3/skills/deepen-prompt/SKILL.md) | 스킬 + CC 플러그인 + opencode 명령 | MIT | 9 | 10-17 | 판정자 순위(돌리는 도구 > 처음 보는 데이터 예측 > 외부 기준 > 사람), 목표 몰래 바꾸기와 역할극을 금지 패턴으로 | D | 라이선스 직접 확인 |
| [cursor/plugins pstack `sharpen`](https://github.com/cursor/plugins/blob/9b93e81fb2921b9263d9463c15bafeabfe3903aa/pstack/skills/sharpen/SKILL.md) | Cursor 플러그인 스킬 | MIT(`pstack/LICENSE`, 저장소 루트는 없음) | 13,596 | 10-22 | Depth 프롬프트에 "선택은 사용자 몫으로 남겨라" 한 줄을 더함 | D | LICENSE 직접 확인 |
| [pronskiy/skills `reprompt`](https://github.com/pronskiy/skills) | CC 플러그인 | MIT | 14 | 10-15 | 늘린 목표를 프롬프트에 넣지 않고 따로 제안 | A, D, R | README 만 |
| [severity1/claude-code-prompt-improver](https://github.com/severity1/claude-code-prompt-improver) | CC 훅 + 스킬 | MIT | 1,961 | 10-01 | 매 프롬프트 명확성을 평가하고 모호하면 질문. Depth 가 아니라 명확성 | 해당 없음 | 라이선스 직접 확인 |

`better` 원문에서 확인한 것:
- 설명이 `/better`, `$better` 로 명시 호출할 때만 쓰라고 하지만 `disable-model-invocation` 같은 차단 필드는 없다.
- Case B 의 3단계가 "목표가 바뀌거나 범위가 넓어지거나 사용자만 줄 수 있는 결정, 돈, 접근이 필요하면 보여 주고 기다린다"이다. 범위가 커지는 문제를 막는 장치다.
- Case B 의 4단계가 2번 답의 원자료와 3번 답의 도구로 다시 하고, 보고 전에 4번 답의 검사를 돌려 결과를 말하게 한다.

`ambitious-model-use` 원문에서 확인한 것:
- frontmatter 에 `disable-model-invocation: true` 가 있다.
- 6단계가 2~5단계 결과를 사용자에게 보여 주고 확인받은 뒤에만 실행하게 한다.
- 표현만 다듬는 요청은 같은 저장소의 `prompt-enhancer` 로 보낸다.

### 이미 가진 스킬과 비교

- 4번 질문(나나 모델 말고 결과를 증명할 것)은 `unlazy` 의 GATES.md `CHECK:`/`EXPECT:` 가 맡는다. 새로 들일 필요가 없다.
- `goal-scoper` 는 요청을 yes/no 기준과 Out of Scope 로 고정해 범위를 좁힌다. Altitude 는 반대로 요청 너머의 결과를 묻는다. 둘을 잇는 스킬(고른 목표를 GOAL.md Objective 로, 4번 답을 GATES CHECK 로 넘김)은 찾지 못했다.
- 1~3번 질문(전문가가 하는 일, 원자료, 방법과 도구)을 맡은 스킬은 가진 것 중에 없다.

## 2. 바깥 판정자

| 이름 | 형태 | 라이선스 | 별 | 마지막 push | 부르는 방향 | 하는 일 | 확인 |
|---|---|---|---|---|---|---|---|
| [openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc) | CC 플러그인(명령, 서브에이전트, Stop 훅) | Apache-2.0 | 34,487 | 07-08 | Claude Code 에서 Codex | review, adversarial-review(read-only), 선택형 Stop 리뷰 게이트, rescue 위임 | 직접 확인 |
| [chaseai-yt/claudex-loop](https://github.com/chaseai-yt/claudex-loop) | 스킬 4개(`.claude-plugin`, `.codex-plugin`) | MIT 에 출처 표기(GitHub 는 NOASSERTION) | 3,185 | 10-14 | 양방향, 리뷰어는 항상 상대 쪽 | 계획 리뷰, 빌드, 새 세션 최종 검사 | 별, 라이선스 직접 확인 |
| [trailofbits/skills `second-opinion`](https://github.com/trailofbits/skills/tree/main/plugins/second-opinion) | 스킬 | CC-BY-SA-4.0(저장소 전체) | 7,727 | 10-22 | Claude Code 에서 Codex, Gemini CLI 등 | 같은 diff 를 외부 CLI 에 넘겨 구조화된 findings 를 받음 | 별, 라이선스 직접 확인 |
| [BeehiveInnovations/pal-mcp-server](https://github.com/BeehiveInnovations/pal-mcp-server)(구 zen-mcp-server) | MCP | Apache-2.0(LICENSE 원문, GitHub 는 NOASSERTION) | 11,802 | 2025-12-15 | MCP 호스트에서 Gemini, OpenAI API 와 CLI | consensus, codereview, clink | 별 직접 확인 |
| Claude Code 내장 Stop 훅 `type: "prompt"`, `"agent"`, `/goal` | 내장 | 해당 없음 | - | - | 같은 호스트의 별도 Claude | 별도 모델이 멈춰도 되는지 판정 | [hooks 문서](https://code.claude.com/docs/en/hooks) |

`codex-plugin-cc` 에서 확인한 것:
- [hooks/hooks.json](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/hooks/hooks.json): Stop 훅이 `stop-review-gate-hook.mjs` 를 timeout 900초로 부른다. `/codex:setup --enable-review-gate` 로 켤 때만 판정한다(조사 에이전트가 스크립트에서 확인).
- [prompts/stop-review-gate.md](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/prompts/stop-review-gate.md): 직전 Claude 턴이 코드를 고쳤을 때만 보고, 첫 줄을 `ALLOW:` 나 `BLOCK:` 로 답한다. Claude 의 말을 코드 변경의 증거로 삼지 말고 저장소 상태로 확인한 뒤에만 막으라고 한다.
- 판정은 Codex 모델의 판단이다. 테스트 실행을 강제하지는 않는다.
- `/codex:rescue` 는 기본이 쓰기 권한이다(조사 에이전트가 [agents/codex-rescue.md](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/agents/codex-rescue.md) 에서 확인). 리뷰만 쓴다.

가진 것의 빈틈:
- 허브의 loop-verifier(2026-10 정리 때 삭제) 는 `model: inherit` 이고 `tools` 줄이 없어 모든 도구가 열려 있다. 같은 계열 모델이 판정하고, 쓰기 권한이 있고, 구현한 쪽이 불러야만 돈다.
- 바깥 도구들은 세 점이 다르다: 다른 계열 모델이 판정하고, Stop 훅이 하네스 차원에서 강제하고, 읽기 전용을 프롬프트가 아니라 CLI 샌드박스가 막는다.
- GATES.md 의 `CHECK:` 를 Stop command 훅으로 결정적으로 돌려 막는 도구는 찾지 못했다.

공식 옵션(조사 에이전트가 문서와 소스로 확인):
- `claude -p`: `--output-format json`, `--json-schema`, `--permission-mode plan|dontAsk`, `--allowedTools`, `--bare`, `--max-turns`, `--max-budget-usd`([headless](https://code.claude.com/docs/en/headless), [cli-reference](https://code.claude.com/docs/en/cli-reference)). `--bare` 가 아니면 `-p` 세션도 프로젝트 훅과 `.mcp.json` 을 실행하므로, 리뷰어로 띄우면 Stop 게이트가 재귀로 돌 수 있다.
- `codex exec`: 기본 샌드박스가 read-only, `-s read-only|workspace-write|danger-full-access`, `-o/--output-last-message`, `--output-schema`, `--ephemeral`, `exec review --uncommitted|--base|--commit`([exec/src/cli.rs](https://github.com/openai/codex/blob/main/codex-rs/exec/src/cli.rs)). `exec resume` 에서는 `--sandbox` 대신 `-c sandbox_mode=...` 를 쓴다.

## 3. Range

| 이름 | 형태 | 라이선스 | 별 | 마지막 push | 하는 일 | 역할극인가 | 확인 |
|---|---|---|---|---|---|---|---|
| [EveryInc `ce-code-review`](https://github.com/EveryInc/compound-engineering-plugin/tree/HEAD/skills/ce-code-review) | 플러그인 스킬 + 리뷰어 프롬프트 파일 | MIT | 25,660 | 10-22 | diff 영역으로 리뷰어를 골라 병렬 리뷰, 검증, 교차 모델 적대 리뷰. Codex, OpenCode 지원 | 실제 작업 | 직접 확인 |
| [anthropics/claude-plugins-official `code-review`](https://github.com/anthropics/claude-plugins-official/blob/HEAD/plugins/code-review/commands/code-review.md) | CC 플러그인 명령 | Apache-2.0 | 43,867 | 10-22 | 리뷰어 5명에게 읽을 자료를 정해 줌(CLAUDE.md, diff, git blame, 이전 PR 코멘트, 코드 주석), 신뢰도 80 미만 버림 | 실제 작업 | 별, 라이선스 직접 확인 |
| [cskwork/persona-product-tester](https://github.com/cskwork/persona-product-tester/blob/HEAD/SKILL.md) | 스킬 | MIT | 0 | 10-21 | 사용자 페르소나가 화면에 보이는 단서만으로 제품을 한 동작씩 조작. 되돌릴 수 없는 행동은 허락 없이 안 함 | 실제 작업 | 별, 라이선스 직접 확인 |
| [garrytan/gstack](https://github.com/garrytan/gstack) | 스킬 23개 묶음 | MIT | 137,306 | 10-22 | `/autoplan` 이 CEO, 디자인, 엔지니어링, DX 리뷰를 차례로, `/qa` 는 재현, 회귀 테스트, 수정, 재검증 | 직함은 있지만 실제 작업 | 별, 라이선스 직접 확인 |
| [obra/superpowers `subagent-driven-development`](https://github.com/obra/superpowers/blob/HEAD/skills/subagent-driven-development/SKILL.md) | 스킬 | MIT | 303,691 | 10-22 | 과제마다 새 구현 서브에이전트와 spec, 품질 리뷰 게이트 | 분야 다양성이 아니라 게이트 | 별, 라이선스 직접 확인 |
| VoltAgent, agency-agents, SuperClaude `/sc:spec-panel`, BMAD `party-mode` | 에이전트 모음, 명령 | MIT 등 | 수만 | - | 분야별 페르소나, 실존 인물 패널, 원탁 대화 | 역할극 | 조사 에이전트 확인 |

`ce-code-review` 에서 확인한 것:
- [설계 문서](https://github.com/EveryInc/compound-engineering-plugin/blob/HEAD/docs/solutions/skill-design/named-frameworks-with-detection-conditions-for-review-personas.md) 25행이 페르소나 프롬프트 연구 결과를 근거로, 점검 항목에 프레임워크 이름은 붙이되 사람 이름은 붙이지 말라고 한다: "Named frameworks help; named people do not." Felix 의 역할극 경고와 같은 결론이다.
- [dispatch-reviewers.md](https://github.com/EveryInc/compound-engineering-plugin/blob/HEAD/skills/ce-code-review/references/dispatch-reviewers.md): 리뷰어 프롬프트 파일을 읽어 범용 서브에이전트에 넘기고, 호스트의 에이전트 타입으로 등록하지 않는다. 그래서 세 호스트에서 같은 스킬이 돈다(조사 에이전트 확인).
- 명사를 동사로 바꾸는 단계 자체를 둔 스킬은 찾지 못했다.

## 4. 어디에 둘지: 공식 근거

| 수단 | Claude Code | Codex | 확실성 |
|---|---|---|---|
| 규칙 파일 | CLAUDE.md 는 세션 시작에 전체가 들어가고 `/compact` 뒤 다시 읽힌다. 강제 설정이 아니라 맥락이다([memory](https://code.claude.com/docs/en/memory)) | AGENTS.md 를 실행마다 이어 붙인다. 합계 32KiB 를 넘으면 뒤는 생략([agents-md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)) | 항상 보이지만 따르는 것은 모델 판단 |
| 스킬 | 이름과 설명만 매번 보인다. 설명은 항목당 1,536자, 목록 전체는 컨텍스트의 1% 예산. `disable-model-invocation: true` 면 설명이 맥락에 안 올라가고 `/name` 으로만 불린다. compaction 뒤에는 최근 호출한 스킬 앞 5,000토큰만 다시 붙는다([skills](https://code.claude.com/docs/en/skills)) | `$name` 명시 호출 또는 설명 매칭. 명시 호출만 받으려면 `agents/openai.yaml` 에 `policy.allow_implicit_invocation: false`. Codex 는 `disable-model-invocation` 을 처리하지 않는다(소스에서 못 찾음) | 자동 선택은 보장 없음. 명시 호출은 확실 |
| 훅 | 이벤트마다 모델 판단 없이 실행. `UserPromptSubmit` 출력이 맥락에 들어간다. 스킬 frontmatter 의 `hooks` 로 스킬과 함께 둘 수 있다([hooks](https://code.claude.com/docs/en/hooks)) | `UserPromptSubmit`, `Stop` 이 있고 기본으로 켜져 있다. 관리되지 않는 훅은 신뢰 승인이 필요([hooks](https://learn.chatgpt.com/docs/hooks)) | 실행은 결정적. 막는 것은 차단형 훅뿐 |
| 출력 스타일 | 메인 대화에만 적용되고 일반 서브에이전트에는 안 된다([output-styles](https://code.claude.com/docs/en/output-styles)) | 같은 기능 없음 | 이 용도에 안 맞음 |

- Claude Code 스킬 문서의 문제 해결 절은 매번 지켜야 할 규칙을 Claude 가 건너뛰면 훅으로 옮기라고 한다. 판단이 필요한 지침은 작업 전체에 걸리게 쓰라고 한다(직접 확인).
- [Vercel 평가](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals)(2026-01-27, 제3자, 에이전트와 모델 미공개): 문서 없음 53%, 스킬 기본 53%, 스킬을 쓰라고 명시 79%, AGENTS.md 문서 인덱스 100%. 56% 경우에 스킬이 호출되지 않았다(직접 확인).
- opencode 는 `~/.claude/skills` 와 `~/.agents/skills` 를 모두 읽는다. 지금처럼 한쪽을 다른 쪽에 링크하면 같은 스킬이 두 번 보일 수 있다(처리 방식은 미확인).

## 들일 순서

1. **Depth 스킬(만듦, 2026-10-23)**: `better`(커밋 037cf47) 본문을 바탕으로 `~/.agents/skills/deeper` 를 만들었다. Apache-2.0 LICENSE 와 변경 표시를 함께 두었다. Claude Code 용 `disable-model-invocation: true` 와 Codex 용 `agents/openai.yaml` 의 `allow_implicit_invocation: false` 를 더했고, 작업이 크면 4번 답을 unlazy GATES.md 로 넘긴다. Claude Code 에서 `claude -p "/deeper ..."` 로 불렀을 때 네 질문과 다시 쓴 프롬프트만 내고 멈췄고, 모델은 스킬 목록에서 `deeper` 를 보지 못했다(대조군 `unlazy` 는 보임). Codex 쪽은 CLI 가 없어 명세 대조만 했다.
2. **검증 한 줄**: dotfiles CLAUDE.md 의 Verification & Evidence 에 "비자명한 작업의 완료는 바깥 증거로 판정한다"를 넣는다.
3. **Codex 리뷰**: Codex 로그인을 되살린 뒤 `codex-plugin-cc` 의 `/codex:review` 만 쓴다. Stop 게이트는 멈출 때마다 Codex 를 돌려 비용이 크니 보류한다. 사내 코드에는 쓰지 않는다.
4. **보류**: Range 패널(필요해지면 `ce-code-review` 처럼 리뷰어 파일 몇 개를 references 에 둔다), UserPromptSubmit 훅(스킬이 제때 안 불리는 일이 실제로 생기면), loop-verifier 의 `tools` 제한(허브 루프 쪽 별도 작업).

## 남은 확인

- 이 Mac 에 Codex CLI 가 없다(2026-10-23 확인: ChatGPT.app 도 `codex` 바이너리도 없음). `codex-plugin-cc` 와 `deeper` 의 Codex 쪽 시험은 설치 뒤로 미룬다.
- `better` 의 Case B(진행 중 작업 다시 하기)가 Claude Code 와 Codex 에서 실제로 범위를 지키는지 시험.
- opencode 가 링크된 두 스킬 경로에서 같은 스킬을 한 번만 보여 주는지.
- Codex 에서 AGENTS.md 가 compaction 뒤 다시 들어가는지.
- AI LABS 유료 `be-ambitious` 의 내용. 공개본이 없어 비교하지 못했다.
