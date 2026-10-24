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
