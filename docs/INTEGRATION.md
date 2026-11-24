# Integration

Other sites read only the published JSON; nothing is built together, so a broken repo never breaks another site.

- `https://fmfalgun.github.io/gate-library/api/v1/index.json`: items, links, `url` of each `.md` / `.yaml`.
- `.../coverage.json`: per paper, `subjects[]` (syllabus order), each with `syllabus_items[]`. A subject or paper carries
  `items, covered, exam_ready, percent_covered, percent_exam_ready` for public topics, and the same numbers under `all`.
- `.../search.json`: `{slug, kind, title, summary, papers, tags, status}`.

Rules for consumers:

1. Show only items whose `show_on` includes your site key (`portfolio` for the portfolio).
2. Fetch a topic's body from its `url`; the index holds metadata only.
3. If a fetch fails, show a short "unavailable" message and keep the rest of your site working.
4. `xrefs` carry a computed `url`: `dsa-library:*` points at that repo's published `.md`; `library-data:tools/*` at its JSON record.

The portfolio's GATE page lives in the `library` repo's `pages/` and is reachable from the portfolio's LIBRARY page.
