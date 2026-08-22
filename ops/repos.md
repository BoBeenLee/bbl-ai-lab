---
repositories:
  - name: hermes-workspace
    url: https://github.com/BoBeenLee/hermes-workspace.git
    path: hermes-workspace
    branch: main
  - name: remote-comfyui
    url: https://github.com/BoBeenLee/remote-comfyui.git
    path: ops/remote-comfyui
    branch: main
  - name: openhuman-altalt-proxy
    url: https://github.com/BoBeenLee/openhuman-altalt-proxy.git
    path: ops/openhuman-altalt-proxy
    branch: main
---

# 운영 repo 목록

`ops/repo-sync.sh` 전용 참조 파일이자 운영 repo 목록의 단일 진실원. 이 hub는 URL과 브랜치만 소유하고, repo 내용은 각 repo가 소유한다. submodule gitlink가 아니므로 하위 repo에 커밋이 생겨도 hub에 포인터 커밋을 만들 필요가 없다.

## 설치

```bash
bash ops/repo-sync.sh
```

이미 클론된 경로는 스킵한다. `GIT_TOKEN=<pat>` 를 주면 https URL에 토큰을 끼워 클론한다.

## repo 추가

이 파일의 frontmatter와 `.gitignore` 두 곳을 함께 고친다. `branch`를 생략하면 `main`으로 클론한다.
