#!/usr/bin/env bash
# friction.sh 를 가짜 gh 로 검증한다. 실제 GitHub 에는 아무것도 남기지 않는다.
# 사용: bash ops/friction.test.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/bin"
cat > "$TMP/bin/gh" <<'EOF'
#!/usr/bin/env bash
echo "$*" >> "$GH_LOG"
case "$1 $2" in
  "issue list") cat "$GH_LIST" ;;
  "issue create") echo "https://github.com/o/r/issues/1" ;;
  "issue comment") echo "https://github.com/o/r/issues/7#issuecomment-1" ;;
esac
EOF
chmod +x "$TMP/bin/gh"
export PATH="$TMP/bin:$PATH" GH_LOG="$TMP/gh.log" GH_LIST="$TMP/list.json"

git init -q "$TMP/repo"
git -C "$TMP/repo" remote add origin https://github.com/o/r.git

item() { jq -n --arg happened "${1:-유튜브 요약에서 yt-dlp 가 막혔다}" '{title: "yt-dlp 봇 확인", happened: $happened,
  wanted: "자막을 받는다", reproduce: "yt-dlp --write-auto-subs", cost: "10분", preliminary: "player_client 넷 다 막힘"}'; }
run() { : > "$GH_LOG"; bash "$SCRIPT_DIR/friction.sh" "$TMP/repo" 2>&1; }
fail() { echo "FAIL: $1" >&2; exit 1; }

echo '[]' > "$GH_LIST"
out="$(item | run)"
grep -q "^created: https://github.com/o/r/issues/1" <<< "$out"   || fail "새 이슈를 만들지 않았다: $out"
grep -q "issue create -R o/r --title Friction: yt-dlp 봇 확인 --label friction" "$GH_LOG" || fail "라벨이나 제목이 빠졌다"
grep -q "label create friction-skipped" "$GH_LOG"                || fail "friction-skipped 라벨을 챙기지 않았다"

echo '[{"number":7,"title":"Friction: yt-dlp 봇 확인"},{"number":8,"title":"Friction: 다른 것"}]' > "$GH_LIST"
out="$(item | run)"
grep -q "^commented: .*issues/7" <<< "$out"                       || fail "같은 제목인데 댓글로 붙이지 않았다: $out"
grep -q "issue create" "$GH_LOG"                                  && fail "같은 제목인데 새 이슈를 만들었다"

out="$(item | jq '.title = "Friction: yt-dlp 봇 확인"' | run)"
grep -q "^commented: .*issues/7" <<< "$out"                       || fail "접두어를 붙여 넣은 제목이 같은 이슈를 못 찾았다: $out"

out="$(item | jq '.cost = " "' | run)"
grep -q "^skipped: cost" <<< "$out"                               || fail "빈 항목을 건너뛰지 않았다: $out"
[ -s "$GH_LOG" ]                                                  && fail "건너뛰는데 gh 를 불렀다"

out="$(item "/Users/someone/x 에서 막혔다" | run)" && fail "홈 경로가 든 본문을 통과시켰다"
grep -q "^refused:" <<< "$out"                                    || fail "거부 이유를 말하지 않았다: $out"
[ -s "$GH_LOG" ]                                                  && fail "거부하는데 gh 를 불렀다"

out="$(item | FRICTION_ALLOW="o/other" run)" && fail "FRICTION_ALLOW 밖 repo 를 통과시켰다"
out="$(item | FRICTION_ALLOW="o/other o/r" run)"
grep -q "^commented:" <<< "$out"                                  || fail "FRICTION_ALLOW 안 repo 를 막았다: $out"

echo "ok  friction.sh 생성, 댓글, 건너뛰기, 거부"
