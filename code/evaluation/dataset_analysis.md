# Dataset reconnaissance

Inspected participant-facing files only. There are 518 official requests, 32 public sample requests, 850 identities, 306 identity changes, 4,011 activity events, 15 policy rules, and 94 manifest entries/artifacts: 28 JSON, 26 logs, 24 SQL, 11 PNG, 4 PDF, 1 text.

Request schema: case_id,email,requested_at,reported_status,reported_at,audit_at,request_text. Identity schema: user_id,name,email,phone,email_hash,updated_at. Audit schema: audit_id,user_id,event_time,field_name,old_value,new_value. Activity schema: activity_id,event_time,event_type,source_system,target_system,resource_id,reported_result,details. Manifest schema: file_id,file_path,origin,captured_at. Policies: rule_id,data_category,condition,required_action. CSV values are strings; JSON preserves nulls/booleans; SQLite stores integer booleans and nested record_json.

SQL has customer_data_primary and separate read/reporting/failover/regional replica tables (resource_id,origin_system,collection_name,record_json,updated_at). Other snapshots use typed customer_profiles, customer_search_documents, customer_analytics_profiles, support_records, customer_exports, connector_subscriptions, backup_restore_entries, security_audit_records, plus snapshot_scope. The small account replica snapshot contains separate primary and failover profile tables. Empty primary results do not prove absence on a replica.

JSON structures include snapshot bundles with nested captured_at/data_store/collection/records, service_exports keyed by system with profile lookups/search hits, and operational history records with recorded_at/system/record_type/result/lookup_value. Anonymized records retain resource_id while dropping identity fields; earlier evidence and catalog links are needed to attribute them. Explicit NOT_FOUND and HTTP 404 readbacks establish absence; lack of a match does not.

Logs contain key=value, pipe-separated, bracketed, JSON, syslog and escaped cloud-message formats. Identity keys may occur on a started event, with results on another line sharing a trace ID. Noise (cache misses, failed previews, DNS events) must not establish deletion state. Contact lookup is a secondary identifier even inside analytics/support systems. Activity operations are claims, while LINK_RESOURCE_IDENTITY is a grounded catalog association.

Times use UTC ISO-8601 Z. Export/capture and per-record observation timestamps differ, sometimes by days. Both must satisfy audit_at. Snapshots can contain old history, later recreations and independent replica state. Identity history contains old/new emails, hashes and phones; case-insensitive exact email matching is needed. Similar email decoys and unrelated global records make substring/name matching unsafe.

Observed request languages: English, Spanish, Portuguese, French, Japanese and Korean. Ten official requests are access/correction/export/support/marketing requests. Public samples also request verification of prior deletion and deletion completion without a simple imperative delete phrase.

Policy treatments: DELETE (profiles, secondary identifiers, search, cache, attachments, exports, marketing), REDACT (shared support conversations, email delivery logs, tombstones), ANONYMIZE (analytics/telemetry), RETAIN (security, legal hold, backup). Tombstones may retain stable user_id but not email_hash. Backup retention requires blocked restore access. Enabled connectors and restoration events can recreate data.

Native PDF extraction succeeded for all four documents; only records with grounded resource identifiers can produce output operations. OCR needs an installed Tesseract executable and explicit failure reporting. Screenshots must be parsed as business artifacts, not assumed verdicts. Risks: trace joins, anonymized identity linkage, OCR identifiers, mixed timestamps, policy category inference, independent replicas, misleading reported success, and over-attribution of document context.

Contract discrepancy: README packaging examples place reports under code/evaluation; AGENTS and statement also name evaluation paths. Use code/evaluation in the archive with explicit README instructions, following the starter layout.
