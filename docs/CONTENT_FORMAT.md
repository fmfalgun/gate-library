# Content format

Source of truth: the JSON Schemas in `schema/` (also published under `api/v1/schema/`).

## Slugs

`^[a-z0-9]+(-[a-z0-9]+)*$`, at most 80 characters, unique across topics and questions, never changed.
A rename or merge goes in `config/redirects.json` (`{"old": "new"}`).

| Kind | Pattern | Example |
| --- | --- | --- |
| topic | `<name>` | `gaussian-elimination` |
| PYQ | `gate-<year>-<paper>-s<session>-q<nn>` | `gate-2024-cs-s2-q23` |
| generated question | `gen-<topic-slug>-<nnn>` | `gen-gaussian-elimination-001` |

## Topic (`topics/<slug>.md`)

YAML front matter, then Markdown with `$...$` / `$$...$$` math (KaTeX). Fields: `slug`, `kind: topic`, `title` (<=120),
`summary` (<=200), `syllabus` (>=1 ref), `prerequisites`, `related`, `xrefs`, `sources` (`{label, url}`), `status`
(`learning|revised|exam-ready`), `confidence` (1-5), `tags`, `show_on` (default `["portfolio"]`), `created`, `updated`.

Body headings, exactly and in this order (`##`): Summary, Intuition, Definitions and theorems, Formulas, Worked examples,
Shortcuts, Traps, Revision sheet, Connections, Sources. The Revision sheet has at most 40 lines. Dated follow-ups are
`### YYYY-MM-DD - <what>` inside the section they extend. `TODO` must not remain.

## Question (`questions/<slug>.yaml`)

`slug`, `kind: question`, `origin` (`pyq|generated`), `exam` and `source_url` (PYQ only), `type` (`mcq|msq|nat`), `marks` (1|2),
`topics`, `stem`, `options` (A-D; not for nat), `answer` (`"B"` | `["A","C"]` | `{min, max}`), `solution`, `fastest_method`,
`trap`, `difficulty`, `attempts` (append-only `{date, result, reason?}`), `show_on`, `created`, `updated`.
PYQ stems keep the official wording; if it cannot be verified, paraphrase and add `x_paraphrased: true`.

## Syllabus (`config/syllabus/<paper>.json`)

Reference format: `<paper>:<subject-id>/<item-id>`, e.g. `da:linear-algebra/gaussian-elimination`.
Old years go to `config/syllabus/archive/<paper>-<year>.json` and are not validated against.

## Extension keys

Unknown keys are allowed only with an `x_` prefix; they are copied to `extra` in the index.
