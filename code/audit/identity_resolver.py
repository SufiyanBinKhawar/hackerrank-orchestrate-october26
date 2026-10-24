from collections import defaultdict
from .models import normalize, timestamp


class IdentityResolver:
    def __init__(self, current, history):
        self.current = {r['user_id']: r for r in current}
        self.history = defaultdict(list)
        self.index = defaultdict(set)
        for row in history:
            self.history[row['user_id']].append(row)
        for uid, row in self.current.items():
            for key in ('email', 'phone', 'email_hash'):
                if row[key]: self.index[normalize(row[key])].add(uid)
            for change in self.history[uid]:
                for key in ('old_value', 'new_value'):
                    if change[key]: self.index[normalize(change[key])].add(uid)

    def profile(self, email, cutoff):
        candidates = self.index.get(normalize(email), set())
        eligible = []
        for uid in candidates:
            values = self.values(uid, cutoff)
            if normalize(email) in values: eligible.append((uid, values))
        if len(eligible) != 1:
            raise ValueError(f'Identity unresolved or ambiguous ({len(eligible)} candidates)')
        uid, values = eligible[0]
        return {'user_id': uid, 'identifiers': sorted(values), 'history': [r for r in self.history[uid] if timestamp(r['event_time']) <= cutoff]}

    def values(self, uid, cutoff):
        row = self.current[uid]
        values = {uid}
        for field in ('email', 'phone', 'email_hash'):
            changes = sorted((r for r in self.history[uid] if r['field_name'] == field), key=lambda r: r['event_time'])
            # Reverse future changes before recovering historical values available at cutoff.
            value = row[field]
            for change in reversed(changes):
                if timestamp(change['event_time']) > cutoff: value = change['old_value']
            if value: values.add(normalize(value))
            for change in changes:
                if timestamp(change['event_time']) <= cutoff:
                    values.update(normalize(change[k]) for k in ('old_value', 'new_value') if change[k])
        return values
