# Interview notes

The architecture separates ingestion, identity resolution, temporal reconstruction, policy and planning because each has different failure modes. A deterministic offline engine makes provenance inspectable and avoids paying for model calls on already structured facts. Runtime model calls, tokens and inference cost are all zero. Development used Codex; that usage is separate and not measured as runtime usage.

Identity resolution uses the supplied stable user ID and normalized exact current/historical email, phone and hash values. Audit changes recover old identifiers and reverse future changes before cutoff. Similar names, substrings and numeric suffixes never establish identity. An ambiguous reused email aborts rather than merging customers.

The in-memory graph consists of identifier/resource indexes, timestamped observation timelines and activity relationships. It is designed for forensic lookup, not visualization. Trace correlation connects a started lookup's identifier to a later result line in the same artifact. JSON paths, SQL tables, PDF pages and OCR lines remain attached to the parent evidence ID.

Both capture time and observation time must precede the audit. Newer primary readbacks update primary state, while named failover/regional/reporting replicas retain separate timelines. A later live read after an earlier absent result detects recreation. Activity records show sync/restore context but SUCCESS is never promoted to a proven state change.

Rules load from deletion_rules.csv. Security and legal records are retained and verified. Backups are retained with restore blocking. Tombstones permit stable internal references while email hashes and other direct identifiers must be removed. Synthetic tests exercise all of these distinctions, including the tombstone hash edge case.

The planner follows exact operation order from the statement, placing data-flow disabling and restore blocking before record mutations. The separate validator checks emitted assertions, citations, timestamps and complete finding-to-remediation-to-verification relationships.

Evaluation uses public sample answers only in a separate evaluator, after prediction. Final measured sample metrics: status 32/32, step precision 100%, recall 158/193 (81.87%), F1 90.03%, exact arrays 9/32. Positional field accuracy is lower because omitted steps shift alignment. Twenty-four independent synthetic/regression tests passed in the measured run. Hidden-set accuracy is unknown.

The main weakness is incomplete attribution of already absent or anonymized resources. Some reference evidence is unavailable before the cutoff or lacks a visible subject association. We document those failures rather than creating IDs or copying expected steps. Evidence-empty authorized cases use a forced COMPLETE/[] fallback because the schema lacks UNKNOWN; this must not be represented as proof of successful deletion. OCR layout ambiguity and unsupported conditional policy cases are further limitations.

Gemini was not evaluated. The deterministic baseline exposed linkage and temporal gaps; there is no measured evidence that an LLM would resolve them without inventing facts. Technical strengths are trace-aware extraction, explicit dual timestamp filtering, independent replica state, and provenance validation; the low exact-plan recall remains an openly measured weakness.
