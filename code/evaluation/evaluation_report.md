# Public sample evaluation

Measured metrics:
```
{
  "cases": 32,
  "status_accuracy": 1.0,
  "exact_step_arrays": 0.25,
  "sequence_without_evidence": 0.25,
  "precision": 0.9937106918238994,
  "recall": 0.8186528497409327,
  "f1": 0.8977272727272727,
  "field_accuracy": {
    "phase": 0.8144329896907216,
    "system_id": 0.5876288659793815,
    "resource_id": 0.5876288659793815,
    "operation": 0.6443298969072165,
    "state": 0.6443298969072165,
    "evidence_id": 0.8144329896907216,
    "step_no": 0.8144329896907216
  }
}
```

Step precision/recall use multiset equality across all fields except step_no. Sequence metrics preserve array order. Field accuracy uses positional alignment, with missing/extra positions counted as incorrect. Sample answers are read only by this evaluator and never used to change predictions.

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

### case_17

Status: predicted INCOMPLETE; expected INCOMPLETE.

Missing steps:
```

```
Extra steps:
```
{"evidence_id": "", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_6523", "state": "ABSENT", "system_id": "account_service"}
```
Ordered match without evidence IDs: False.

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
