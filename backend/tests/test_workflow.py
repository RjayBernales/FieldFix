import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

import pytest
import httpx

from app.agent import MockProvider, investigate
from app.core import Conflict, Engine, STATION
from app.main import create_app
from app.settings import Settings
from app.tools import execute


def proposal(e, topic='stations/varied-92/sediment'):
    e.reset('mismatch', topic)
    i = e.new_incident('mock', 'Investigate stale samples.')
    asyncio.run(investigate(e, i['id'], MockProvider()))
    i = e.store.get('incidents', i['id'])
    assert i['state']=='awaiting_approval'
    return e.store.get('proposals', i['proposal_id'])


def test_topic_router_independent_of_agent(engine):
    before = engine.samples(True)[-1]
    engine.clock.advance(); engine.tick()
    assert engine.samples()[-1]['sequence']>before['sequence']
    assert engine.samples(True)[-1]==before
    assert engine.config()['publish_topic'] != engine.config()['subscription_topic']


def test_full_approval_and_verified_recovery(engine):
    p = proposal(engine)
    assert engine.config()['subscription_topic']==p['before']
    i = engine.decide(p['id'], STATION, True)
    assert i['state']=='verifying'
    assert not engine.verify_step(i['id'])
    for expected in (1,2,3):
        engine.clock.advance(); engine.tick()
        done=engine.verify_step(i['id'])
        assert done == (expected==3)
    assert engine.store.get('incidents',i['id'])['state']=='resolved'
    assert engine.config()['subscription_topic']==p['after']


@pytest.mark.parametrize('approve',[True,False])
def test_replayed_decisions_blocked(engine,approve):
    p=proposal(engine);engine.decide(p['id'],STATION,approve)
    with pytest.raises(Conflict):engine.decide(p['id'],STATION,approve)


def test_reject_and_no_approval_never_write(engine):
    p=proposal(engine);before=engine.config()
    engine.clock.advance(10);engine.tick()
    assert engine.config()['subscription_topic']==before['subscription_topic']
    engine.decide(p['id'],STATION,False)
    assert engine.config()['version']==before['version']
    assert engine.store.get('incidents',p['incident_id'])['state']=='unresolved'


def test_expired_proposal_cannot_apply(engine):
    p=proposal(engine);engine.clock.advance(121)
    with pytest.raises(Conflict):engine.decide(p['id'],STATION,True)
    assert engine.config()['subscription_topic']==p['before']


def test_wrong_station_cannot_apply(engine):
    p=proposal(engine)
    with pytest.raises(ValueError):engine.decide(p['id'],'station-other',True)
    assert engine.config()['subscription_topic']==p['before']


def test_stale_version_cannot_apply(engine):
    p=proposal(engine)
    with engine.store.transaction():
        c=engine.config();c['version']+=1;engine.store.put('config',1,c)
    with pytest.raises(Conflict):engine.decide(p['id'],STATION,True)


def test_reset_invalidates_approval(engine):
    p=proposal(engine);sequence=engine.config()['sequence'];engine.reset('healthy')
    with pytest.raises(Conflict):engine.decide(p['id'],STATION,True)
    assert engine.config()['sequence']>sequence
    assert engine.store.get('incidents',p['incident_id'])['state']=='unresolved'


def test_concurrent_approval_has_one_write(engine):
    p=proposal(engine)
    def approve():
        try: engine.decide(p['id'],STATION,True);return 'ok'
        except Conflict:return 'conflict'
    with ThreadPoolExecutor(2) as pool:results=list(pool.map(lambda _:approve(),range(2)))
    assert sorted(results)==['conflict','ok']
    assert engine.config()['version']==p['version']+1


@pytest.mark.parametrize('scenario',['healthy','sensor_failure','unavailable'])
def test_secondary_outcomes_do_not_propose(engine,scenario):
    engine.reset(scenario)
    i=engine.new_incident('mock','Inspect this station.')
    asyncio.run(investigate(engine,i['id'],MockProvider()))
    result=engine.store.get('incidents',i['id'])
    assert result['state']=='unresolved' and result['proposal_id'] is None
    assert ('No fault found' in result['finding'])==(scenario=='healthy')


def test_evidence_boundary(engine):
    p=proposal(engine)
    evidence=engine.evidence_list(p['incident_id'])
    serialized=json.dumps(evidence)
    for forbidden in ('mismatch','scenario','read_failure','evidence_unavailable','expected_answer'):
        assert forbidden not in serialized
    for e in evidence:
        assert {'evidence_id','station_id','observed_at','status','tool_name','payload'}<=e.keys()


@pytest.mark.parametrize('name,args',[
 ('run_shell',{'command':'anything'}),('get_local_samples',{'station_id':STATION,'limit':100}),
 ('get_station_status',{'station_id':'other'}),('get_transport_config',{'station_id':STATION,'scenario':'mismatch'}),
 ('get_local_samples',{'station_id':STATION,'limit':'3'}),
])
def test_invalid_tools_are_structured_errors(engine,name,args):
    i=engine.new_incident('mock','inspect')
    assert execute(engine,i['id'],name,json.dumps(args))['status']=='error'


def test_malformed_json(engine):
    i=engine.new_incident('mock','inspect')
    assert execute(engine,i['id'],'get_local_samples','{bad')['status']=='error'


def test_proposal_requires_real_evidence(engine):
    i=engine.new_incident('mock','inspect')
    with pytest.raises(ValueError):engine.propose(i['id'],'stations/a',engine.config()['version'],['fake'])


def test_recovery_rejects_pre_repair_duplicate_cached_and_stale(engine):
    p=proposal(engine);i=engine.decide(p['id'],STATION,True)
    # Existing received samples cannot count; a sample at the exact repair instant cannot count.
    engine.tick();assert engine.recovery(i['id'])['count']==0
    engine.clock.advance();engine.tick()
    row=engine.samples(True)[-1]
    assert engine.recovery(i['id'])['count']==1
    with pytest.raises(Exception):
        with engine.store.transaction():
            engine.store.db.execute('INSERT INTO samples VALUES(?,?,?,?,?)',(row['sequence'],engine.clock(),engine.clock(),1,'ok'))
    engine.clock.advance();engine.tick();engine.clock.advance();engine.tick()
    assert engine.recovery(i['id'])['recovered']
    engine.clock.advance(7)
    assert not engine.recovery(i['id'])['recovered']


def test_cached_timestamp_with_new_sequence_cannot_count(engine):
    p=proposal(engine);i=engine.decide(p['id'],STATION,True)
    with engine.store.transaction():
        for n in range(3):
            engine.store.db.execute('INSERT INTO samples VALUES(?,?,?,?,?)',(900+n,i['repair_at']-1,engine.clock(),10,'ok'))
    assert engine.recovery(i['id'])['count']==0


def test_failed_repair_times_out_unresolved(engine):
    p=proposal(engine);i=engine.decide(p['id'],STATION,True)
    with engine.store.transaction():
        c=engine.config();c['publish_topic']='stations/changed';engine.store.put('config',1,c)
    engine.clock.advance(20);engine.tick()
    assert engine.verify_step(i['id'])
    assert engine.store.get('incidents',i['id'])['state']=='unresolved'


def test_restart_marks_interrupted_jobs(engine):
    p=proposal(engine)
    restarted=Engine(engine.store,engine.clock)
    assert restarted.store.get('incidents',p['incident_id'])['state']=='unresolved'
    with pytest.raises(Conflict):restarted.decide(p['id'],STATION,True)


def test_model_cannot_set_resolved(engine):
    i=engine.new_incident('mock','inspect')
    with pytest.raises(Conflict):engine.transition(i,'resolved')


def test_api_local_security_and_missing_key(engine):
    async def check():
        settings=Settings(_env_file=None,FIELDFIX_PROVIDER='meta',MODEL_API_KEY='',FIELDFIX_ENABLE_DEMO=False)
        app=create_app(settings,engine)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://127.0.0.1') as client:
                assert (await client.get('/health')).json()['provider']=='meta'
                assert (await client.post('/incidents',json={'station_id':STATION})).status_code==503
                assert (await client.post('/demo/reset',json={})).status_code==404
                assert (await client.post('/incidents',headers={'Origin':'https://evil.example'},json={})).status_code==403
                assert (await client.get('/health',headers={'Host':'evil.example'})).status_code==403
                assert (await client.get('/stations/other/samples')).status_code==400
                assert 'api_key' not in json.dumps((await client.get('/health')).json())
    asyncio.run(check())


def test_api_investigation_approval_and_history(engine):
    async def check():
        app=create_app(Settings(_env_file=None),engine)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://127.0.0.1') as client:
                r=await client.post('/incidents',json={'station_id':STATION});assert r.status_code==202
                id=r.json()['id']
                for _ in range(50):
                    i=(await client.get('/incidents/'+id)).json()
                    if i['state']!='investigating':break
                    await asyncio.sleep(.01)
                assert i['state']=='awaiting_approval'
                assert (await client.post('/incidents',json={})).status_code==409
                assert (await client.post('/proposals/'+i['proposal']['id']+'/approve',json={'station_id':STATION})).status_code==200
                for _ in range(3):engine.clock.advance();engine.tick()
                engine.verify_step(id)
                assert (await client.get('/incidents/'+id)).json()['state']=='resolved'
                assert (await client.get('/incidents')).json()[0]['id']==id
    asyncio.run(check())


def test_expired_proposal_becomes_unresolved_on_tick(engine):
    p=proposal(engine);version=engine.config()['version']
    engine.clock.advance(121);engine.tick()
    assert engine.store.get('proposals',p['id'])['status']=='expired'
    assert engine.store.get('incidents',p['incident_id'])['state']=='unresolved'
    assert engine.config()['version']==version


def test_stale_evidence_cannot_propose(engine):
    i=engine.new_incident('mock','inspect')
    refs=[execute(engine,i['id'],n,json.dumps({'station_id':STATION}))['evidence_id'] for n in ('get_local_samples','get_received_samples','get_transport_config')]
    engine.clock.advance(7)
    with pytest.raises(ValueError,match='stale'):engine.propose(i['id'],engine.config()['publish_topic'],engine.config()['version'],refs)


def test_active_investigation_can_be_cancelled(engine):
    from app.agent import investigate
    class Waiting:
        def __init__(self):self.cancelled=False
        async def complete(self,messages,id):
            try:await asyncio.sleep(100)
            except asyncio.CancelledError:self.cancelled=True;raise
    async def check():
        provider=Waiting();app=create_app(Settings(_env_file=None),engine,provider)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://127.0.0.1') as client:
                id=(await client.post('/incidents',json={})).json()['id']
                await asyncio.sleep(.01)
                assert (await client.post('/incidents/'+id+'/cancel')).status_code==200
                await asyncio.sleep(.01)
                assert provider.cancelled
                assert (await client.get('/incidents/'+id)).json()['state']=='unresolved'
    asyncio.run(check())


def test_bounded_requests_and_unknown_incidents(engine):
    async def check():
        app=create_app(Settings(_env_file=None),engine)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://127.0.0.1') as client:
                assert (await client.post('/incidents',content='x'*16001)).status_code==413
                assert (await client.get('/health',headers={'Content-Length':'invalid'})).status_code==400
                assert (await client.get('/incidents/missing')).status_code==404
                assert (await client.post('/incidents',json={'question':'x'*1001})).status_code==422
    asyncio.run(check())


def test_model_latency_does_not_invalidate_current_fresh_acquisition(engine):
    i=engine.new_incident('meta','inspect')
    refs=[execute(engine,i['id'],n,json.dumps({'station_id':STATION}))['evidence_id'] for n in ('get_local_samples','get_received_samples','get_transport_config')]
    engine.clock.advance(10);engine.tick()
    p=engine.propose(i['id'],engine.config()['publish_topic'],engine.config()['version'],refs)
    assert p['status']=='pending'
    assert p['evidence_ids']==refs
    assert engine.config()['subscription_topic']==p['before']


def test_recent_cached_samples_do_not_hide_current_acquisition_failure(engine):
    i=engine.new_incident('meta','inspect')
    refs=[execute(engine,i['id'],n,json.dumps({'station_id':STATION}))['evidence_id'] for n in ('get_local_samples','get_received_samples','get_transport_config')]
    with engine.store.transaction():
        c=engine.config();c['read_failure']=True;engine.store.put('config',1,c)
    with pytest.raises(ValueError,match='unavailable or stale'):
        engine.propose(i['id'],c['publish_topic'],c['version'],refs)
