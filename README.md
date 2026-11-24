# gate-library

GATE preparation material stored as validated files, published as a generated JSON API.

- **Topics** (`topics/<slug>.md`): teaching notes, formulas, traps and a revision sheet, shared across papers.
- **Questions** (`questions/<slug>.yaml`): past-year and generated practice questions with an attempt log.
- **Syllabus** (`config/syllabus/<paper>.json`): the official syllabus as data (`da`, `cs`, `ga` for GATE 2027).

Every link is stored once, by its owner; reverse links, PYQ years, question counts and syllabus coverage
are computed. Nothing generated is edited by hand.

## Published API

Base: <https://fmfalgun.github.io/gate-library/api/v1/>

| File | Holds |
| --- | --- |
| `index.json` | every topic and question with links in both directions, `questions`, `pyq_years`, `question_stats`, `papers`, `diagnostics` |
| `coverage.json` | per paper, subject and syllabus item: which topics cover it and the best status; public percentages and, under `all`, private ones |
| `search.json` | slim list for search boxes |
| `schema/` | the JSON Schemas |

Topic and question files are served from the same site (`url` in the index).

## Working in this repo

```
python ci/sync_index.py                       validate, then regenerate api/v1 and the rule list below
python ci/sync_index.py --check               validate and fail if generated files are stale (G20)
python ci/sync_index.py --online              also check xrefs against other repos (warnings only)
python ci/sync_index.py --explain SLUG        links and warnings for one item
python ci/sync_index.py --new KIND SLUG       scaffold a file (topic, question-mcq, question-msq, question-nat)
python ci/sync_index.py --stats               coverage and accuracy per paper
python ci/sync_index.py --attempt SLUG right|wrong|skipped [reason]
```

Setup: `python -m venv .venv && .venv/bin/pip install -r requirements.txt && git config core.hooksPath ci/hooks`.
The pre-commit hook scans for secrets (gitleaks), checks scripts for force commands, validates and regenerates
`api/v1`. Never bypass it. Start with `docs/AUTHORING.md`; every design choice is in `docs/DECISIONS.md`.

## Rules

Errors block the commit; warnings are printed and recorded in `diagnostics.warnings`.

<!-- rules:start -->
| Rule | Severity | Check |
| --- | --- | --- |
| G1 | error | Only `topics/*.md` and `questions/*.yaml` in the content folders; filename = slug; slug format and patterns |
| G2 | error | Slugs are unique across kinds and are not a redirect key; redirects are well formed |
| G3 | error | Front matter / YAML passes its JSON Schema; unknown keys only with an `x_` prefix |
| G4 | error | Only the link fields of the relation table are used, each on its own kind |
| G5 | error | Link targets exist and are the right kind (resolving through a redirect is a warning) |
| G6 | error | No cycles in `prerequisites`; no self-links |
| G7 | error | A `related` pair is not stored in both files |
| G8 | error | No duplicate entries in any list |
| G9 | error | Syllabus refs exist in the current `config/syllabus/*.json` |
| G10 | error | Syllabus files are valid; item IDs are unique slugs within a subject; every `source_url` is set |
| G11 | error | PYQ identity `(year, paper, session, number)` is unique and matches the slug; PYQs have `source_url` |
| G12 | error | Answer is consistent with type: mcq answer in options; msq a non-empty subset; nat `min <= max` with no options |
| G13 | error | Topic body has the exact section headings in order; Revision sheet at most 40 lines; no `TODO` left |
| G14 | warning | Two topics list the same syllabus item: possible duplicate topic |
| G15 | warning | Topic title similarity >= 0.85, or a title that equals another topic's slug |
| G16 | warning | Two generated questions on one topic with stem similarity >= 0.90 |
| G17 | error | Old `attempts` entries are never changed or removed (compared with `HEAD`, or `GATE_BASE_REF` in CI); new entries go last with non-decreasing dates |
| G18 | error | `show_on` and `tags` values come from config |
| G19 | error | Dates are valid and not in the future; `created <= updated` |
| G20 | error | `api/v1/` and the README rule list are up to date (`--check`) |
| G21 | error offline / warning online | `xrefs` format and alias (offline); target exists (online, CI only) |
| G22 | error | No secrets (gitleaks + Python scan); no content file over 1 MB |
<!-- rules:end -->

## Known limits

- Directory-size rule (max 9 files per directory) is broken knowingly in `topics/`, `questions/` and the repo root; see `docs/DECISIONS.md`.
- Topic bodies are not in `index.json`; consumers fetch each topic's `.md`.
- `attempts` (your private practice log) is published because the spec puts it in the index. Hide a question with `show_on: []`.
