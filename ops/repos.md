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
  - name: openmontage
    url: https://github.com/calesthio/OpenMontage.git
    path: ops/openmontage
    branch: main
  - name: games
    url: https://github.com/BoBeenLee/games.git
    path: projects/games
    branch: main
  - name: travel
    url: https://github.com/BoBeenLee/travel.git
    path: projects/travel
    branch: main
  - name: finance
    url: https://github.com/BoBeenLee/finance.git
    path: projects/finance
    branch: main
  - name: music
    url: https://github.com/BoBeenLee/music.git
    path: projects/music
    branch: main
  - name: shopping
    url: https://github.com/BoBeenLee/shopping.git
    path: projects/shopping
    branch: main
  - name: hiking
    url: https://github.com/BoBeenLee/hiking.git
    path: projects/hiking
    branch: main
  - name: cad
    url: https://github.com/BoBeenLee/cad.git
    path: projects/cad
    branch: main
  - name: voice-agent
    url: https://github.com/BoBeenLee/voice-agent.git
    path: projects/voice-agent
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

`path`는 `ops/` 아래일 필요가 없다 — `repo-sync.sh`가 hub 루트 기준 임의 경로를 클론한다.

**`projects/` 아래는 손댈 필요가 없다.** repo를 만들고 origin만 붙인 뒤 `bash ops/repo-sync.sh`를
한 번 돌리면 `repo-sync.sh`가 origin URL과 기본 브랜치를 읽어 이 frontmatter에 등록한다.
`.gitignore`는 `/projects/*/` glob이라 이미 덮고 있다. origin이 없는 디렉터리는 경고만 하고 건너뛴다.

```bash
git -C projects/<name> remote add origin https://github.com/BoBeenLee/<name>.git
bash ops/repo-sync.sh
```

`projects/` 밖(운영 repo)은 여전히 이 파일의 frontmatter와 `.gitignore` 두 곳을 함께 고친다.
`branch`를 생략하면 `main`으로 클론한다.

## private repo

`games`, `travel`, `finance`, `music`, `shopping`, `hiking`, `cad`, `voice-agent`는 private다. 앞의 셋은 계정 로스터,
여행 일정, 재무 프로필 같은 개인 데이터를 이미 담고 있고, `music`은 생성곡·가사·취향이, `shopping`은 구매 이력·
예산·사이즈가, `hiking`은 GPS 경로·체력 수치·장비 이력이, `cad`는 집 실측 치수·제작 이력이, `voice-agent`는
통화 녹음·전사·목소리가 쌓이면 개인 데이터가 되기 때문이다.
나중에 공개에서 비공개로 돌리는 것보다 처음부터 private인 쪽이 싸다.
private repo는 `gh auth` 세션이나 `GIT_TOKEN=<pat>` 없이는 클론되지 않는다.

## 외부 도구 repo

`openmontage` 만 내 소유가 아니다. 업스트림은 [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage),
라이선스는 AGPL-3.0 이다. `repo-sync.sh` 는 클론만 하고 의존성은 설치하지 않는다. venv, npm, `.env` 는
그 repo 자신의 `make setup` 이 만든다.

로컬 수정은 푸시 대상이 없으므로 로컬 커밋으로만 남는다. 푸시가 필요해지면 그때 포크하고 이 항목의 `url` 을 바꾼다.
