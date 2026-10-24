"""Format adapters normalize observations without treating workflow success as state."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
from .models import Observation, Link, Scope, identifiers, RESOURCE, timestamp

COLLECTIONS = {
    'customer_profiles': ('account_service', 'USER_PROFILE'),
    'customer_search_documents': ('search_service', 'SEARCH_INDEX_ENTRY'),
    'search_documents_primary': ('search_service', 'SEARCH_INDEX_ENTRY'),
    'customer_analytics_reports': ('analytics_platform', 'ANALYTICS_PROFILE'),
    'customer_analytics_profiles': ('analytics_platform', 'ANALYTICS_PROFILE'),
    'support_conversations': ('support_platform', 'SUPPORT_MESSAGE'),
    'support_records': ('support_platform', 'SUPPORT_MESSAGE'),
    'ticket_attachments': ('support_platform', 'SUPPORT_ATTACHMENT'),
    'customer_export_jobs': ('export_service', 'USER_EXPORT'),
    'customer_exports': ('export_service', 'USER_EXPORT'),
    'connector_configurations': ('integration_service', 'DATA_FLOW'),
    'connector_subscriptions': ('integration_service', 'DATA_FLOW'),
    'backup_catalog': ('backup_service', 'BACKUP_ARCHIVE'),
    'backup_restore_entries': ('backup_service', 'BACKUP_ARCHIVE'),
    'security_audit_events': ('security_service', 'SECURITY_AUDIT_LOG'),
    'security_audit_records': ('security_service', 'SECURITY_AUDIT_LOG'),
    'retained_order_records': ('finance_service', 'LEGAL_HOLD_RECORD'),
    'deleted_customer_references': ('identity_service', 'ACCOUNT_TOMBSTONE'),
}
PREFIX = {'account': ('account_service', 'USER_PROFILE'), 'search': ('search_service', 'SEARCH_INDEX_ENTRY'),
          'analytics': ('analytics_platform', 'ANALYTICS_PROFILE'), 'support': ('support_platform', 'SUPPORT_MESSAGE'),
          'export': ('export_service', 'USER_EXPORT'), 'data_flow': ('integration_service', 'DATA_FLOW'),
          'backup': ('backup_service', 'BACKUP_ARCHIVE'), 'audit_record': ('security_service', 'SECURITY_AUDIT_LOG'),
          'legal_hold': ('finance_service', 'LEGAL_HOLD_RECORD'), 'tombstone': ('identity_service', 'ACCOUNT_TOMBSTONE'),
          'marketing': ('marketing_service', 'MARKETING_PROFILE'), 'cache': ('cache_service', 'CACHE_ENTRY'),
          'email_delivery': ('email_delivery_service', 'EMAIL_DELIVERY_LOG')}
NULLS = (None, '', 'null', 'None', '[REDACTED]', '[redacted]')


def truth(value):
    return str(value).lower() in ('true', '1', 'yes')


def fields(data):
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (dict, list)): yield from fields(v)
            else: yield k, v
    elif isinstance(data, list):
        for v in data: yield from fields(v)


def exposed(data, include_subject=False):
    keys = {'name', 'full_name', 'display_name', 'email', 'email_hash', 'phone', 'requester_name', 'requester_email', 'requester_phone', 'customer_email', 'owner_email', 'owner_phone'}
    if include_subject: keys |= {'user_id', 'customer_reference', 'subject_reference'}
    if any(k in keys and v not in NULLS for k, v in fields(data)): return True
    return any(k in ('message_text', 'message_excerpt') and identifiers(v) for k, v in fields(data))


def record_state(data, category):
    result = str(data.get('result', '')).upper()
    explicit = {'NOT_FOUND': 'ABSENT', 'FOUND': 'PRESENT', 'IDENTIFIABLE': 'PRESENT', 'REDACTED': 'REDACTED', 'ANONYMIZED': 'ANONYMIZED', 'ACTIVE': 'ACTIVE', 'DISABLED': 'DISABLED', 'BLOCKED': 'BLOCKED', 'RETAINED': 'PRESENT', 'PRESENT': 'PRESENT'}
    if result in explicit: return explicit[result]
    if str(data.get('status_code', data.get('http_status', ''))) == '404': return 'ABSENT'
    if category == 'DATA_FLOW': return 'ACTIVE' if truth(data.get('enabled')) else 'DISABLED'
    if category == 'BACKUP_ARCHIVE': return 'ACTIVE' if truth(data.get('restore_allowed')) else 'BLOCKED'
    if category in ('ANALYTICS_PROFILE', 'PRODUCT_TELEMETRY'): return 'PRESENT' if exposed(data, True) else 'ANONYMIZED'
    if category in ('SUPPORT_MESSAGE', 'EMAIL_DELIVERY_LOG', 'ACCOUNT_TOMBSTONE'): return 'PRESENT' if exposed(data) else 'REDACTED'
    if category == 'SEARCH_INDEX_ENTRY' and isinstance(data.get('hits'), dict) and data['hits'].get('total') == 0: return 'ABSENT'
    return 'PRESENT'


class EvidenceStore:
    def __init__(self, dataset, manifest, cache):
        self.dataset, self.cache = dataset, cache
        self.observations, self.links, self.scopes, self.diagnostics = [], [], [], []
        self.manifest = {r['file_id']: r for r in manifest}
        self.extracted = {}
        for meta in manifest:
            path = dataset / meta['file_path']
            if not path.resolve().is_relative_to(dataset.resolve()): raise ValueError('Manifest path escapes dataset')
            if path.suffix == '.json': self.walk(json.loads(path.read_text(encoding='utf8')), meta)
            elif path.suffix == '.sql': self.sql(path, meta)
            elif path.suffix == '.log': self.logs(path.read_text(encoding='utf8'), meta)
            elif path.suffix == '.txt': self.text(path.read_text(encoding='utf8'), meta)
            elif path.suffix in ('.pdf', '.png'): self.document(path, meta)
            else: raise ValueError(f'Unsupported evidence format: {path}')

    def add(self, data, meta, context=None, location='', replica='primary', state=None):
        context = context or {}
        resource = data.get('resource_id')
        if not resource: return
        default = PREFIX.get(resource.rsplit('_', 1)[0])
        if not default:
            self.diagnostics.append(f'Unrecognized resource at {meta["file_id"]}:{location}'); return
        system, category = COLLECTIONS.get(context.get('collection'), default)
        system = data.get('system', context.get('system', system))
        category = data.get('record_type', context.get('category', category))
        observed = data.get('observed_at', data.get('recorded_at', context.get('time', meta['captured_at'])))
        state = state or record_state(data, category)
        self.observations.append(Observation(resource, system, category, state, observed, meta['captured_at'], meta['file_id'], location, identifiers(data), replica, data))

    def walk(self, data, meta, context=None, location='$'):
        context = dict(context or {})
        if isinstance(data, dict):
            context['time'] = data.get('captured_at', data.get('observed_at', context.get('time', meta['captured_at'])))
            if 'collection' in data: context['collection'] = data['collection']
            if 'data_store' in data and data['data_store'] in {x[0] for x in PREFIX.values()}: context['system'] = data['data_store']
            if 'resource_id' in data:
                self.add(data, meta, context, location); return
            for k, v in data.items():
                child = dict(context)
                if k in {x[0] for x in PREFIX.values()}: child['system'] = k
                self.walk(v, meta, child, location + '.' + k)
        elif isinstance(data, list):
            for i, item in enumerate(data): self.walk(item, meta, context, f'{location}[{i}]')

    def sql(self, path, meta):
        with sqlite3.connect(':memory:') as connection:
            connection.enable_load_extension(False)
            # Evidence snapshots are isolated; deny filesystem attachments and extension loading.
            connection.set_authorizer(lambda action, a, b, db, trigger: sqlite3.SQLITE_DENY if action in (sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH) or (action == sqlite3.SQLITE_FUNCTION and b == 'load_extension') else sqlite3.SQLITE_OK)
            connection.executescript(path.read_text(encoding='utf8'))
            connection.row_factory = sqlite3.Row
            names = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            for table in names:
                if table == 'snapshot_scope': continue
                quoted = '"' + table.replace('"', '""') + '"'
                rows = [dict(r) for r in connection.execute('SELECT * FROM ' + quoted)]
                replica = table if 'replica' in table else 'primary'
                collection = table
                if table.startswith('customer_profiles_'): collection = 'customer_profiles'
                for row in rows:
                    if 'record_json' in row:
                        self.add(json.loads(row['record_json']), meta, {'collection': row['collection_name'], 'system': row['origin_system'], 'time': meta['captured_at']}, f'{table}/{row["resource_id"]}', replica)
                    else:
                        self.add(row, meta, {'collection': collection, 'time': meta['captured_at']}, f'{table}/{row["resource_id"]}', replica)
                if collection in COLLECTIONS:
                    system, category = COLLECTIONS[collection]
                    self.scopes.append(Scope(system, replica, {r['resource_id'] for r in rows}, meta['captured_at'], meta['file_id'], category))

    def logs(self, text, meta):
        contexts = {}
        kv = re.compile(r'(\w+)=(?:"([^"]*)"|([^\s|]+))')
        for number, original in enumerate(text.splitlines(), 1):
            line = original.replace('\\"', '"')
            if not re.match(r'\d{4}-\d\d-\d\dT', line): continue
            time = line.split()[0]
            if line[21:].lstrip().startswith('{'):
                data = json.loads(line[line.index('{'):])
            else:
                data = {m[1]: m[2] if m[2] is not None else m[3] for m in kv.finditer(line)}
                if ' | ' in line:
                    parts = line.split(' | ')
                    if len(parts) >= 6: data.update(service=parts[2], trace_id=parts[3], event=parts[4])
                match = re.search(r'\[\w+\] \[([^]]+)\] \[([^]]+)\] (\w+):', line)
                if match: data.update(service=match[1], trace_id=match[2], event=match[3])
                match = re.search(r'<\d+>1 \S+ (\S+) (\S+) - -', line)
                if match: data.update(service=match[1], trace_id=match[2])
                if 'function' in data: data['service'] = data['function']
                if 'requestId' in data: data['trace_id'] = data['requestId']
            trace = data.get('trace_id')
            previous = contexts.get(trace, {}) if trace else {}
            merged = {**previous, **data}
            if trace: contexts[trace] = merged
            event = data.get('event', '')
            resource = data.get('resource_id')
            if not resource or event.endswith('_started'): continue
            category = None; state = None
            if event == 'record_lookup': category = data['record_type']; state = record_state(data, category)
            elif event == 'profile_lookup_completed': category = 'USER_PROFILE'; state = 'ABSENT' if data.get('rows') == '0' else 'PRESENT'
            elif event == 'index_query_completed': category = 'SEARCH_INDEX_ENTRY'; state = 'ABSENT' if data.get('result') == 'miss' else 'PRESENT'
            elif event in ('contact_lookup_completed', 'contact_query_completed'): category = 'SECONDARY_IDENTIFIER'; state = 'ABSENT' if data.get('rows') == '0' else 'PRESENT'
            elif event == 'attachment_pii_scan': category = 'SUPPORT_ATTACHMENT'; state = 'PRESENT'
            elif event in ('message_pii_scan', 'message_read', 'support_ticket_read_completed'):
                category = 'SUPPORT_MESSAGE'; state = 'PRESENT' if event == 'message_pii_scan' or exposed(data) else 'REDACTED'
            elif event in ('analytics_identity_scan', 'analytics_profile_read', 'analytics_profile_read_completed'):
                category = 'ANALYTICS_PROFILE'; state = 'PRESENT' if event == 'analytics_identity_scan' or exposed(data, True) else 'ANONYMIZED'
            elif event in ('connector_heartbeat', 'connector_config_loaded', 'connector_config_read_completed'):
                category = 'DATA_FLOW'; state = 'ACTIVE' if truth(data.get('enabled')) else 'DISABLED'
            elif event in ('restore_candidate_evaluated', 'restore_authorization_completed', 'restore_policy_read_completed'):
                category = 'BACKUP_ARCHIVE'; state = 'BLOCKED' if data.get('decision') == 'deny' or ('restore_allowed' in data and not truth(data['restore_allowed'])) else 'ACTIVE'
            elif event in ('export_download_check_completed', 'export_metadata_read_completed'): category = 'USER_EXPORT'; state = 'PRESENT' if truth(data.get('available')) else 'ABSENT'
            elif event == 'audit_record_read_completed': category = 'SECURITY_AUDIT_LOG'; state = 'PRESENT'
            if category:
                system = merged.get('system', merged.get('service', ''))
                if system == 'support_replica': system = 'support_platform'
                if system == 'profile_service': system = 'account_service'
                self.add({**merged, 'recorded_at': time, 'record_type': category, 'system': system}, meta, location=f'line {number}; trace {trace}', replica='support_replica' if merged.get('service') == 'support_replica' else 'primary', state=state)

    def text(self, text, meta):
        for number, line in enumerate(text.splitlines(), 1):
            parts = [p.strip() for p in line.removeprefix('- ').split('|')]
            if len(parts) == 6:
                self.add(dict(zip(('recorded_at', 'system', 'resource_id', 'record_type', 'result', 'subject_reference'), parts)), meta, location=f'line {number}')

    def document(self, path, meta):
        if path.suffix == '.pdf':
            import pymupdf
            with pymupdf.open(path) as document:
                pages = [page.get_text() for page in document]
            for i, text in enumerate(pages, 1):
                self.extracted[f'{meta["file_id"]}:page:{i}'] = text
                # Page-level attribution only when a business record carries its own explicit ID.
                if 'Support reference' in text:
                    for resource in set(RESOURCE.findall(text)):
                        if resource.startswith('support_'): self.add({'resource_id': resource, 'text': text, 'record_type': 'SUPPORT_ATTACHMENT'}, meta, location=f'page {i}')
                if 'Event reference' in text:
                    for resource in set(RESOURCE.findall(text)):
                        if resource.startswith('audit_record_'): self.add({'resource_id': resource, 'text': text}, meta, location=f'page {i}')
            if not any(p.strip() for p in pages): raise ValueError(f'PDF has no extractable text: {path}')
        else:
            import pytesseract
            from PIL import Image
            executable = os.environ.get('TESSERACT_CMD') or shutil.which('tesseract')
            if not executable:
                candidate = Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Tesseract-OCR/tesseract.exe'
                if candidate.is_file(): executable = str(candidate)
            if not executable: raise RuntimeError('Tesseract executable missing; set TESSERACT_CMD. Images cannot be treated as empty.')
            pytesseract.pytesseract.tesseract_cmd = executable
            self.cache.mkdir(exist_ok=True)
            digest = hashlib.sha256(path.read_bytes() + b'ocr-psm3-v1').hexdigest()
            cached = self.cache / (digest + '.txt')
            if cached.exists(): text = cached.read_text(encoding='utf8')
            else:
                with Image.open(path) as image: text = pytesseract.image_to_string(image, config='--psm 3', timeout=60)
                cached.write_text(text, encoding='utf8')
            if not text.strip(): raise RuntimeError(f'OCR produced no text: {path}')
            self.extracted[meta['file_id']] = text
            # Only locally co-located identifiers; avoid assigning every table row to the selected user.
            for i, line in enumerate(text.splitlines()):
                resources = RESOURCE.findall(line)
                ids = identifiers(line)
                if resources and ids:
                    for resource in resources:
                        system, category = PREFIX[resource.rsplit('_', 1)[0]]
                        state = 'PRESENT'
                        if category in ('BACKUP_ARCHIVE', 'DATA_FLOW'): continue  # visibility alone cannot prove control state
                        self.add({'resource_id': resource, 'text': line}, meta, location=f'OCR line {i+1}', state=state)
            self.diagnostics.append(f'{meta["file_id"]}: OCR extracted; ambiguous layout/control fields are not asserted')
