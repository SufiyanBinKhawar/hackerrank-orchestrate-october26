# Deterministic deletion auditor

Python 3.11+ offline engine for the participant-visible Ghost Data Still Exists dataset. There are no runtime model calls, API keys, graph servers, or network requests.

## Setup and commands

From the checkout root (or the extracted archive root, with the official dataset placed alongside `code/`):

```sh
python -m pip install -r code/requirements.txt
python code/main.py
python code/main.py --sample
python code/main.py --evaluate
python code/main.py --validate output.csv
python code/main.py --sample --validate sample_predictions.csv
python code/main.py --inspect case_33
python code/main.py --sample --inspect case_17
python -m pytest code/tests -q
python code/package_submission.py
```

Install **Tesseract OCR 5.x with English language data** separately: Windows `winget install --id UB-Mannheim.TesseractOCR --exact`, macOS `brew install tesseract`, or Debian/Ubuntu `apt install tesseract-ocr`. Put it on PATH or set `TESSERACT_CMD` to the executable. The standard Windows Program Files location is also detected. Missing OCR or empty extraction is a fatal error; images are never silently ignored. PDF text uses PyMuPDF, and images use Pillow/pytesseract. Requirements pin PyMuPDF below 2 to avoid unrelated ML/layout dependencies.

All default paths, including relative `--output` and `--validate` paths, resolve from the source repository root, not the shell working directory. The default run writes 518 sorted rows to root `output.csv`. `--evaluate` reads public sample answers only after predictions have been produced. `--inspect` emits JSON to stdout; operational diagnostics go to stderr. Locally installed `.deps/` is supported but never packaged. Tests need writable temporary storage; use `--basetemp=.cache/tests` if the OS temporary directory is restricted.

## Architecture and decisions

- `audit/orchestrator.py` loads shared indexes once, classifies each request, resolves identities, reconstructs state, plans steps and validates output.
- `request_intent.py` uses Unicode-aware multilingual authorization and negation rules, independently of workflow status.
- `identity_resolver.py` recovers current/historical email, phone and hash values. Exact normalized matches resolve the supplied stable user ID; ambiguous identities fail visibly. Names never merge subjects.
- `evidence_ingestion.py` contains format-specific JSON, SQLite, log, PDF and OCR adapters. JSON retains record paths; SQL retains table/replica identity; logs join trace starts/results inside each artifact; documents retain page or OCR-line locations.
- `knowledge_graph.py` indexes identifier-to-resource edges and per-resource observations. Evidence IDs and both timestamps stay attached. Activity catalog links can connect resources; successful mutation claims cannot establish their state.
- `temporal_engine.py` filters both capture and observation time against `audit_at`, then selects the latest observation for each independent copy. A newer primary absence cannot clear a surviving replica. Export subsets are not universal absence proofs.
- `dependency_analyzer.py` selects subject-grounded sync/restore/index events for inspection. Actual active/disabled control states come from evidence observations.
- `policy_engine.py` loads supplied rules dynamically. Tombstones retain user references while requiring direct identifiers and hashes to be removed. Retained security/legal records are verified. Backups receive restore blocking, never deletion merely because they remain.
- `remediation_planner.py` emits allowed operations in the statement's exact order, then system/resource order. This places flow disabling and restore blocking before record changes. Every selected record receives its final-state verification.
- `output_validator.py` independently checks schema, coverage, order, duplicates, citations, cutoffs, asserted states and matching finding/remediation/verification relationships.
- `evaluation/main.py` computes status, multiset step, positional field and ordered-array metrics, with per-case missing/extra steps and evidence-gap diagnostics.

No resource ID is derived from a case number or user-number suffix. No golden output is imported by the production auditor. Findings and COMPLETE verifications cite parent manifest IDs; incomplete future actions use empty citations. Multiple readings of one file retain their separate timestamps and locations.

## Conflicts, failures and uncertainty

Conflicts within one copy use observation time, capture time, then stable evidence/location order. Conflicts across replicas preserve a surviving prohibited copy. Explicit readbacks establish absence; a workflow's `SUCCESS` alone cannot. Missing required evidence formats, ambiguous subjects, unknown policies, expired retention without a fallback rule, and malformed output abort visibly rather than emitting a partially written CSV.

The output contract lacks UNKNOWN. The engine currently uses COMPLETE with no asserted checks for an authorized case without attributable state evidence, while recording the gap in `evaluation/uncertainty_report.md`. This fallback does **not** prove completion. Missing historical links for anonymized/absent resources also limit verification recall. Read the evaluation report before relying on predictions. The validator checks defensibility of emitted assertions, not completeness against unavailable truth.

Measured public sample: 32/32 statuses; 158/193 exact steps; precision 100%; recall 81.87%; F1 90.03%; 9/32 exact ordered arrays. Hidden accuracy is unknown. See generated reports for final runtime and regression measurements. OCR results are cached by content/configuration hash under `.cache`; other evidence is indexed once per invocation. No Gemini extraction experiment was performed.

## Packaging

`python code/package_submission.py` writes root `code.zip` with root README and the `code/` tree (including this README, requirements, tests, and Markdown reports). It excludes the dataset, transcript, predictions, environments, caches, binary files, secrets, and nested archives. Submit `code.zip`, root `output.csv`, and root `log.txt` separately. The official root README and AGENTS instructions remain in the checkout.
