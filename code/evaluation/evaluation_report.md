# Public sample evaluation

Measured metrics:
```
{
  "cases": 32,
  "status_accuracy": 1.0,
  "exact_step_arrays": 0.28125,
  "sequence_without_evidence": 0.28125,
  "precision": 1.0,
  "recall": 0.8186528497409327,
  "f1": 0.9002849002849003,
  "field_accuracy": {
    "phase": 0.8186528497409327,
    "system_id": 0.6010362694300518,
    "resource_id": 0.6010362694300518,
    "operation": 0.6580310880829016,
    "state": 0.6580310880829016,
    "evidence_id": 0.8186528497409327,
    "step_no": 0.8186528497409327
  }
}
```

Step precision/recall use multiset equality across all fields except step_no. Sequence metrics preserve array order. Field accuracy uses positional alignment, with missing/extra positions counted as incorrect. Sample answers are read only by this evaluator and never used to change predictions.

Failure classification:
```
{
  "No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.": 17,
  "Resource has a pre-cutoff state observation but no grounded pre-cutoff subject link.": 12,
  "All parsed resource observations are after the audit cutoff by capture or observation time.": 6
}
```

## Regression scenarios and measured development changes

The independent fixture suite contains 24 passing tests (pytest, 0.35 seconds in the recorded post-fix run). Fixtures are generated in pytest temporary directories, never in the official dataset. The scenarios and expected outcomes are:

| Scenario | Expected outcome | Observed |
|---|---|---|
| Deleted account followed by a later live record and active connector | INCOMPLETE; disable connector before deleting record | Pass |
| Identical display names and similar email addresses | Only exact subject's account included | Pass |
| Tombstone with stable user reference and null direct identifiers | COMPLETE; redaction verification only | Pass |
| Tombstone still carrying an email hash | INCOMPLETE; redact, preserve user reference | Pass |
| Security retention plus active legal hold | Verify both retained records; do not delete | Pass |
| Unsafe backup restore access | Report risk, block restore, verify blocked | Pass |
| Pre-audit event in an artifact captured after audit | Ignore it for earlier state | Pass |
| Old live failover replica and newer absent primary | Preserve failover violation | Pass |
| Multilingual non-deletion request | NOT_APPLICABLE, empty steps | Pass |
| Correlated lookup start and result lines | Recover subject link and detect remaining record | Pass |
| Reused exact email with two candidate subjects | Fail visibly as ambiguous | Pass |
| Expired retention without a supplied fallback policy | Fail visibly instead of inventing deletion rule | Pass |
| Old absent account alongside a different current account | Exclude old completed account from the new request | Pass |
| Invalid citation, reordered steps, and false asserted state | Independent validator rejects mutations | Pass |

Nine parametrized language tests include Korean authorization and negation, Japanese negation, Spanish negation, French authorization, Portuguese negation, English account-close negation, marketing-only language, and verification of prior deletion.

Baseline measured sample metrics: status 32/32, exact arrays 8/32, precision 99.3711%, recall 81.8653%, F1 89.7727%. After a general request-window scope rule excluded an already absent older account when a different current account was evidenced, precision rose to 100%, exact arrays to 9/32, and F1 to 90.0285%. Status and recall were unchanged. No case-ID or specific email branch was introduced.

Full-run inspection also found that NFKD decomposes Korean syllables: matching native-script intent against the decomposed Latin-normalization string missed Korean authorization. Native-script checks now use NFKC text, with accent-stripped text only for Latin language matching. Two English negation forms were added. These improvements are exercised by synthetic tests; they do not improve the public sample metric because that sample lacks those non-deletion/Korean examples.

An early full run exposed a broad SQL absence inference. Export subsets cannot prove all other resources absent. Absence from a table is now usable only when the same artifact establishes the resource in another table. Primary readbacks share the primary timeline; separately named replicas retain their independent timelines.

## Failure analysis and remaining limitations

The sample has 193 steps. The revised engine matches 158, with 35 missing and no extra steps. Missing fields shift positional alignment, which explains lower positional field scores despite perfect precision of the emitted steps. Detailed per-case differences and automatically classified extraction/linkage/cutoff gaps follow below.

Some reference checks cannot currently be grounded from pre-cutoff participant evidence. For example, analytics_9406 has a pre-cutoff anonymized readback whose identity fields and lookup key are all null; no prior attributed observation was found. For audit_record_4902, the parsed readback is in an artifact captured September 18, after the September 16 audit. Some absent account IDs occur in activity claims but have no visible subject association. These are concrete limitations of the permitted evidence or current extraction, not proof that every reference is erroneous. We neither infer identities from numeric suffixes nor use the reference plans to fill these gaps.

The three output labels cannot express uncertainty. An evidence-empty authorized request receives COMPLETE with [] as a forced fallback, recorded in uncertainty_report.md and inspection traces. This is not evidence of successful deletion and is a material submission weakness. Some nonempty COMPLETE plans may also omit unlinked anonymized or absent resources. Hidden-set accuracy has not been measured.

OCR is local and deterministic for a fixed executable/version, but errors and layout ambiguity remain. Only co-located exact resource/subject identifiers yield screenshot observations. A visible backup alone does not prove restore permission, and a visible connector alone does not prove active delivery. Ambiguous image fields are reported instead of guessed. Documents lacking canonical resource IDs supply context without invented output references.

Policy category coverage follows the supplied categories; unknown or expired conditional-retention cases fail visibly. Conditions expressed only in free text, shared attachment ownership beyond explicit record types, and unusual legal-hold states need further adapters for new corpora. Workflow claims provide trace/dependency context but are never promoted to successful state changes. No Gemini experiment was performed: no additional model or network dependency is enabled.

The first pytest attempt failed because Windows sandbox permissions denied pytest's own temporary directories. The same tests passed through the approved execution path; those environment errors are not counted as test passes.


### case_01

Status: predicted COMPLETE; expected COMPLETE.

Missing steps:
```
{"evidence_id": "evidence_54", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_001", "state": "ABSENT", "system_id": "account_service"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_001: No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.

### case_02

Status: predicted COMPLETE; expected COMPLETE.

Missing steps:
```
{"evidence_id": "evidence_54", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_002", "state": "ABSENT", "system_id": "account_service"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_002: No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.

### case_03

Status: predicted COMPLETE; expected COMPLETE.

Missing steps:
```
{"evidence_id": "evidence_94", "operation": "VERIFY_RECORD_ANONYMIZED", "phase": "VERIFICATION", "resource_id": "analytics_9406", "state": "ANONYMIZED", "system_id": "analytics_platform"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- analytics_9406: Resource has a pre-cutoff state observation but no grounded pre-cutoff subject link.

### case_04

Status: predicted COMPLETE; expected COMPLETE.

Missing steps:
```
{"evidence_id": "evidence_54", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_004", "state": "ABSENT", "system_id": "account_service"}
{"evidence_id": "evidence_56", "operation": "VERIFY_RECORD_ANONYMIZED", "phase": "VERIFICATION", "resource_id": "analytics_901", "state": "ANONYMIZED", "system_id": "analytics_platform"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_004: No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.
- analytics_901: Resource has a pre-cutoff state observation but no grounded pre-cutoff subject link.

### case_06

Status: predicted INCOMPLETE; expected INCOMPLETE.

Missing steps:
```
{"evidence_id": "", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_006", "state": "ABSENT", "system_id": "account_service"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_006: No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.

### case_07

Status: predicted INCOMPLETE; expected INCOMPLETE.

Missing steps:
```
{"evidence_id": "", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_007", "state": "ABSENT", "system_id": "account_service"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_007: No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.

### case_08

Status: predicted INCOMPLETE; expected INCOMPLETE.

Missing steps:
```
{"evidence_id": "", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_008", "state": "ABSENT", "system_id": "account_service"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_008: No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.

### case_09

Status: predicted INCOMPLETE; expected INCOMPLETE.

Missing steps:
```
{"evidence_id": "", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_3960", "state": "ABSENT", "system_id": "account_service"}
{"evidence_id": "", "operation": "VERIFY_RECORD_PRESENT", "phase": "VERIFICATION", "resource_id": "audit_record_4902", "state": "PRESENT", "system_id": "security_service"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_3960: All parsed resource observations are after the audit cutoff by capture or observation time.
- audit_record_4902: All parsed resource observations are after the audit cutoff by capture or observation time.

### case_10

Status: predicted INCOMPLETE; expected INCOMPLETE.

Missing steps:
```
{"evidence_id": "", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_010", "state": "ABSENT", "system_id": "account_service"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_010: No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.

### case_18

Status: predicted INCOMPLETE; expected INCOMPLETE.

Missing steps:
```
{"evidence_id": "", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_5521", "state": "ABSENT", "system_id": "account_service"}
{"evidence_id": "", "operation": "VERIFY_RECORD_PRESENT", "phase": "VERIFICATION", "resource_id": "audit_record_6645", "state": "PRESENT", "system_id": "security_service"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_5521: No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.
- audit_record_6645: No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.

### case_20

Status: predicted INCOMPLETE; expected INCOMPLETE.

Missing steps:
```
{"evidence_id": "", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_5037", "state": "ABSENT", "system_id": "account_service"}
{"evidence_id": "", "operation": "VERIFY_RECORD_PRESENT", "phase": "VERIFICATION", "resource_id": "audit_record_5569", "state": "PRESENT", "system_id": "security_service"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_5037: No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.
- audit_record_5569: No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.

### case_21

Status: predicted COMPLETE; expected COMPLETE.

Missing steps:
```
{"evidence_id": "evidence_92", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_6440", "state": "ABSENT", "system_id": "account_service"}
{"evidence_id": "evidence_92", "operation": "VERIFY_RECORD_ANONYMIZED", "phase": "VERIFICATION", "resource_id": "analytics_5335", "state": "ANONYMIZED", "system_id": "analytics_platform"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_6440: Resource has a pre-cutoff state observation but no grounded pre-cutoff subject link.
- analytics_5335: Resource has a pre-cutoff state observation but no grounded pre-cutoff subject link.

### case_22

Status: predicted INCOMPLETE; expected INCOMPLETE.

Missing steps:
```
{"evidence_id": "", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_4990", "state": "ABSENT", "system_id": "account_service"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_4990: No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.

### case_23

Status: predicted INCOMPLETE; expected INCOMPLETE.

Missing steps:
```
{"evidence_id": "", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_410", "state": "ABSENT", "system_id": "account_service"}
{"evidence_id": "", "operation": "VERIFY_RECORD_PRESENT", "phase": "VERIFICATION", "resource_id": "audit_record_4128", "state": "PRESENT", "system_id": "security_service"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_410: No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.
- audit_record_4128: All parsed resource observations are after the audit cutoff by capture or observation time.

### case_24

Status: predicted INCOMPLETE; expected INCOMPLETE.

Missing steps:
```
{"evidence_id": "", "operation": "VERIFY_RECORD_PRESENT", "phase": "VERIFICATION", "resource_id": "audit_record_7095", "state": "PRESENT", "system_id": "security_service"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- audit_record_7095: All parsed resource observations are after the audit cutoff by capture or observation time.

### case_25

Status: predicted COMPLETE; expected COMPLETE.

Missing steps:
```
{"evidence_id": "evidence_92", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_3136", "state": "ABSENT", "system_id": "account_service"}
{"evidence_id": "evidence_92", "operation": "VERIFY_RECORD_ANONYMIZED", "phase": "VERIFICATION", "resource_id": "analytics_1895", "state": "ANONYMIZED", "system_id": "analytics_platform"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_3136: Resource has a pre-cutoff state observation but no grounded pre-cutoff subject link.
- analytics_1895: Resource has a pre-cutoff state observation but no grounded pre-cutoff subject link.

### case_26

Status: predicted COMPLETE; expected COMPLETE.

Missing steps:
```
{"evidence_id": "evidence_92", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_5684", "state": "ABSENT", "system_id": "account_service"}
{"evidence_id": "evidence_92", "operation": "VERIFY_RECORD_ANONYMIZED", "phase": "VERIFICATION", "resource_id": "analytics_4566", "state": "ANONYMIZED", "system_id": "analytics_platform"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_5684: Resource has a pre-cutoff state observation but no grounded pre-cutoff subject link.
- analytics_4566: Resource has a pre-cutoff state observation but no grounded pre-cutoff subject link.

### case_27

Status: predicted COMPLETE; expected COMPLETE.

Missing steps:
```
{"evidence_id": "evidence_92", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_3866", "state": "ABSENT", "system_id": "account_service"}
{"evidence_id": "evidence_92", "operation": "VERIFY_RECORD_ANONYMIZED", "phase": "VERIFICATION", "resource_id": "analytics_4574", "state": "ANONYMIZED", "system_id": "analytics_platform"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_3866: Resource has a pre-cutoff state observation but no grounded pre-cutoff subject link.
- analytics_4574: Resource has a pre-cutoff state observation but no grounded pre-cutoff subject link.

### case_28

Status: predicted COMPLETE; expected COMPLETE.

Missing steps:
```
{"evidence_id": "evidence_92", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_5482", "state": "ABSENT", "system_id": "account_service"}
{"evidence_id": "evidence_92", "operation": "VERIFY_RECORD_ANONYMIZED", "phase": "VERIFICATION", "resource_id": "analytics_6077", "state": "ANONYMIZED", "system_id": "analytics_platform"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_5482: Resource has a pre-cutoff state observation but no grounded pre-cutoff subject link.
- analytics_6077: Resource has a pre-cutoff state observation but no grounded pre-cutoff subject link.

### case_29

Status: predicted INCOMPLETE; expected INCOMPLETE.

Missing steps:
```
{"evidence_id": "", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_7012", "state": "ABSENT", "system_id": "account_service"}
{"evidence_id": "", "operation": "VERIFY_RECORD_PRESENT", "phase": "VERIFICATION", "resource_id": "audit_record_3954", "state": "PRESENT", "system_id": "security_service"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_7012: No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.
- audit_record_3954: All parsed resource observations are after the audit cutoff by capture or observation time.

### case_30

Status: predicted INCOMPLETE; expected INCOMPLETE.

Missing steps:
```
{"evidence_id": "", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_4163", "state": "ABSENT", "system_id": "account_service"}
{"evidence_id": "", "operation": "VERIFY_RECORD_PRESENT", "phase": "VERIFICATION", "resource_id": "audit_record_1707", "state": "PRESENT", "system_id": "security_service"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_4163: No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.
- audit_record_1707: All parsed resource observations are after the audit cutoff by capture or observation time.

### case_31

Status: predicted COMPLETE; expected COMPLETE.

Missing steps:
```
{"evidence_id": "evidence_51", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_4857", "state": "ABSENT", "system_id": "account_service"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_4857: No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.

### case_32

Status: predicted INCOMPLETE; expected INCOMPLETE.

Missing steps:
```
{"evidence_id": "", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_8858", "state": "ABSENT", "system_id": "account_service"}
```
Extra steps:
```

```
Ordered match without evidence IDs: False.

- account_8858: No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.
