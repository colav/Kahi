# Changelog

## 0.1.3-alpha - 2026-11-06

- Add `kahi.progress.ProgressLogger`, a shared progress reporter for plugins:
  uniform `[plugin:phase] START/progress/DONE` lines with totals, rate, ETA
  and outcome counts, emitted every 5% of the total (minimum 1000 records) or
  every 60 seconds; thread-safe, resumable (`initial`) and with names
  normalized to `[a-z0-9_:]`.
- Let snapshot plugins manage their own checkpoints: skip the workflow-log
  resume shortcut when `manages_checkpoints(config)` returns true.
- Add `campuses` to the empty affiliation template.
