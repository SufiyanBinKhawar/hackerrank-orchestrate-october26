OPERATIONS = {
    'REPORT_REMAINING_RECORD': ('FINDING', 'PRESENT'),
    'REPORT_EXPOSED_PII': ('FINDING', 'PRESENT'),
    'REPORT_ACTIVE_DATA_FLOW': ('FINDING', 'ACTIVE'),
    'REPORT_RESTORE_RISK': ('FINDING', 'ACTIVE'),
    'DISABLE_DATA_FLOW': ('REMEDIATION', 'DISABLED'),
    'BLOCK_RESTORE': ('REMEDIATION', 'BLOCKED'),
    'DELETE_RECORD': ('REMEDIATION', 'ABSENT'),
    'REDACT_RECORD': ('REMEDIATION', 'REDACTED'),
    'ANONYMIZE_RECORD': ('REMEDIATION', 'ANONYMIZED'),
    'VERIFY_RECORD_ABSENT': ('VERIFICATION', 'ABSENT'),
    'VERIFY_RECORD_PRESENT': ('VERIFICATION', 'PRESENT'),
    'VERIFY_RECORD_REDACTED': ('VERIFICATION', 'REDACTED'),
    'VERIFY_RECORD_ANONYMIZED': ('VERIFICATION', 'ANONYMIZED'),
    'VERIFY_DATA_FLOW_DISABLED': ('VERIFICATION', 'DISABLED'),
    'VERIFY_RESTORE_BLOCKED': ('VERIFICATION', 'BLOCKED'),
}
ORDER = {operation: i for i, operation in enumerate(OPERATIONS)}
REMEDIATION = {'DELETE': 'DELETE_RECORD', 'REDACT': 'REDACT_RECORD', 'ANONYMIZE': 'ANONYMIZE_RECORD', 'DISABLE': 'DISABLE_DATA_FLOW', 'BLOCK': 'BLOCK_RESTORE'}
FINDINGS = {'DELETE': 'REPORT_REMAINING_RECORD', 'REDACT': 'REPORT_EXPOSED_PII', 'ANONYMIZE': 'REPORT_EXPOSED_PII', 'DISABLE': 'REPORT_ACTIVE_DATA_FLOW', 'BLOCK': 'REPORT_RESTORE_RISK'}
VERIFY = {'ABSENT': 'VERIFY_RECORD_ABSENT', 'PRESENT': 'VERIFY_RECORD_PRESENT', 'REDACTED': 'VERIFY_RECORD_REDACTED', 'ANONYMIZED': 'VERIFY_RECORD_ANONYMIZED', 'DISABLED': 'VERIFY_DATA_FLOW_DISABLED', 'BLOCKED': 'VERIFY_RESTORE_BLOCKED'}


def sort_key(step):
    return ORDER[step['operation']], step['system_id'], step['resource_id']


def plan(decisions):
    incomplete = any(not decision.compliant for decision in decisions)
    steps = []
    def add(operation, observation, evidence):
        phase, state = OPERATIONS[operation]
        steps.append(dict(step_no=0, phase=phase, system_id=observation.system, resource_id=observation.resource, operation=operation, state=state, evidence_id=evidence))
    for decision in decisions:
        obs = decision.observation
        if not decision.compliant:
            if decision.action == 'RETAIN': raise ValueError(f'Absent required retained record cannot be repaired with permitted operations: {obs.resource}')
            add(FINDINGS[decision.action], obs, obs.evidence)
            add(REMEDIATION[decision.action], obs, '')
        add(VERIFY[decision.desired], obs, '' if incomplete else obs.evidence)
    steps.sort(key=sort_key)
    for i, step in enumerate(steps, 1): step['step_no'] = i
    return ('INCOMPLETE' if incomplete else 'COMPLETE'), steps
