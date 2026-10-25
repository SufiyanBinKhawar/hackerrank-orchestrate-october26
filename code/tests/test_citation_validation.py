"""Source existence and state support are independent citation requirements."""
import json
import pytest
from test_auditor import fixture, record, write_csv
from audit.orchestrator import Auditor
from audit.output_validator import validate


def replace_citation(row, evidence):
    steps = json.loads(row['steps_json'])
    steps[0]['evidence_id'] = evidence
    return {**row, 'steps_json': json.dumps(steps)}


def activity_fixture(tmp_path, **changes):
    engine, request = fixture(tmp_path, [record('data_flow_90001', 'DATA_FLOW', 'ACTIVE', time='2026-01-20T00:00:00Z')])
    activity = dict(activity_id='activity_90001', event_time='2026-01-10T00:00:00Z',
                    event_type='CHECK_DATA_FLOW', source_system='deletion_worker',
                    target_system='integration_service', resource_id='data_flow_90001',
                    reported_result='SUCCESS',
                    details='Connector status check confirmed that data flow data_flow_90001 remains enabled.')
    activity.update(changes)
    write_csv(tmp_path/'dataset/system_activity.csv', ','.join(activity), [activity])
    engine = Auditor(tmp_path)
    row = replace_citation(engine.audit(request), activity['activity_id'])
    return engine, request, row


def audit_fixture(tmp_path, **changes):
    engine, request = fixture(tmp_path, [record(time='2026-01-20T00:00:00Z', email='previous@example.test')])
    audit = dict(audit_id='audit_90001', user_id='user_90001', event_time='2026-01-10T00:00:00Z',
                 field_name='email', old_value='previous@example.test', new_value='alex@example.test')
    audit.update(changes)
    write_csv(tmp_path/'dataset/user_audit_log.csv', ','.join(audit), [audit])
    engine = Auditor(tmp_path)
    if audit['event_time'] > request['audit_at']:
        request['email'] = audit['old_value']
    row = replace_citation(engine.audit(request), audit['audit_id'])
    return engine, request, row


def check(engine, request, row):
    validate([row], [request], engine.store, engine.graph)


def test_existing_file_output_still_valid(tmp_path):
    engine, request = fixture(tmp_path, [record(state='NOT_FOUND')])
    check(engine, request, engine.audit(request))


def test_activity_check_with_independent_state_provenance(tmp_path):
    engine, request, row = activity_fixture(tmp_path)
    check(engine, request, row)


def test_audit_attribution_with_independently_observed_identifier(tmp_path):
    engine, request, row = audit_fixture(tmp_path)
    check(engine, request, row)


@pytest.mark.parametrize('prefix', ['evidence', 'activity', 'audit'])
def test_nonexistent_source_id(tmp_path, prefix):
    engine, request = fixture(tmp_path, [record()])
    row = replace_citation(engine.audit(request), prefix+'_99999')
    with pytest.raises(ValueError, match='Unknown evidence ID'): check(engine, request, row)


def test_activity_success_is_not_state_proof_even_with_resource_match(tmp_path):
    engine, request, row = activity_fixture(tmp_path, event_type='DISABLE_DATA_FLOW',
                                           details='Policy action completed for data_flow_90001.')
    with pytest.raises(ValueError, match='Activity claim'): check(engine, request, row)


def test_activity_check_without_confirmed_result_rejected(tmp_path):
    engine, request, row = activity_fixture(tmp_path, details='Connector check submitted for data_flow_90001.')
    with pytest.raises(ValueError, match='Activity claim'): check(engine, request, row)


@pytest.mark.parametrize('factory', [activity_fixture, audit_fixture])
def test_future_event_rejected(tmp_path, factory):
    engine, request, row = factory(tmp_path, event_time='2026-02-02T00:00:00Z')
    with pytest.raises(ValueError, match='Future evidence'): check(engine, request, row)


def test_future_file_capture_rejected(tmp_path):
    engine, request = fixture(tmp_path, [record()])
    row = engine.audit(request)
    engine.store.manifest['evidence_90001']['captured_at'] = '2026-02-02T00:00:00Z'
    with pytest.raises(ValueError, match='Future evidence'): check(engine, request, row)


@pytest.mark.parametrize('change', [{'resource_id': 'data_flow_90002'}, {'target_system': 'other_service'}])
def test_activity_wrong_resource_or_system(tmp_path, change):
    engine, request, row = activity_fixture(tmp_path, **change)
    with pytest.raises(ValueError, match='wrong resource or system'): check(engine, request, row)


def test_audit_wrong_subject(tmp_path):
    engine, request, row = audit_fixture(tmp_path, user_id='user_90002', new_value='alex.jr@example.test')
    with pytest.raises(ValueError, match='wrong subject'): check(engine, request, row)


def test_activity_wrong_subject_in_details(tmp_path):
    engine, request, row = activity_fixture(tmp_path, details='Connector status check confirmed that data flow data_flow_90001 remains enabled for user_90002.')
    with pytest.raises(ValueError, match='wrong subject'): check(engine, request, row)


def test_audit_identifier_not_in_resource(tmp_path):
    engine, request, row = audit_fixture(tmp_path, old_value='unrelated@example.test', new_value='other@example.test')
    with pytest.raises(ValueError, match='corroboration'): check(engine, request, row)


def test_identity_change_cannot_prove_account_absence(tmp_path):
    engine, request, row = audit_fixture(tmp_path)
    steps = [dict(step_no=1, phase='VERIFICATION', system_id='account_service',
                  resource_id='account_90001', operation='VERIFY_RECORD_ABSENT',
                  state='ABSENT', evidence_id='audit_90001')]
    row.update(deletion_status='COMPLETE', steps_json=json.dumps(steps))
    with pytest.raises(ValueError, match='Identity audit does not establish'): check(engine, request, row)


@pytest.mark.parametrize('factory', [activity_fixture, audit_fixture])
def test_event_needs_matching_independent_state(tmp_path, factory):
    engine, request, row = factory(tmp_path)
    for observations in engine.graph.resources.values():
        for obs in observations: obs.state = 'ABSENT'
    with pytest.raises(ValueError, match='corroboration'): check(engine, request, row)


@pytest.mark.parametrize('factory', [activity_fixture, audit_fixture])
def test_event_corroboration_cannot_use_future_capture(tmp_path, factory):
    engine, request, row = factory(tmp_path)
    engine.store.manifest['evidence_90001']['captured_at'] = '2026-02-02T00:00:00Z'
    with pytest.raises(ValueError, match='corroboration'): check(engine, request, row)


def test_file_citation_for_another_requests_resource_rejected(tmp_path):
    engine, request = fixture(tmp_path, [record(subject='user_90002')])
    other_request = {**request, 'email': 'alex.jr@example.test'}
    row = engine.audit(other_request)
    with pytest.raises(ValueError, match='request subject'): check(engine, request, row)
