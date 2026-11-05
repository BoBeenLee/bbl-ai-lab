#!/usr/bin/env bash
# 그 repo 에 friction 이슈를 남긴다. Kent C. Dodds 의 friction-log 패키지가 하던 일(라벨 강제, 같은 제목이면 댓글,
# 항목이 비면 건너뛰기)을 gh 로 한다. 언제 남기는지는 .claude/skills/file-friction/SKILL.md 가 정한다.
# 사용: ops/friction.sh <repo 경로> < item.json
#   item.json: {"title","happened","wanted","reproduce","cost","preliminary","files"}, files 만 비워도 된다
#   FRICTION_ALLOW="owner/a owner/b" 가 있으면 그 밖의 repo 는 거부한다 (kakao-agent 봇은 자기 repo 하나로 묶는다)
#   github.com 이 아닌 repo(사내 OSS 등)는 GitHub 이슈 대신 Jira 모음 티켓에 코멘트로 남긴다.
#   티켓 키는 FRICTION_JIRA_ISSUE 또는 ~/.config/friction/jira-issue 에서 읽는다. 공개 repo 라 키를 여기 적지 않는다
set -euo pipefail

dir="${1:?usage: friction.sh <repo path> < item.json}"
item="$(cat)"
url="$(git -C "$dir" remote get-url origin)"
case "$url" in
  https://github.com/*|git@github.com:*) target=github ;;
  *) target=jira ;;
esac
repo="$(sed -E 's#^(https?://[^/]+/|git@[^:]+:)##; s#\.git$##' <<< "$url")"

if [ -n "${FRICTION_ALLOW:-}" ]; then
  case " ${FRICTION_ALLOW//,/ } " in
    *" $repo "*) ;;
    *) echo "refused: $repo 는 FRICTION_ALLOW 밖이다" >&2; exit 2 ;;
  esac
fi

for k in title happened wanted reproduce cost preliminary; do
  v="$(jq -r --arg k "$k" '.[$k] // "" | tostring | gsub("^\\s+|\\s+$"; "")' <<< "$item")"
  [ -n "$v" ] || { echo "skipped: $k 가 비었다"; exit 0; }
done

# 열린 이슈 목록의 제목을 그대로 넣어도 접두어가 두 번 붙지 않게 한다. 두 번 붙으면 중복 검사를 빠져나간다.
title="$(jq -r '.title' <<< "$item")"
title="Friction: ${title#Friction: }"
body="$(jq -r '
  def files: (.files // "") | (if type == "array" then join("\n") else tostring end) | if . == "" then "모름" else . end;
  "### 무슨 일\n\(.happened)\n\n### 원한 것\n\(.wanted)\n\n### 재현 방법\n\(.reproduce)\n\n### 비용\n\(.cost)\n\n### 이미 본 것\n\(.preliminary)\n\n### 관련 파일\n\(files)"
' <<< "$item")"

# ponytail: 흔한 꼴만 잡는다. 공개 repo(허브)에 홈 경로, 메일, 비밀 값이 새는 것을 막는 마지막 그물이지 검사기가 아니다.
if grep -Eiq '/Users/|/home/|[[:alnum:]._%+-]+@[[:alnum:].-]+\.[a-z]{2,}|(api[_-]?key|secret|password|token)[[:space:]]*[:=]|ghp_|gho_|github_pat_|sk-[[:alnum:]]{10,}|xox[bp]-' <<< "$title"$'\n'"$body"; then
  echo "refused: 본문에 홈 경로, 메일, 비밀 값 꼴이 있다" >&2
  exit 2
fi

if [ "$target" = jira ]; then
  key="${FRICTION_JIRA_ISSUE:-$(cat "$HOME/.config/friction/jira-issue" 2>/dev/null || true)}"
  [ -n "$key" ] || { echo "refused: $repo 는 Jira 모음 티켓으로 남기는데 FRICTION_JIRA_ISSUE 가 없다" >&2; exit 2; }
  cli="${FRICTION_JIRA_CLI:-$HOME/.claude/skills/naver-jira/scripts/jira_api.py}"
  head="[$repo] ${title#Friction: }"
  body="${body//### /h5. }"
  # ponytail: 최근 코멘트 200개의 앞머리만 본다. 모음 티켓이 그보다 커지면 월 단위로 새 티켓을 연다
  if python3 "$cli" comments "$key" --max 200 | grep -qF "h4. $head"; then
    python3 "$cli" comment "$key" "h4. (재발) $head"$'\n\n'"$body" >/dev/null
  else
    python3 "$cli" comment "$key" "h4. $head"$'\n\n'"$body" >/dev/null
  fi
  echo "commented: jira $key"
  exit 0
fi

gh label create friction -R "$repo" --force --color d93f0b --description "작업 중 겪은 repo 쪽 불편" >/dev/null
gh label create friction-skipped -R "$repo" --force --color cccccc --description "제품 결정이 필요해 sweep 이 건너뛴다" >/dev/null

existing="$(gh issue list -R "$repo" --label friction --state open --search "\"${title#Friction: }\" in:title" --json number,title \
  | jq -r --arg t "$title" '[.[] | select(.title == $t)][0].number // empty')"

if [ -n "$existing" ]; then
  echo "commented: $(gh issue comment "$existing" -R "$repo" --body "$body")"
else
  echo "created: $(gh issue create -R "$repo" --title "$title" --label friction --body "$body")"
fi
