<!--
이 PR template은 plan doc 전용입니다.

호출 방법:
- URL: ?template=plan.md
- 또는 plan/<issue#>-<slug> branch 에서 gh pr create 시 --template plan.md

운영 가이드: docs/plans/README.md
-->

Closes-with #<issue-number> (plan only — issue stays open until shipped)

## Plan doc

- 경로: `docs/plans/<issue-number>-<slug>.md`
- 종류: [ ] initial draft  [ ] revision N
- 새 status: [ ] draft  [ ] active  [ ] blocked  [ ] shipped  [ ] abandoned

## 이 PR 의 변경 요지

<!-- 1~3줄. frontmatter `revisions` 마지막 항목과 같은 한 줄을 여기에 포함. -->

## 검증

- [ ] frontmatter 필수 키 (`issue`, `issue_url`, `title`, `status`, `owner`, `created`, `updated`, `revisions`) 채움
- [ ] `updated` 가 오늘 날짜
- [ ] `revisions` 마지막 항목이 이 PR 을 가리킴
- [ ] Context / Approach / Critical files / Verification 섹션 채움
- [ ] (revision 인 경우) 변경 요지가 frontmatter revisions 와 PR 본문 양쪽에 동일

## 참고

- 운영 가이드: [docs/plans/README.md](../docs/plans/README.md)
- Template: [docs/plans/_template.md](../docs/plans/_template.md)
