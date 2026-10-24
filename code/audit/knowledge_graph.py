from collections import defaultdict
from .models import timestamp


class EvidenceGraph:
    """Timestamped subject/resource edges and indexed observation timelines."""
    def __init__(self, observations, links):
        self.resources = defaultdict(list)
        self.identifiers = defaultdict(list)
        self.edges = []
        for obs in observations:
            self.resources[obs.resource].append(obs)
            for value in obs.identifiers:
                self.identifiers[value].append((obs.resource, obs.observed_at, obs.captured_at, obs.evidence))
                self.edges.append((value, 'IDENTIFIER_LINKS_RESOURCE', obs.resource, obs.evidence, obs.observed_at))
            self.edges.append((obs.resource, 'RESOURCE_STORED_IN_SYSTEM', obs.system, obs.evidence, obs.observed_at))
            self.edges.append((obs.resource, 'RESOURCE_OBSERVED_IN_EVIDENCE', obs.evidence, obs.evidence, obs.observed_at))
        for link in links:
            for value in link.identifiers:
                self.identifiers[value].append((link.resource, link.observed_at, link.captured_at, link.evidence))

    def discover(self, values, cutoff):
        values = set(values)
        result = set()
        for value in values:
            for resource, observed, captured, evidence in self.identifiers.get(value, []):
                if timestamp(observed) <= cutoff and timestamp(captured) <= cutoff:
                    same = [o for o in self.resources.get(resource, []) if o.evidence == evidence and o.observed_at == observed]
                    owners = {o.attributes[k] for o in same for k in ('user_id', 'customer_reference') if isinstance(o.attributes.get(k), str) and o.attributes[k].startswith('user_')}
                    if owners and not owners.intersection(values): continue
                    result.add(resource)
        return result
