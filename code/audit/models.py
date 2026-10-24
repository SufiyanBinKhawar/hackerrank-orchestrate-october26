from dataclasses import dataclass, field
from datetime import datetime, timezone
import csv
import re
import unicodedata


def timestamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError(f'Timezone required: {value}')
    return result.astimezone(timezone.utc)


def normalize(value):
    return unicodedata.normalize('NFKC', str(value)).strip().casefold()


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


TOKEN = re.compile(r'(?<![\w.@+-])(?:[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}|user_\d+|[a-fA-F0-9]{64})(?![\w@+-])')
RESOURCE = re.compile(r'\b(?:account|analytics|search|support|export|data_flow|backup|audit_record|legal_hold|tombstone|cache|marketing|email_delivery)_\d+\b')


def identifiers(data):
    """Exact tokens only; names and resource-number similarities are never identities."""
    if isinstance(data, dict):
        values = set().union(*(identifiers(v) for k, v in data.items() if k not in {'resource_id', 'source_resource_id'}))
        for k, v in data.items():
            if k in ('phone', 'owner_phone', 'requester_phone') and v and str(v).startswith('+'):
                values.add(re.sub(r'[^\d+]', '', str(v)))
        return values
    if isinstance(data, list):
        return set().union(*(identifiers(v) for v in data)) if data else set()
    return {normalize(m.group()) for m in TOKEN.finditer(str(data))}


@dataclass
class Observation:
    resource: str
    system: str
    category: str
    state: str
    observed_at: str
    captured_at: str
    evidence: str
    location: str
    identifiers: set = field(default_factory=set)
    replica: str = 'primary'
    attributes: dict = field(default_factory=dict)

    def available(self, cutoff):
        return timestamp(self.captured_at) <= cutoff and timestamp(self.observed_at) <= cutoff


@dataclass
class Link:
    resource: str
    identifiers: set
    observed_at: str
    captured_at: str
    evidence: str


@dataclass
class Scope:
    system: str
    replica: str
    resources: set
    captured_at: str
    evidence: str
    category: str = 'USER_PROFILE'
