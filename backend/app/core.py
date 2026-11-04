import json
import math
import re
import time
import uuid
from datetime import datetime, timezone

from .storage import Store

STATION = 'station-01'
TOPIC = re.compile(r'^[A-Za-z0-9][A-Za-z0-9/_-]{0,119}$')
TRANSITIONS = {
    'investigating': {'awaiting_approval', 'unresolved', 'failed'},
    'awaiting_approval': {'repairing', 'unresolved'},
    'repairing': {'verifying', 'failed'},
    'verifying': {'resolved', 'unresolved', 'failed'},
    'resolved': set(), 'unresolved': set(), 'failed': set(),
}


def utc(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def uid(prefix):
    return f'{prefix}_{uuid.uuid4().hex[:16]}'


class Conflict(ValueError):
    pass


class Engine:
    def __init__(self, store: Store, clock=time.time):
        self.store, self.clock = store, clock
        if not store.get('config', 1):
            self.reset('mismatch')
        # A process restart must not silently leave background jobs running.
        with store.transaction():
            for i in store.all('incidents'):
                if i['state'] in {'investigating', 'repairing', 'verifying', 'awaiting_approval'}:
                    self.transition(i, 'unresolved' if i['state'] != 'repairing' else 'failed',
                                    'Server restarted; previous investigation interrupted. Start a new investigation.')
            self.invalidate_proposals()

    def config(self):
        return self.store.get('config', 1)

    def check_station(self, station):
        if station != STATION:
            raise ValueError('Unknown station')

    def event(self, message):
        self.store.db.execute('INSERT INTO events(observed_at,message) VALUES(?,?)', (self.clock(), message))
        self.store.db.execute('DELETE FROM events WHERE id NOT IN (SELECT id FROM events ORDER BY id DESC LIMIT 200)')

    def invalidate_proposals(self):
        for p in self.store.all('proposals'):
            if p['status'] == 'pending':
                p['status'] = 'invalidated'
                self.store.put('proposals', p['id'], p)

    def reset(self, scenario, topic='stations/river-01/turbidity'):
        if scenario not in {'mismatch', 'healthy', 'sensor_failure', 'unavailable'} or not TOPIC.fullmatch(topic):
            raise ValueError('Invalid simulator configuration')
        with self.store.transaction():
            old = self.config()
            version = old['version'] + 1 if old else 1
            for i in self.store.all('incidents'):
                if i['state'] in {'investigating', 'awaiting_approval', 'verifying', 'repairing'}:
                    self.transition(i, 'failed' if i['state'] == 'repairing' else 'unresolved', 'Demo reset interrupted investigation.')
            self.invalidate_proposals()
            # Sequence remains monotonic across resets. Controls never enter operational logs.
            sequence = old['sequence'] if old else 0
            self.store.db.execute('DELETE FROM samples')
            self.store.db.execute('DELETE FROM events')
            c = dict(version=version, sequence=sequence, publish_topic=topic, subscription_topic=topic,
                     read_failure=False, evidence_unavailable=False, heartbeat=self.clock())
            self.store.put('config', 1, c)
            for offset in (-16, -14, -12, -10):
                self._sample(c, self.clock() + offset)
            if scenario == 'mismatch':
                c['subscription_topic'] = topic + '-old'
            c['read_failure'] = scenario == 'sensor_failure'
            c['evidence_unavailable'] = scenario == 'unavailable'
            self.store.put('config', 1, c)
            self.event('Station connected; sampling interval 2 seconds.')
            self._sample(c, self.clock())

    def _sample(self, c, now):
        c['heartbeat'] = now
        if not c['read_failure']:
            c['sequence'] += 1
            value = round(17.0 + math.sin(c['sequence'] * .42) * 2 + math.cos(c['sequence'] * .19), 2)
            received = now if c['publish_topic'] == c['subscription_topic'] else None
            self.store.db.execute('INSERT INTO samples VALUES(?,?,?,?,?)', (c['sequence'], now, received, value, 'ok'))
            self.store.db.execute('DELETE FROM samples WHERE sequence NOT IN (SELECT sequence FROM samples ORDER BY sequence DESC LIMIT 600)')
        self.store.put('config', 1, c)

    def tick(self):
        with self.store.transaction():
            c = self.config()
            self._sample(c, self.clock())
            for p in self.store.all('proposals'):
                if p['status']=='pending' and datetime.fromisoformat(p['expires_at']).timestamp() <= self.clock():
                    p['status']='expired'
                    self.store.put('proposals',p['id'],p)
                    i=self.store.get('incidents',p['incident_id'])
                    if i['state']=='awaiting_approval':
                        self.transition(i,'unresolved','Proposal expired without approval. No configuration was changed.')

    def samples(self, received=False, limit=40):
        with self.store.lock:
            where = 'WHERE received_at IS NOT NULL' if received else ''
            rows = self.store.db.execute(f'SELECT * FROM samples {where} ORDER BY sequence DESC LIMIT ?', (limit,)).fetchall()
            return [dict(station_id=STATION, sequence=r['sequence'], sampled_at=utc(r['sampled_at']),
                         received_at=utc(r['received_at']) if r['received_at'] is not None else None,
                         value=r['value'], unit='NTU', quality=r['quality']) for r in reversed(rows)]

    def new_incident(self, provider, question):
        with self.store.transaction():
            active = [i for i in self.store.all('incidents') if i['state'] in {'investigating','awaiting_approval','repairing','verifying'}]
            if active:
                raise Conflict('An investigation or proposal is already active. Finish it or reset the demo.')
            i = dict(id=uid('inc'), station_id=STATION, state='investigating', provider=provider,
                     created_at=utc(self.clock()), updated_at=utc(self.clock()), question=question,
                     finding='Collecting diagnostic evidence.', proposal_id=None, repair_at=None,
                     pre_repair_sequence=None, verification=None, model_turns=0, tool_calls=0)
            self.store.put('incidents', i['id'], i)
            return i

    def transition(self, i, state, finding=None):
        if state not in TRANSITIONS[i['state']]:
            raise Conflict(f"Invalid transition {i['state']} -> {state}")
        i['state'], i['updated_at'] = state, utc(self.clock())
        if finding is not None:
            i['finding'] = finding
        self.store.put('incidents', i['id'], i)

    def evidence(self, incident_id, name, status, payload):
        e = dict(evidence_id=uid('ev'), tool_name=name, station_id=STATION, observed_at=utc(self.clock()),
                 status=status, payload=payload)
        with self.store.transaction():
            self.store.db.execute('INSERT INTO evidence VALUES(?,?,?)', (e['evidence_id'], incident_id, json.dumps(e)))
        return e

    def evidence_list(self, incident_id):
        with self.store.lock:
            return [json.loads(r[0]) for r in self.store.db.execute('SELECT body FROM evidence WHERE incident_id=? ORDER BY rowid', (incident_id,))]

    def propose(self, incident_id, topic, version, refs):
        with self.store.transaction():
            c, i = self.config(), self.store.get('incidents', incident_id)
            if i['state'] != 'investigating' or c['version'] != version:
                raise Conflict('Incident or configuration is stale')
            if not TOPIC.fullmatch(topic) or topic == c['subscription_topic']:
                raise ValueError('Proposal must contain a valid, changed subscription topic')
            evidence = self.evidence_list(incident_id)
            by_id = {e['evidence_id']: e for e in evidence}
            if not refs or not set(refs) <= by_id.keys():
                raise ValueError('Proposal requires evidence from this incident')
            referenced = [by_id[r] for r in refs]
            configs = [e for e in referenced if e['tool_name']=='get_transport_config' and e['status']=='ok']
            local = [e for e in referenced if e['tool_name']=='get_local_samples' and e['status']=='ok' and e['payload'].get('samples')]
            received = [e for e in referenced if e['tool_name']=='get_received_samples' and e['status']=='ok']
            if not configs or not local or not received:
                raise ValueError('Need configuration, local samples, and received samples as supporting evidence')
            snapshot = configs[-1]['payload']
            if snapshot['version'] != version or snapshot['publish_topic'] != topic or topic != c['publish_topic']:
                raise ValueError('Proposed topic must match observed publishing configuration')
            # Model latency must not make a still-healthy acquisition path unrepairable.
            # Keep cited observations immutable, but check the current device samples at proposal time.
            cited = local[-1]['payload']['samples'][-1]
            cited_age = self.clock() - datetime.fromisoformat(cited['sampled_at']).timestamp()
            current = self.samples(limit=1)
            current_age = self.clock() - datetime.fromisoformat(current[-1]['sampled_at']).timestamp() if current else float('inf')
            if not 0 <= cited_age <= 120 or not 0 <= current_age <= 6 or c['read_failure'] or c['evidence_unavailable']:
                raise ValueError('Local acquisition is unavailable or stale; recollect diagnostic evidence')
            p = dict(id=uid('prop'), incident_id=incident_id, station_id=STATION,
                     version=version, before=c['subscription_topic'], after=topic, evidence_ids=refs,
                     expires_at=utc(self.clock()+120), status='pending')
            self.store.put('proposals', p['id'], p)
            i['proposal_id'] = p['id']
            self.transition(i, 'awaiting_approval', 'Evidence supports a subscription-topic correction. Technician approval is required.')
            return p

    def decide(self, proposal_id, station, approve):
        self.check_station(station)
        with self.store.transaction():
            p = self.store.get('proposals', proposal_id)
            if not p:
                raise ValueError('Unknown proposal')
            i, c = self.store.get('incidents', p['incident_id']), self.config()
            if p['station_id'] != station or p['status'] != 'pending' or i['state'] != 'awaiting_approval':
                raise Conflict('Proposal is not pending for this station')
            if datetime.fromisoformat(p['expires_at']).timestamp() <= self.clock() or p['version'] != c['version'] or p['before'] != c['subscription_topic']:
                raise Conflict('Proposal expired or configuration changed; investigate again')
            if not approve:
                p['status'] = 'rejected'
                self.store.put('proposals', p['id'], p)
                self.transition(i, 'unresolved', 'Technician rejected the proposal. No configuration was changed.')
                return i
            self.transition(i, 'repairing')
            rows = self.store.db.execute('SELECT MAX(sequence) FROM samples WHERE received_at IS NOT NULL').fetchone()
            i['pre_repair_sequence'], i['repair_at'] = rows[0] or 0, self.clock()
            c['subscription_topic'], c['version'] = p['after'], c['version']+1
            self.store.put('config', 1, c)
            p['status'] = 'approved'
            self.store.put('proposals', p['id'], p)
            self.invalidate_proposals()
            self.event('Technician-approved subscription update applied.')
            self.transition(i, 'verifying', 'Configuration updated. Waiting for three distinct fresh post-repair samples.')
            return i

    def recovery(self, incident_id):
        i = self.store.get('incidents', incident_id)
        if i['repair_at'] is None:
            return dict(recovered=False, count=0, required=3, reason='No approved repair recorded.')
        with self.store.lock:
            rows = self.store.db.execute('''SELECT DISTINCT sequence,sampled_at,received_at FROM samples
                WHERE sequence>? AND sampled_at>? AND received_at>=? AND quality='ok' ORDER BY sequence''',
                (i['pre_repair_sequence'], i['repair_at'], i['repair_at'])).fetchall()
        valid = [r for r in rows if r['sampled_at'] <= r['received_at'] <= self.clock() and r['sampled_at'] <= self.clock()]
        fresh = bool(valid) and 0 <= self.clock()-valid[-1]['sampled_at'] <= 6
        return dict(recovered=len(valid)>=3 and fresh, count=len(valid), required=3, latest_fresh=fresh,
                    reason='Three distinct post-repair samples and latest freshness required.')

    def verify_step(self, incident_id):
        with self.store.transaction():
            i = self.store.get('incidents', incident_id)
            if i['state'] != 'verifying':
                return True
            result = self.recovery(incident_id)
            i['verification'] = result
            if result['recovered']:
                self.transition(i, 'resolved', 'Recovery verified: three distinct post-repair samples received; latest sample is fresh.')
                return True
            if self.clock()-i['repair_at'] >= 20:
                self.transition(i, 'unresolved', 'Recovery verification timed out. Configuration write does not prove recovery.')
                return True
            self.store.put('incidents', i['id'], i)
            return False
