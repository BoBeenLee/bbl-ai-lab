#!/usr/bin/env bash
# repo-sync.sh 의 projects/ 자동 등록을 임시 디렉터리에서 검증한다. 실제 repo는 건드리지 않는다.
# 사용: bash ops/repo-sync.test.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/ops" "$TMP/projects"
cp "$SCRIPT_DIR/repo-sync.sh" "$TMP/ops/"
cat > "$TMP/ops/repos.md" <<'EOF'
---
repositories:
  - name: registered
    url: https://example.com/registered.git
    path: projects/registered
    branch: main
---

# prose must survive
EOF

# registered = 이미 manifest에 있음 / adoptme = 미등록+origin / noremote = 미등록+origin 없음
for n in registered adoptme noremote; do
  git -C "$TMP/projects" init -q "$n"
  git -C "$TMP/projects/$n" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
done
git -C "$TMP/projects/adoptme" remote add origin https://example.com/adoptme.git

fail() { echo "FAIL: $1" >&2; exit 1; }

out1="$(bash "$TMP/ops/repo-sync.sh" --list 2>&1)"
grep -q "adopt projects/adoptme" <<< "$out1"                          || fail "origin 있는 미등록 repo를 등록하지 않았다"
grep -q "warn  projects/noremote" <<< "$out1"                         || fail "origin 없는 repo를 경고하지 않았다"
grep -qE "^adoptme\s+https://example.com/adoptme.git\s+projects/adoptme" <<< "$out1" || fail "등록된 항목이 레코드로 안 나온다"
grep -q "noremote" "$TMP/ops/repos.md"                                && fail "origin 없는 repo가 manifest에 들어갔다"
grep -q "# prose must survive" "$TMP/ops/repos.md"                    || fail "frontmatter 아래 산문이 사라졌다"

out2="$(bash "$TMP/ops/repo-sync.sh" --list 2>&1)"
grep -q "adopt " <<< "$out2"                                          && fail "두 번째 실행에서 중복 등록했다"
[ "$(grep -c "path: projects/adoptme" "$TMP/ops/repos.md")" = 1 ]     || fail "adoptme 항목이 중복됐다"

echo "ok  repo-sync.sh projects/ 자동 등록"
