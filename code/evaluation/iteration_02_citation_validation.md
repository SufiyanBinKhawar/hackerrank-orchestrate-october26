# Iteration 2: evidence citation validation

Baseline: `4a710e39880951b66931eacc25a7a7d9be9a95d7`. Scope: citation validation only.

## Confirmed defect

The problem statement permits file_id, activity_id and audit_id citations. AGENTS.md sections 6.3/6.6 require that citations establish the claimed state and be available at the audit cutoff. The original validator accepted all three prefixes syntactically, but then required every ID to exist in store.manifest. Consequently every real activity/audit ID failed as unknown before provenance could be assessed.

Inspection found 4,011 activity rows and 306 audit rows. Activity has activity_id/event_time/source_system/target_system/resource_id/event_type/reported_result/details. Audit history has audit_id/user_id/event_time/field_name/old_value/new_value; its observed field types are email, email_hash and phone. Identity history is attribution evidence, not a resource-state readback. Activity success is also not independent proof.

## Isolated change

Only output_validator.py changes production behavior. It reads actual activity/audit records once per validation, indexes each by its source-specific ID, and validates event_time rather than looking for a manifest capture time. File citations still require manifest membership, capture cutoff and their original observation/scope-state support.

All steps must refer to a resource grounded to the request subject using the existing identity/graph APIs. No identity or graph implementation was changed.

Event citations require independent file-backed observations of the same system/resource/state, available before audit_at and observed at or after the cited event. The corroborating file's manifest timestamp is checked independently as well.

- Activity: admit the supplied explicit CHECK_DATA_FLOW / CHECK_RESTORE_ACCESS readback semantics only, with matching target system, exact resource ID in the row and details, and no conflicting subject in details. Require independent ACTIVE-state corroboration. Mutation success, submitted checks, and unsupported event semantics fail closed.
- Audit: admit attribution of a remaining/exposed identifier only. The source audit user must match the resolved request subject, and its old/new email/hash/phone must appear in an independently observed PRESENT resource. Audit events cannot support absence, redaction or anonymization verification merely because an identifier changed.

These are conservative composite evidence checks: the event supplies a check/attribution fact; independent file evidence supplies the resource state. The predictor still emits file citations only. No activity/audit citation was introduced into production predictions, and no extraction, temporal reconstruction, dependency, OCR or planning logic changed.

## Tracked regression tests

Added code/tests/test_citation_validation.py: 22 test cases, including parametrizations. They cover valid existing file output, corroborated activity checks, audit attribution of an independently observed historical email, nonexistent IDs of each type, successful mutation claims, unconfirmed checks, future activity/audit/file evidence, wrong resource/system/subject, audit identifiers absent from the cited resource, attempts to use identity change as account-absence proof, missing state corroboration, and future corroborating captures.

Full tracked suite: **46 passed in 0.89 seconds**. An initial test fixture used a future email change with the new email as an earlier request identifier; corrected the fixture to use the old email, without changing identity resolution.

## Measured comparison

| Metric | Baseline | New |
|---|---:|---:|
| Status accuracy | 32/32 | 32/32 |
| Exact step arrays | 9/32 (28.125%) | 9/32 (28.125%) |
| Step precision | 100% | 100% |
| Step recall | 81.8652849741% | 81.8652849741% |
| F1 | 90.0284900285% | 90.0284900285% |
| Missing / extra steps | 35 / 0 | 35 / 0 |

Changed sample predictions: **0**, confirmed byte-for-byte against the preserved pre-change sample output. SHA-256: `44f915221dda30054c76d0a5067b68e08dbed4c824e8e8011989c7f3d5e1c9c1`. Existing sample and full outputs validate (32 and 518 rows). No observed status, state, citation or ordering regression. The public evaluator report is unchanged.

## Limits and stop condition

This fixes source lookup and safe citation admission; it does not recover missing predictions or introduce new event extractors. Unknown activity semantics remain rejected, and identity audits alone still cannot prove deletion. The pre-existing sample inaccuracies and evidence-empty fallback remain outside this iteration. Submission artifacts were not regenerated because prediction generation did not change. Stop after committing this targeted iteration.
