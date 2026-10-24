import json
from collections import Counter


def evaluate(predictions, reference, report, auditor=None, requests=None):
    expected = {r['case_id']: r for r in reference}
    status = exact = sequence = matched = predicted_count = expected_count = 0
    fields = Counter(); totals = Counter(); diagnostics = []; gaps = Counter()
    request_map = {r['case_id']: r for r in (requests or [])}
    for row in predictions:
        gold = expected[row['case_id']]
        pred, truth = json.loads(row['steps_json']), json.loads(gold['steps_json'])
        status += row['deletion_status'] == gold['deletion_status']
        exact += pred == truth
        strip = lambda seq: [{k: v for k, v in s.items() if k != 'evidence_id'} for s in seq]
        sequence += strip(pred) == strip(truth)
        canonical = lambda s: json.dumps({k:v for k,v in s.items() if k != 'step_no'}, sort_keys=True)
        pc, tc = Counter(map(canonical, pred)), Counter(map(canonical, truth))
        matched += sum((pc & tc).values()); predicted_count += len(pred); expected_count += len(truth)
        # Positional alignment penalizes missing/extra and incorrectly ordered steps.
        for i in range(max(len(pred), len(truth))):
            p = pred[i] if i < len(pred) else {}; t = truth[i] if i < len(truth) else {}
            for key in ('phase','system_id','resource_id','operation','state','evidence_id','step_no'):
                totals[key] += 1; fields[key] += key in p and key in t and p[key] == t[key]
        if pred != truth or row['deletion_status'] != gold['deletion_status']:
            reasons = []
            if auditor:
                from audit.models import timestamp
                cutoff = timestamp(request_map[row['case_id']]['audit_at'])
                discovered = auditor.traces[row['case_id']].get('resources', [])
                for missing in (tc-pc).elements():
                    step = json.loads(missing); resource = step['resource_id']
                    observations = auditor.graph.resources.get(resource, [])
                    available = [o for o in observations if o.available(cutoff)]
                    if not observations: reason = 'No parsed state observation for this resource in any artifact; resource may occur only in activity claims or be absent from exported tables.'
                    elif not available: reason = 'All parsed resource observations are after the audit cutoff by capture or observation time.'
                    elif resource not in discovered: reason = 'Resource has a pre-cutoff state observation but no grounded pre-cutoff subject link.'
                    else: reason = 'State, policy, citation, or scope conflict; inspect the trace alongside the reference.'
                    gaps[reason] += 1; reasons.append(f'- {resource}: {reason}')
            diagnostics.append(f'### {row["case_id"]}\n\nStatus: predicted {row["deletion_status"]}; expected {gold["deletion_status"]}.\n\nMissing steps:\n```\n' + '\n'.join((tc-pc).elements()) + '\n```\nExtra steps:\n```\n' + '\n'.join((pc-tc).elements()) + '\n```\nOrdered match without evidence IDs: ' + str(strip(pred)==strip(truth)) + '.\n\n' + '\n'.join(reasons) + '\n')
    n = len(predictions); precision = matched / predicted_count if predicted_count else 0; recall = matched / expected_count if expected_count else 0
    metrics = dict(cases=n,status_accuracy=status/n,exact_step_arrays=exact/n,sequence_without_evidence=sequence/n,precision=precision,recall=recall,f1=2*precision*recall/(precision+recall) if precision+recall else 0,field_accuracy={k:fields[k]/totals[k] for k in totals})
    narrative = report.with_name('evaluation_method.md')
    report.write_text('# Public sample evaluation\n\nMeasured metrics:\n```\n' + json.dumps(metrics, indent=2) + '\n```\n\nStep precision/recall use multiset equality across all fields except step_no. Sequence metrics preserve array order. Field accuracy uses positional alignment, with missing/extra positions counted as incorrect. Sample answers are read only by this evaluator and never used to change predictions.\n\nFailure classification:\n```\n' + json.dumps(gaps, indent=2) + '\n```\n\n' + (narrative.read_text(encoding='utf8') if narrative.exists() else '') + '\n\n' + '\n'.join(diagnostics), encoding='utf8')
    print(json.dumps(metrics, indent=2)); return metrics
