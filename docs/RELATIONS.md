# Relations

Links are stored once, in the file of the owner. Reverse links are computed into `api/v1/index.json`.

| Field | Owner | Points to | Reverse name in index |
| --- | --- | --- | --- |
| `topics` | question | topic | `questions` |
| `prerequisites` | topic | topic | `required_by` |
| `related` | topic | topic | `related` (both sides) |
| `syllabus` | topic | syllabus item | `covered_by` (in `coverage.json`) |
| `xrefs` | topic | other repo | none; consumers join them |

- `related` is symmetric: store it only in the file created later; storing it in both fails G7.
- `prerequisites` must not form a cycle (G6). A topic must not re-explain another topic; it links to it.
- `xrefs` look like `dsa-library:concepts/<slug>`, `dsa-library:problems/<slug>`, `library-data:tools/<slug>`
  and use the aliases in `config/repos.json`. Algorithm internals live in dsa-library; network tools in library-data.
- Never write a reverse link by hand; it would be a second copy that can disagree with the first.
