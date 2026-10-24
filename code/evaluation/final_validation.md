# Final validation

- Automated regression suite: 24 passed (last run 0.34 seconds).
- Public sample: 32/32 statuses; 158/193 exact steps; 9/32 exact ordered arrays.
- Full output: 518 rows; exact three-column header; sorted unique case IDs; all JSON parsed.
- Full output structural/provenance validator passed; all 2,673 emitted steps checked.
- Two successive executions, including execution from outside the checkout, produced byte-identical output.csv.
- output.csv SHA-256: `2a249bda29b463204297d14be73eb706f4918cc0f3e984c3d0f5c7008f7b4be4`.
- Official dataset is unchanged relative to upstream/main.
- Full-run status distribution: {'INCOMPLETE': 351, 'COMPLETE': 157, 'NOT_APPLICABLE': 10}.
- Runtime usage is in usage_report.md; inference calls/tokens/cost are zero.
- Four evidence-empty authorized cases remain documented in uncertainty_report.md. Structural validation does not certify semantic completeness or hidden-set accuracy.
- Source-only packaging uses an allowlist and verifies required reports, archive integrity and absence of dataset/cache/secret/nested archive paths.
