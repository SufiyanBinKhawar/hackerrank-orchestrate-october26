from dataclasses import dataclass
from .models import timestamp


@dataclass
class Decision:
    observation: object
    action: str
    desired: str
    compliant: bool
    rule: str
    condition: str


class PolicyEngine:
    def __init__(self, rules):
        self.rules = {row['data_category']: row for row in rules}
        if len(self.rules) != len(rules): raise ValueError('Multiple rules per category require explicit precedence')

    def decide(self, obs, cutoff):
        if obs.category == 'DATA_FLOW': return Decision(obs, 'DISABLE', 'DISABLED', obs.state == 'DISABLED', '', 'Subject-linked active connector')
        rule = self.rules[obs.category]
        action = rule['required_action']
        if obs.category == 'BACKUP_ARCHIVE':
            action, desired = 'BLOCK', 'BLOCKED'
        else:
            desired = {'DELETE': 'ABSENT', 'REDACT': 'REDACTED', 'ANONYMIZE': 'ANONYMIZED', 'RETAIN': 'PRESENT'}[action]
        until = obs.attributes.get('retention_until', obs.attributes.get('retained_until'))
        if action == 'RETAIN' and until and timestamp(until) < cutoff:
            raise ValueError(f'Expired retention has no supplied fallback rule: {obs.resource}')
        if obs.category == 'LEGAL_HOLD_RECORD' and obs.attributes.get('legal_hold_active') is False:
            raise ValueError(f'Inactive hold has no supplied fallback rule: {obs.resource}')
        return Decision(obs, action, desired, obs.state == desired, rule['rule_id'], rule['condition'])
