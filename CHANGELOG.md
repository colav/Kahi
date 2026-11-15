# Changelog

## 0.1.7 - 2026-11-15

- Add `primary_topic`, `topics` and `topic_text` to the empty project template.
  Topics are inferred in postcalculations from the title and the abstract;
  `topic_text` holds the text used when the project has no abstract.

## 0.1.6 - 2026-11-14

- Add `age` (default `None`) to the empty person template. Postcalculations
  computes it from `birthdate` and then clears the birth date, so the published
  profile carries the age but not the date.

## 0.1.5 - 2026-11-14

- Add `abstracts`, `primary_topic` and `topics` to the empty patent template,
  with the same shape as in works (Lens abstracts as inverted index, one entry
  per language; topics inferred in postcalculations).

## 0.1.4 - 2026-11-10

- Add `cited_by_api_url` to the empty work template (OpenAlex cited-by query
  URL rebuilt from the work id; the snapshot does not carry it).

## 0.1.3 - 2026-11-06

- Add `kahi.progress.ProgressLogger`, a shared progress reporter for plugins:
  uniform `[plugin:phase] START/progress/DONE` lines with totals, rate, ETA
  and outcome counts, emitted every 5% of the total (minimum 1000 records) or
  every 60 seconds; thread-safe, resumable (`initial`) and with names
  normalized to `[a-z0-9_:]`.
- Let snapshot plugins manage their own checkpoints: skip the workflow-log
  resume shortcut when `manages_checkpoints(config)` returns true.
- Add `campuses` to the empty affiliation template.
