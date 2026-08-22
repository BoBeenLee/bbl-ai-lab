#!/usr/bin/env bash
# ops/repos.md manifest에 등록된 운영 repo를 제자리에 클론한다.
# 사용: bash ops/repo-sync.sh [--list]
#   GIT_TOKEN=<pat> 를 주면 https URL에 토큰을 끼워 클론한다.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT/ops/repos.md"

# frontmatter(첫 --- ~ 두 번째 ---)만 잘라 name/url/path/branch 레코드로 편다.
records="$(
  awk '/^---[[:space:]]*$/ { n++; next } n == 1' "$MANIFEST" | awk '
    function flush() { if (name != "") printf "%s\t%s\t%s\t%s\n", name, url, path, branch }
    /^[[:space:]]*-[[:space:]]*name:/ { flush(); name = $3; url = ""; path = ""; branch = "main"; next }
    /^[[:space:]]*url:/    { url = $2;    next }
    /^[[:space:]]*path:/   { path = $2;   next }
    /^[[:space:]]*branch:/ { branch = $2; next }
    END { flush() }
  '
)"

[ -n "$records" ] || { echo "manifest 파싱 실패: $MANIFEST" >&2; exit 1; }
while IFS=$'\t' read -r name url path branch; do
  [ -n "$name" ] && [ -n "$url" ] && [ -n "$path" ] && [ -n "$branch" ] ||
    { echo "manifest 항목이 불완전하다: '$name'" >&2; exit 1; }
done <<< "$records"

if [ "${1:-}" = "--list" ]; then printf '%s\n' "$records"; exit 0; fi

while IFS=$'\t' read -r name url path branch; do
  target="$ROOT/$path"
  if [ -e "$target/.git" ]; then
    echo "skip  $path"
    continue
  fi
  clone_url="$url"
  [ -n "${GIT_TOKEN:-}" ] && clone_url="https://$GIT_TOKEN@${url#https://}"
  echo "clone $path ($branch)"
  git clone --branch "$branch" "$clone_url" "$target"
done <<< "$records"
