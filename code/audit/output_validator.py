import json
import re
from .models import timestamp, read_csv, normalize, identifiers
from .identity_resolver import IdentityResolver
from .remediation_planner import OPERATIONS, sort_key

FIELDS = {'step_no', 'phase', 'system_id', 'resource_id', 'operation', 'state', 'evidence_id'}


def _event_support(step, source, kind, observations, profile, store, cutoff):
    """An event ID is not a state assertion: require independent file corroboration.

    Activity checks can corroborate their explicitly checked control state. Identity
    audits can corroborate attribution of exposed identifiers, never deletion.
    Neither path promotes a successful mutation to proof of its resulting state.
    """
    supporting = [o for o in observations if o.state == step['state']
                  and o.evidence in store.manifest
                  and timestamp(store.manifest[o.evidence]['captured_at']) <= cutoff
                  and timestamp(o.observed_at) >= timestamp(source['event_time'])]
    if kind == 'activity':
        if source['resource_id'] != step['resource_id'] or source['target_system'] != step['system_id']:
            raise ValueError('Activity citation refers to wrong resource or system')
        subjects = identifiers(source['details'])
        if subjects and not subjects.intersection(profile['identifiers']):
            raise ValueError('Activity citation refers to wrong subject')
        checks = {
            'CHECK_DATA_FLOW': ('REPORT_ACTIVE_DATA_FLOW', r'\bremains enabled\b'),
            'CHECK_RESTORE_ACCESS': ('REPORT_RESTORE_RISK', r'\bcan still be restored\b'),
        }
        check = checks.get(source['event_type'])
        if not check or step['operation'] != check[0] or not re.search(check[1], source['details']):
            raise ValueError('Activity claim does not establish asserted state')
        if not re.search(r'(?<!\w)' + re.escape(step['resource_id']) + r'(?!\w)', source['details']):
            raise ValueError('Activity check lacks resource provenance')
    else:
        if source['user_id'] != profile['user_id']:
            raise ValueError('Audit citation refers to wrong subject')
        if step['operation'] not in {'REPORT_REMAINING_RECORD', 'REPORT_EXPOSED_PII'}:
            raise ValueError('Identity audit does not establish asserted state')
        field = source['field_name']
        if field not in {'email', 'email_hash', 'phone'}:
            raise ValueError('Audit field lacks supported identifier provenance')
        values = {normalize(source[k]) for k in ('old_value', 'new_value') if source[k]}
        if field == 'phone': values = {re.sub(r'[^\d+]', '', v) for v in values}
        supporting = [o for o in supporting if values.intersection(o.identifiers)]
    if not supporting:
        raise ValueError('Event citation lacks independent state/identifier corroboration')


def validate(rows, requests, store, graph):
    # Read actual participant source rows once per validation, not per step.
    activity = {r['activity_id']: r for r in read_csv(store.dataset / 'system_activity.csv')}
    history = read_csv(store.dataset / 'user_audit_log.csv')
    audits = {r['audit_id']: r for r in history}
    identity = IdentityResolver(read_csv(store.dataset / 'user_identities.csv'), history)
    expected = sorted(r['case_id'] for r in requests)
    if [r['case_id'] for r in rows] != expected or len(set(expected)) != len(expected): raise ValueError('Output case coverage or order invalid')
    request_map = {r['case_id']: r for r in requests}
    for row in rows:
        if set(row) != {'case_id', 'deletion_status', 'steps_json'}: raise ValueError('Incorrect CSV schema')
        status = row['deletion_status']
        if status not in {'COMPLETE', 'INCOMPLETE', 'NOT_APPLICABLE'}: raise ValueError('Invalid deletion status')
        steps = json.loads(row['steps_json'])
        if not isinstance(steps, list): raise ValueError('steps_json must be array')
        if status == 'NOT_APPLICABLE' and steps: raise ValueError('Unauthorized deletion steps')
        if steps != sorted(steps, key=sort_key): raise ValueError('Invalid operation ordering')
        seen = set()
        cutoff = timestamp(request_map[row['case_id']]['audit_at'])
        profile = identity.profile(request_map[row['case_id']]['email'], cutoff) if steps else None
        subject_resources = graph.discover(profile['identifiers'], cutoff) if profile else set()
        for i, step in enumerate(steps, 1):
            if set(step) != FIELDS or type(step['step_no']) is not int or step['step_no'] != i: raise ValueError('Invalid step fields/numbering')
            if any(not isinstance(step[k], str) for k in FIELDS - {'step_no'}): raise ValueError('Non-string step field')
            if OPERATIONS.get(step['operation']) != (step['phase'], step['state']): raise ValueError('Invalid operation/state')
            if status == 'COMPLETE' and step['phase'] != 'VERIFICATION': raise ValueError('Complete case has non-verification')
            key = (step['operation'], step['system_id'], step['resource_id'])
            if key in seen: raise ValueError('Duplicate operation')
            seen.add(key)
            evidence = step['evidence_id']
            cite = step['phase'] == 'FINDING' or status == 'COMPLETE'
            if bool(evidence) != cite: raise ValueError('Incorrect evidence citation behavior')
            if evidence:
                if not re.fullmatch(r'(?:evidence|activity|audit)_\d+', evidence): raise ValueError('Invalid evidence ID syntax')
                kind = evidence.split('_', 1)[0]
                index = {'evidence': store.manifest, 'activity': activity, 'audit': audits}[kind]
                if evidence not in index: raise ValueError('Unknown evidence ID')
                source = index[evidence]
                if timestamp(source['captured_at'] if kind == 'evidence' else source['event_time']) > cutoff:
                    raise ValueError('Future evidence citation')
            resource = step['resource_id']
            if resource not in subject_resources: raise ValueError('Resource does not belong to request subject')
            valid = [o for o in graph.resources.get(resource, []) if o.available(cutoff) and o.system == step['system_id']]
            if not valid: raise ValueError(f'Unsupported resource reference: {resource}')
            if cite and kind != 'evidence':
                _event_support(step, source, kind, valid, profile, store, cutoff)
            if cite and kind == 'evidence' and not any(o.evidence == evidence for o in valid) and not any(s.evidence == evidence and s.system == step['system_id'] and timestamp(s.captured_at) <= cutoff for s in store.scopes):
                raise ValueError('Citation does not support resource')
            if cite and kind == 'evidence':
                observations = [o for o in valid if o.evidence == evidence]
                scope_absence = step['state'] == 'ABSENT' and any(s.evidence == evidence and s.system == step['system_id'] and resource not in s.resources for s in store.scopes)
                if not any(o.state == step['state'] for o in observations) and not scope_absence:
                    raise ValueError('Cited evidence does not establish asserted state')
        if status == 'INCOMPLETE':
            required = {'REPORT_REMAINING_RECORD': ('DELETE_RECORD', 'VERIFY_RECORD_ABSENT'), 'REPORT_EXPOSED_PII': (None, None), 'REPORT_ACTIVE_DATA_FLOW': ('DISABLE_DATA_FLOW', 'VERIFY_DATA_FLOW_DISABLED'), 'REPORT_RESTORE_RISK': ('BLOCK_RESTORE', 'VERIFY_RESTORE_BLOCKED')}
            for step in steps:
                if step['phase'] != 'FINDING': continue
                remediation, verification = required[step['operation']]
                target = (step['system_id'], step['resource_id'])
                if remediation:
                    if (remediation, *target) not in seen or (verification, *target) not in seen: raise ValueError('Finding missing matching remediation or verification')
                elif not any((r, *target) in seen and (v, *target) in seen for r,v in [('REDACT_RECORD','VERIFY_RECORD_REDACTED'),('ANONYMIZE_RECORD','VERIFY_RECORD_ANONYMIZED')]):
                    raise ValueError('Exposed PII missing treatment and verification')
        if status == 'INCOMPLETE' and {s['phase'] for s in steps} != {'FINDING', 'REMEDIATION', 'VERIFICATION'}: raise ValueError('Incomplete plan missing phase')
