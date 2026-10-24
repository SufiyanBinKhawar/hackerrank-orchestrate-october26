from .models import RESOURCE, timestamp


def analyze_dependencies(activity, resources, cutoff, graph):
    """Keep only subject-grounded flows; activity describes attempts, never final state."""
    events = []
    for event in activity:
        if timestamp(event['event_time']) > cutoff: continue
        touched = set(RESOURCE.findall(event['details'])) | {event['resource_id']}
        if not touched.intersection(resources): continue
        if event['event_type'] in ('SYNC_RECORD', 'RESTORE_BACKUP', 'INDEX_RECORD', 'DISABLE_DATA_FLOW', 'BLOCK_RESTORE'):
            events.append(event)
    return events
