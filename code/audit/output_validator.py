import json
from .models import timestamp
from .remediation_planner import OPERATIONS, sort_key

FIELDS = {'step_no', 'phase', 'system_id', 'resource_id', 'operation', 'state', 'evidence_id'}


def validate(rows, requests, store, graph):
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
                if evidence not in store.manifest: raise ValueError('Unknown evidence ID')
                if timestamp(store.manifest[evidence]['captured_at']) > cutoff: raise ValueError('Future evidence citation')
            resource = step['resource_id']
            valid = [o for o in graph.resources.get(resource, []) if o.available(cutoff) and o.system == step['system_id']]
            if not valid: raise ValueError(f'Unsupported resource reference: {resource}')
            if cite and not any(o.evidence == evidence for o in valid) and not any(s.evidence == evidence and s.system == step['system_id'] and timestamp(s.captured_at) <= cutoff for s in store.scopes):
                raise ValueError('Citation does not support resource')
        if status == 'INCOMPLETE' and {s['phase'] for s in steps} != {'FINDING', 'REMEDIATION', 'VERIFICATION'}: raise ValueError('Incomplete plan missing phase')
