from dataclasses import asdict
import csv
import json
import logging
from .models import read_csv, identifiers, Link, timestamp
from .identity_resolver import IdentityResolver
from .evidence_ingestion import EvidenceStore
from .knowledge_graph import EvidenceGraph
from .request_intent import authorizes_deletion
from .temporal_engine import reconstruct
from .policy_engine import PolicyEngine
from .remediation_planner import plan
from .output_validator import validate
from .dependency_analyzer import analyze_dependencies


class Auditor:
    def __init__(self, root):
        self.root = root
        dataset = root / 'dataset'
        self.identity = IdentityResolver(read_csv(dataset / 'user_identities.csv'), read_csv(dataset / 'user_audit_log.csv'))
        self.store = EvidenceStore(dataset, read_csv(dataset / 'evidence_files.csv'), root / '.cache')
        self.activity = read_csv(dataset / 'system_activity.csv')
        for row in self.activity:
            values = identifiers(row['details'])
            if values:
                self.store.links.append(Link(row['resource_id'], values, row['event_time'], row['event_time'], row['activity_id']))
        self.graph = EvidenceGraph(self.store.observations, self.store.links)
        for row in self.activity:
            if row['event_type'] in ('SYNC_RECORD', 'INDEX_RECORD', 'RESTORE_BACKUP'):
                self.graph.edges.append((row['source_system'], 'PROCESS_WRITES_TO_SYSTEM', row['target_system'], row['activity_id'], row['event_time']))
        self.policy = PolicyEngine(read_csv(dataset / 'deletion_rules.csv'))
        self.traces = {}

    def audit(self, request):
        case = request['case_id']
        if not authorizes_deletion(request['request_text']):
            self.traces[case] = {'intent': 'not authorized'}
            return dict(case_id=case, deletion_status='NOT_APPLICABLE', steps_json='[]')
        cutoff = timestamp(request['audit_at'])
        profile = self.identity.profile(request['email'], cutoff)
        resources = self.graph.discover(profile['identifiers'], cutoff)
        states = reconstruct(self.graph, self.store.scopes, resources, cutoff)
        # A previously absent account is outside a later request when the same subject
        # has a different, explicitly observed account in the current request window.
        requested = timestamp(request['requested_at'])
        current_accounts = {r for r, o in states.items() if o.category == 'USER_PROFILE' and timestamp(o.observed_at) >= requested}
        if current_accounts:
            states = {r: o for r, o in states.items() if not (o.category == 'USER_PROFILE' and o.state == 'ABSENT' and timestamp(o.observed_at) < requested and r not in current_accounts)}
        decisions = [self.policy.decide(states[r], cutoff) for r in sorted(states)]
        status, steps = plan(decisions)
        uncertainty = [] if decisions else ['No attributable state evidence before cutoff; completeness is unproven. COMPLETE is a forced three-label fallback, not proof of absence.']
        self.traces[case] = dict(identity=profile, resources=sorted(resources), timelines={r: [asdict(o) for o in self.graph.resources[r] if o.available(cutoff)] for r in resources}, decisions=[asdict(d) for d in decisions], flow_and_restore_events=analyze_dependencies(self.activity, resources, cutoff, self.graph), uncertainty=uncertainty, steps=steps)
        return dict(case_id=case, deletion_status=status, steps_json=json.dumps(steps, ensure_ascii=False, separators=(',', ':')))

    def run(self, requests, output):
        rows = []
        for request in sorted(requests, key=lambda r: r['case_id']):
            try:
                rows.append(self.audit(request))
            except (ValueError, KeyError) as error:
                raise ValueError(f'Audit failed for {request["case_id"]}: {error}') from error
        uncertain = [case for case, trace in self.traces.items() if trace.get('uncertainty')]
        if uncertain: logging.warning('No attributable state evidence for %d cases; see uncertainty report/inspection', len(uncertain))
        validate(rows, requests, self.store, self.graph)
        temporary = output.with_name(output.name + '.tmp')
        with temporary.open('w', encoding='utf8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['case_id', 'deletion_status', 'steps_json'])
            writer.writeheader(); writer.writerows(rows)
        temporary.replace(output)
        return rows
