"""Run from any directory; all default paths resolve relative to this checkout."""
from pathlib import Path
import argparse
import json
import logging
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if (ROOT / '.deps').is_dir(): sys.path.insert(0, str(ROOT / '.deps'))
from audit.models import read_csv
from audit.orchestrator import Auditor
from audit.output_validator import validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', action='store_true')
    parser.add_argument('--evaluate', action='store_true')
    parser.add_argument('--validate', type=Path)
    parser.add_argument('--inspect', metavar='CASE_ID')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    started = time.perf_counter()
    auditor = Auditor(ROOT)
    requests = read_csv(ROOT / 'dataset' / ('sample_deletion_requests.csv' if args.sample or args.evaluate else 'deletion_requests.csv'))
    if args.validate:
        path = args.validate if args.validate.is_absolute() else ROOT / args.validate
        validate(read_csv(path), requests, auditor.store, auditor.graph)
        print(f'Validated {len(requests)} rows'); return
    if args.inspect:
        request = next((r for r in requests if r['case_id'] == args.inspect), None)
        if request is None: parser.error('Case not found in selected request set')
        auditor.audit(request)
        print(json.dumps(auditor.traces[args.inspect], indent=2, ensure_ascii=True, default=lambda x: sorted(x))); return
    output = args.output or Path('sample_predictions.csv' if args.sample or args.evaluate else 'output.csv')
    if not output.is_absolute(): output = ROOT / output
    rows = auditor.run(requests, output)
    elapsed = time.perf_counter() - started
    logging.info('Processed %d requests, %d observations in %.3f seconds', len(rows), len(auditor.store.observations), elapsed)
    if args.evaluate:
        from evaluation.main import evaluate
        evaluate(rows, read_csv(ROOT / 'dataset/sample_output.csv'), ROOT / 'code/evaluation/evaluation_report.md')
    if not args.sample and not args.evaluate:
        (ROOT / 'code/evaluation/usage_report.md').write_text(f'# Final runtime usage\n\nRequests: {len(rows)}. Elapsed wall time: {elapsed:.3f} seconds. Observations indexed: {len(auditor.store.observations)}.\n\nRuntime providers/models: none. Model calls: 0. Input tokens: 0. Output tokens: 0. Total tokens: 0. Tokens/request: 0. Total inference cost: $0. Cost/request: $0.\n\nDevelopment used codex_vscode with gpt-6-astra; development token/cost totals are not available and are not included in runtime metrics.\n', encoding='utf8')
    print(output)


if __name__ == '__main__': main()
