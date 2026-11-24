# Decisions log

Source: the gate-library build specification v1.0 (2026-11-24). Architecture follows `dsa-library`
(same file roles, rule-table style, hook, workflow). Newest entries go last.

## Questions the owner answered before the build (2026-11-24)

| # | Question | Answer | Effect |
| --- | --- | --- | --- |
| 1 | Existing GATE notes in `gate-notes-extract/` | They duplicate `study-notes`; keep one, remove the other | Verified all 18 files byte-identical in `study-notes`, removed `gate-notes-extract/` (no force flags). Notes are not imported |
| 2 | Where do the syllabus files come from | The syllabus is already downloaded | DA and CS were read from `~/Downloads/personal/{DA,CS}_GATE2027_Syllabus.pdf` (IIT Madras, GATE 2027). GA is not in those files, so it was fetched from the official PDF |
| 3 | Portfolio navigation | Reach GATE through the LIBRARY button, like other library pages | No nav edits in `fmfalgun.github.io`; the page is added to the `library` repo (see below) |
| 4 | GitHub steps | Go ahead on all | Repo creation, Pages, push and PR are done by the build |

## Spec gaps and how they were closed

| # | Topic | Decision | Why |
| --- | --- | --- | --- |
| 5 | `exists_check: "index"` | New code in `checks/xrefs.py`: fetch `<base>api/v1/index.json`, look for the slug in `items`; dsa-library only had `manifest` | Spec asks for it; dsa-library is untouched |
| 6 | G15 "alias clash" | Topics have no alias field, so G15 also warns when a title equals another topic's slug | Closest meaningful clash |
| 7 | xref shape | `<alias>:<folder>/<slug>`; index repos publish `<base><folder>/<slug>.md`, manifest repos `<base>data/<folder>/<slug>.json` | Matches dsa-library and library-data layouts |
| 8 | Same-day `related` pair | Only a pair stored in both files is rejected (G7) | The checker cannot know which file is newer (dsa-library decision 12) |
| 9 | G17 base | Compares with `HEAD` locally; CI sets `GATE_BASE_REF` (push: previous commit, PR: base branch). No history or a new file means nothing to compare, so no error. Date order is always checked | A hook runs before the commit exists; CI runs after |
| 10 | G13 headings | Only `##` headings outside code fences count; `###` follow-ups stay inside their section. Revision-sheet length counts lines after trimming blank ends, follow-ups included | Spec allows dated follow-ups inside sections |
| 11 | Syllabus item labels | One item per phrase of the official text; ids are slugs of the label. CS Engineering Mathematics items are prefixed with their sub-heading (for example `linear-algebra-system-of-linear-equations`) | The official text lists them under four sub-headings of one section |
| 12 | `coverage.json` shape | `papers.<paper>.subjects[]` in syllabus order, each with `syllabus_items[]` (`id, text, covered_by, best_status, all`). `items` is the *count* (spec) so the list is `syllabus_items`. Public numbers at top level, private under `all` | Spec lists `items` as a count; order matters for display |
| 13 | `best_status` | Highest of `learning < revised < exam-ready` among covering topics; `none` if uncovered. Covered = any topic; exam-ready = status `exam-ready` | Spec does not define them |
| 14 | `question_stats.accuracy` | Share of attempted questions whose latest attempt is `right` (4 places); `null` if none attempted | Spec does not define it |
| 15 | Question title in `search.json` | Title is the slug; summary is the stem cut to 160 characters; papers come from the linked topics | Questions have no title |
| 16 | Seed syllabus mapping | `gaussian-elimination` lists the DA item and the CS item "system of linear equations"; `system-of-linear-equations` lists only the DA item. This avoids a permanent G14 warning | CS has no separate Gaussian-elimination item |
| 17 | Seed questions | Two generated questions (one MCQ, one NAT). No PYQs: the official papers could not be verified in this build | Spec: add PYQs only if verified |
| 18 | `notify.yml` | Not created | The spec's layout lists only `validate.yml` |
| 19 | Slug date, redirects | Redirect checks reuse rule G2; there is no separate redirect rule in G1-G22 | Spec has no redirect rule |
| 20 | Template kinds | `--new` kinds: `topic`, `question-mcq`, `question-msq`, `question-nat` | Matches the template files |
| 21 | Local setup | `.venv` and `.tools/bin/gitleaks` per machine (both gitignored); hook uses them | Same as dsa-library 21 and 34 |
| 22 | Versions | Python 3.14 locally, 3.12 in CI; PyYAML 6.0.2, jsonschema 4.23.0, pytest 8.3.4 | Same as dsa-library 33 |

## Directory-size rule (max 9 files per directory)

Code obeys it: `ci/gate_lib/` has 9 files, `ci/gate_lib/checks/` 9, `tests/` 6; fixtures are grouped by family
(`structure/`, `links/`, `content/`, `policy/`, `valid/`). Broken knowingly (spec layout outranks a readability rule):
the repo root, `topics/`, `questions/` (one file per item, unbounded by design) and `config/syllabus/` stays small.
If `topics/` or `questions/` pass about 500 files, revisit.
