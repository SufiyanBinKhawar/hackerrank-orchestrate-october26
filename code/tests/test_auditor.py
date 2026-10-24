"""Independent fixtures: no sample answer is used by these regression tests."""
import csv
import json
from pathlib import Path
import pytest
from audit.orchestrator import Auditor
from audit.models import Observation, timestamp
from audit.knowledge_graph import EvidenceGraph
from audit.temporal_engine import reconstruct
from audit.output_validator import validate
from audit.request_intent import authorizes_deletion

EARLY = '2026-01-01T00:00:00Z'
AUDIT = '2026-02-01T00:00:00Z'


def write_csv(path, columns, rows):
    with path.open('w', encoding='utf8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns.split(','))
        writer.writeheader(); writer.writerows(rows)


def fixture(root, records, text='Please delete my account.', extra_files=()):
    data = root / 'dataset'; (data / 'evidence').mkdir(parents=True)
    identities = [dict(user_id='user_90001', name='Alex Example', email='alex@example.test', phone='+1 555 1010', email_hash='a'*64, updated_at=EARLY), dict(user_id='user_90002', name='Alex Example', email='alex.jr@example.test', phone='+1 555 1011', email_hash='b'*64, updated_at=EARLY)]
    write_csv(data/'user_identities.csv','user_id,name,email,phone,email_hash,updated_at',identities)
    write_csv(data/'user_audit_log.csv','audit_id,user_id,event_time,field_name,old_value,new_value',[])
    write_csv(data/'system_activity.csv','activity_id,event_time,event_type,source_system,target_system,resource_id,reported_result,details',[])
    policies = {'USER_PROFILE':'DELETE','SEARCH_INDEX_ENTRY':'DELETE','ACCOUNT_TOMBSTONE':'REDACT','ANALYTICS_PROFILE':'ANONYMIZE','SECURITY_AUDIT_LOG':'RETAIN','LEGAL_HOLD_RECORD':'RETAIN','BACKUP_ARCHIVE':'RETAIN','SUPPORT_MESSAGE':'REDACT'}
    write_csv(data/'deletion_rules.csv','rule_id,data_category,condition,required_action',[dict(rule_id=f'rule_{i}',data_category=k,condition='Fixture supplied condition',required_action=v) for i,(k,v) in enumerate(policies.items())])
    (data/'evidence/snapshot.json').write_text(json.dumps({'records':records}),encoding='utf8')
    manifest = [dict(file_id='evidence_90001',file_path='evidence/snapshot.json',origin='test',captured_at='2026-01-31T00:00:00Z')]
    for fid, filename, capture, content in extra_files:
        (data/'evidence'/filename).write_text(content,encoding='utf8')
        manifest.append(dict(file_id=fid,file_path='evidence/'+filename,origin='test',captured_at=capture))
    write_csv(data/'evidence_files.csv','file_id,file_path,origin,captured_at',manifest)
    request = dict(case_id='synthetic',email='alex@example.test',requested_at=EARLY,reported_status='COMPLETE',reported_at=EARLY,audit_at=AUDIT,request_text=text)
    return Auditor(root), request


def record(resource='account_90001', category='USER_PROFILE', state='FOUND', time=EARLY, subject='user_90001', **kwargs):
    return dict(resource_id=resource,record_type=category,result=state,recorded_at=time,subject_reference=subject,**kwargs)


def operations(row): return [s['operation'] for s in json.loads(row['steps_json'])]


def test_sync_recreation(tmp_path):
    records=[record(state='NOT_FOUND'),record(time='2026-01-20T00:00:00Z'),record('data_flow_90001','DATA_FLOW','ACTIVE')]
    engine,request=fixture(tmp_path,records)
    row=engine.audit(request)
    assert row['deletion_status']=='INCOMPLETE'
    ops=operations(row)
    assert ops==['REPORT_REMAINING_RECORD','REPORT_ACTIVE_DATA_FLOW','DISABLE_DATA_FLOW','DELETE_RECORD','VERIFY_RECORD_ABSENT','VERIFY_DATA_FLOW_DISABLED']


def test_identity_collision(tmp_path):
    engine,request=fixture(tmp_path,[record(state='NOT_FOUND'),record('account_90002',subject='alex.jr@example.test')])
    row=engine.audit(request)
    assert row['deletion_status']=='COMPLETE'
    assert [s['resource_id'] for s in json.loads(row['steps_json'])]==['account_90001']


@pytest.mark.parametrize('hash_value,expected',[ (None,'COMPLETE'),('a'*64,'INCOMPLETE') ])
def test_tombstone_stable_reference(tmp_path,hash_value,expected):
    tombstone=dict(resource_id='tombstone_90001',subject_reference='user_90001',name=None,email=None,phone=None,email_hash=hash_value,account_status='DELETED')
    engine,request=fixture(tmp_path,[record(state='NOT_FOUND'),tombstone])
    row=engine.audit(request)
    assert row['deletion_status']==expected
    assert 'DELETE_RECORD' not in operations(row)
    assert 'VERIFY_RECORD_REDACTED' in operations(row)


def test_retained_security_and_legal_hold(tmp_path):
    records=[record(state='NOT_FOUND'),record('audit_record_90001','SECURITY_AUDIT_LOG',retention_until='2030-01-01T00:00:00Z'),record('legal_hold_90001','LEGAL_HOLD_RECORD',legal_hold_active=True)]
    engine,request=fixture(tmp_path,records)
    row=engine.audit(request)
    assert row['deletion_status']=='COMPLETE'
    assert operations(row)==['VERIFY_RECORD_ABSENT','VERIFY_RECORD_PRESENT','VERIFY_RECORD_PRESENT']


def test_unsafe_backup(tmp_path):
    engine,request=fixture(tmp_path,[record(state='NOT_FOUND'),record('backup_90001','BACKUP_ARCHIVE','ACTIVE')])
    row=engine.audit(request)
    assert operations(row)==['REPORT_RESTORE_RISK','BLOCK_RESTORE','VERIFY_RECORD_ABSENT','VERIFY_RESTORE_BLOCKED']


def test_future_capture_ignored(tmp_path):
    future=json.dumps({'records':[record(time='2026-01-30T00:00:00Z')]})
    engine,request=fixture(tmp_path,[record(state='NOT_FOUND')],extra_files=[('evidence_90002','future.json','2026-02-02T00:00:00Z',future)])
    assert engine.audit(request)['deletion_status']=='COMPLETE'


def test_later_replica_survival():
    items=[Observation('account_90001','account_service','USER_PROFILE','PRESENT',EARLY,EARLY,'evidence_1','row',{'user_90001'},'failover'),Observation('account_90001','account_service','USER_PROFILE','ABSENT',AUDIT,AUDIT,'evidence_2','row',{'user_90001'},'primary')]
    states=reconstruct(EvidenceGraph(items,[]),[],{'account_90001'},timestamp(AUDIT))
    assert states['account_90001'].state=='PRESENT'
    assert states['account_90001'].replica=='failover'


@pytest.mark.parametrize('text,expected',[
    ('이 계정의 영구 삭제를 요청합니다.',True),
    ('계정을 삭제하지 마세요. 정보만 보내 주세요.',False),
    ('No quiero eliminar mi cuenta, solo exportar mis datos.',False),
    ('アカウントを削除しないでください。',False),
    ('Je demande la suppression de mon compte.',True),
    ('Não exclua minha conta.',False),
    ('Do not close the account. Reset my login.',False),
    ('Please stop promotional emails. I am not asking for deletion.',False),
    ('Can you verify that my account was deleted?',True),
])
def test_intent(text,expected): assert authorizes_deletion(text) is expected


def test_multilingual_non_deletion_integration(tmp_path):
    engine,request=fixture(tmp_path,[record()],text='No quiero eliminar mi cuenta, solo exportar mis datos.')
    row=engine.audit(request)
    assert row['deletion_status']=='NOT_APPLICABLE' and row['steps_json']=='[]'


def test_validator_rejects_citation_and_order_mutations(tmp_path):
    engine,request=fixture(tmp_path,[record()]); row=engine.audit(request)
    validate([row],[request],engine.store,engine.graph)
    steps=json.loads(row['steps_json']);steps[0]['evidence_id']='evidence_99999'
    with pytest.raises(ValueError,match='Unknown evidence'):validate([{**row,'steps_json':json.dumps(steps)}],[request],engine.store,engine.graph)
    steps=json.loads(row['steps_json']);steps.reverse()
    with pytest.raises(ValueError,match='ordering'):validate([{**row,'steps_json':json.dumps(steps)}],[request],engine.store,engine.graph)


def test_trace_join_and_workflow_claim(tmp_path):
    log='2026-01-20T00:00:00Z level=DEBUG service=account_service trace_id=t1 event=profile_lookup_started lookup_key=alex@example.test\n2026-01-20T00:00:01Z level=INFO service=account_service trace_id=t1 event=profile_lookup_completed resource_id=account_90001 rows=1\n'
    engine,request=fixture(tmp_path,[],extra_files=[('evidence_90002','trace.log','2026-01-21T00:00:00Z',log)])
    assert engine.audit(request)['deletion_status']=='INCOMPLETE'


def test_reused_email_is_ambiguous(tmp_path):
    engine,request=fixture(tmp_path,[record()])
    engine.identity.index['alex@example.test'].add('user_90002')
    engine.identity.current['user_90002']['email']='alex@example.test'
    with pytest.raises(ValueError,match='ambiguous'):engine.audit(request)


def test_expired_retention_fails_visibly(tmp_path):
    engine,request=fixture(tmp_path,[record('audit_record_90001','SECURITY_AUDIT_LOG',retention_until='2025-01-01T00:00:00Z')])
    with pytest.raises(ValueError,match='Expired retention'):engine.audit(request)


def test_prior_closed_account_outside_new_request(tmp_path):
    engine,request=fixture(tmp_path,[record('account_90000',state='NOT_FOUND'),record(time='2026-01-25T00:00:00Z')])
    request['requested_at']='2026-01-20T00:00:00Z'
    row=engine.audit(request)
    assert {s['resource_id'] for s in json.loads(row['steps_json'])}=={'account_90001'}


def test_validator_rejects_false_state(tmp_path):
    engine,request=fixture(tmp_path,[record(state='NOT_FOUND')]);row=engine.audit(request)
    steps=json.loads(row['steps_json']);steps[0].update(operation='VERIFY_RECORD_PRESENT',state='PRESENT')
    with pytest.raises(ValueError,match='asserted state'):validate([{**row,'steps_json':json.dumps(steps)}],[request],engine.store,engine.graph)
