from collections import defaultdict
from .models import Observation, timestamp


def reconstruct(graph, scopes, resources, cutoff):
    states = {}
    for resource in resources:
        observations = [o for o in graph.resources.get(resource, []) if o.available(cutoff)]
        # Complete SQL table snapshots may establish absence, but only for a previously grounded resource.
        if observations:
            category = observations[-1].category
            system = observations[-1].system
            for scope in scopes:
                # A file's tables are an export subset, not necessarily the entire company's database.
                # Cross-table absence is grounded only when this same artifact contains the resource.
                covered = any(o.evidence == scope.evidence for o in observations)
                if covered and scope.system == system and scope.category == category and resource not in scope.resources and timestamp(scope.captured_at) <= cutoff:
                    observations.append(Observation(resource, system, category, 'ABSENT', scope.captured_at, scope.captured_at, scope.evidence, 'complete SQL table scope', set(), scope.replica))
        latest = {}
        for obs in observations:
            key = obs.replica
            ordering = (timestamp(obs.observed_at), timestamp(obs.captured_at), obs.evidence, obs.location)
            if key not in latest or ordering > latest[key][0]: latest[key] = (ordering, obs)
        if latest:
            copies = [item[1] for item in latest.values()]
            # A proven surviving independent replica cannot be erased by a newer primary read.
            violations = [o for o in copies if o.state in ('PRESENT', 'ACTIVE') and o.category not in ('SECURITY_AUDIT_LOG', 'LEGAL_HOLD_RECORD')]
            candidates = violations or copies
            states[resource] = max(candidates, key=lambda o: (timestamp(o.observed_at), timestamp(o.captured_at), o.evidence))
    return states
