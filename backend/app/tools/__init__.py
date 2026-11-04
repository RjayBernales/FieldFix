"""Allowlisted tools; simulator controls are deliberately absent."""
import json
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

from ..core import STATION


class StationArgs(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    station_id: str


class SampleArgs(StationArgs):
    limit: int = Field(default=12, ge=1, le=40)


class ProposalArgs(StationArgs):
    subscription_topic: str = Field(min_length=1, max_length=120, pattern=r'^[A-Za-z0-9][A-Za-z0-9/_-]*$')
    expected_version: int = Field(ge=1)
    evidence_ids: list[Annotated[str, Field(max_length=40)]] = Field(min_length=3, max_length=12)


TOOLS = {
    'get_station_status': (StationArgs, 'Read device connection and last heartbeat.'),
    'get_local_samples': (SampleArgs, 'Read recent local device samples with original sampling timestamps.'),
    'get_received_samples': (SampleArgs, 'Read recent dashboard-delivered samples with original timestamps.'),
    'get_device_logs': (StationArgs, 'Read bounded operational device events.'),
    'get_transport_config': (StationArgs, 'Read publishing/subscription topics and configuration version.'),
    'propose_subscription_update': (ProposalArgs, 'Propose an exact subscription correction supported by configuration, local, and received evidence. Never applies a repair.'),
    'verify_recovery': (StationArgs, 'Read deterministic recovery status for this incident. Does not change state.'),
}


def schemas():
    return [dict(type='function', function=dict(name=n, description=desc, parameters=model.model_json_schema()))
            for n, (model, desc) in TOOLS.items()]


def execute(engine, incident_id, name, arguments):
    if name not in TOOLS:
        return engine.evidence(incident_id, 'unknown_tool', 'error', {'error': 'Tool is not allowlisted.'})
    try:
        if len(arguments) > 12000:
            raise ValueError()
        args = TOOLS[name][0].model_validate(json.loads(arguments))
        engine.check_station(args.station_id)
    except (ValueError, TypeError):
        return engine.evidence(incident_id, name, 'error', {'error': 'Invalid tool arguments or station.'})
    c = engine.config()
    if c['evidence_unavailable'] and name in {'get_local_samples', 'get_received_samples', 'get_transport_config'}:
        return engine.evidence(incident_id, name, 'unavailable', {'error': 'Diagnostic access unavailable.'})
    status = 'ok'
    try:
        if name == 'get_station_status':
            from ..core import utc
            payload = dict(connected=engine.clock()-c['heartbeat'] <= 6, last_heartbeat=utc(c['heartbeat']))
        elif name == 'get_local_samples':
            if c['read_failure']:
                status, payload = 'error', dict(error='Local acquisition read failed. Physical inspection required.')
            else:
                payload = dict(samples=engine.samples(limit=args.limit))
        elif name == 'get_received_samples':
            payload = dict(samples=engine.samples(received=True, limit=args.limit))
        elif name == 'get_device_logs':
            from ..core import utc
            with engine.store.lock:
                rows = engine.store.db.execute('SELECT observed_at,message FROM events ORDER BY id DESC LIMIT 20').fetchall()
            payload = dict(events=[dict(observed_at=utc(r[0]), message=r[1]) for r in reversed(rows)])
        elif name == 'get_transport_config':
            payload = {k: c[k] for k in ('publish_topic', 'subscription_topic', 'version')}
        elif name == 'propose_subscription_update':
            payload = engine.propose(incident_id, args.subscription_topic, args.expected_version, args.evidence_ids)
        else:
            payload = engine.recovery(incident_id)
    except ValueError as exc:
        status, payload = 'error', dict(error=str(exc))
    return engine.evidence(incident_id, name, status, payload)
