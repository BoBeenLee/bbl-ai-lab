#!/usr/bin/env bash
# ops/repos.md manifest에 등록된 운영 repo를 제자리에 클론한다.
# 사용: bash ops/repo-sync.sh [--list]
#   GIT_TOKEN=<pat> 를 주면 https URL에 토큰을 끼워 클론한다.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT/ops/repos.md"

# projects/ 아래 클론 중 manifest에 없는 것을 origin URL을 읽어 자동 등록한다.
# 손으로 manifest를 고치는 단계를 없앤다. 등록된 뒤에는 no-op이다.
for dir in "$ROOT"/projects/*/; do
  [ -e "$dir/.git" ] || continue
  name="$(basename "$dir")"
  grep -qE "^[[:space:]]*path:[[:space:]]*projects/$name[[:space:]]*$" "$MANIFEST" && continue

  url="$(git -C "$dir" remote get-url origin 2>/dev/null || true)"
  if [ -z "$url" ]; then
    echo "warn  projects/$name: origin remote가 없어 등록하지 못했다 (git remote add origin <url>)" >&2
    continue
  fi

  # 기본 브랜치를 우선한다. 피처 브랜치를 체크아웃한 채 등록하면 그 브랜치가 사라진 뒤 클론이 깨진다.
  branch="$(git -C "$dir" symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || true)"
  branch="${branch#origin/}"
  [ -n "$branch" ] || branch="$(git -C "$dir" branch --show-current)"
  [ -n "$branch" ] || branch=main

  echo "adopt projects/$name ($branch)"
  # frontmatter 닫는 --- 바로 앞에 끼운다. BSD awk는 -v 값에 개행을 못 받으므로 필드별로 넘긴다.
  awk -v name="$name" -v url="$url" -v branch="$branch" '
    /^---[[:space:]]*$/ && ++n == 2 {
      printf "  - name: %s\n    url: %s\n    path: projects/%s\n    branch: %s\n", name, url, name, branch
    }
    { print }
  ' "$MANIFEST" > "$MANIFEST.tmp"
  mv "$MANIFEST.tmp" "$MANIFEST"
done

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
