# Authoring

New content only creates files; old files change only to add `updated`, a dated follow-up, or an attempt.

1. Scaffold: `python ci/sync_index.py --new topic <slug>` (or `question-mcq|msq|nat <slug>`).
2. Fill every `TODO`; the scaffold deliberately fails G13 until you do.
3. Find syllabus refs in `config/syllabus/<paper>.json` (`<paper>:<subject-id>/<item-id>`).
4. Link, never re-explain: `prerequisites`, `related`, `xrefs`.
5. Commit. The hook validates, regenerates `api/v1`, and stages it.

## Questions

- Generated: slug `gen-<topic-slug>-<nnn>`, `origin: generated`.
- PYQ: only with a verified official `source_url`; slug `gate-<year>-<paper>-s<session>-q<nn>`.
- Log a practice attempt: `python ci/sync_index.py --attempt <slug> wrong trap` (reasons: concept, calculation, trap, time, misread).
  Old attempts are never edited (G17).

## Syllabus changes

A new exam year: move the old file to `config/syllabus/archive/<paper>-<year>.json`, add the new one. Topics whose refs vanish fail G9.
