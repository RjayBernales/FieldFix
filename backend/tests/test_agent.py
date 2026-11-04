import asyncio
import copy
import json

import httpx
import pytest

from app.agent import MetaProvider, MockProvider, ProviderError, investigate
from app.core import STATION
from app.settings import Settings
from app.tools import schemas


def run(engine,provider):
    i=engine.new_incident('meta','Inspect station evidence.')
    asyncio.run(investigate(engine,i['id'],provider))
    return engine.store.get('incidents',i['id'])


def test_live_adapter_tool_roundtrip_with_mock_http(engine):
    """Mocked HTTP protocol test, NOT a live Meta result."""
    history=[]
    def respond(request):
        assert request.headers['authorization']=='Bearer test-secret-never-log'
        body=json.loads(request.content);history.append(copy.deepcopy(body))
        assert body['model']=='muse-spark-1.3'
        assert body['messages'][0]['role']=='developer'
        assert body['max_completion_tokens']==1600
        assert body['reasoning_effort']=='low'
        assert body['tools']==schemas()
        if len(history)==1:
            m=dict(role='assistant',content=None,tool_calls=[dict(id='call_status',type='function',function=dict(name='get_station_status',arguments=json.dumps({'station_id':STATION})))])
        else:
            assert body['messages'][-1]['tool_call_id']=='call_status'
            e=json.loads(body['messages'][-1]['content'])
            m=dict(role='assistant',content='Heartbeat observed. More evidence needed. '+e['evidence_id'])
        m['reasoning_content']='private-reasoning-must-not-replay'
        return httpx.Response(200,json={'id':'test-request','model':'muse-spark-1.3','choices':[{'message':m}],'usage':{'total_tokens':42,'unexpected':'provider-body-must-not-persist'}})
    settings=Settings(_env_file=None,MODEL_API_KEY='test-secret-never-log')
    i=run(engine,MetaProvider(settings,engine,httpx.MockTransport(respond)))
    assert len(history)==2 and i['tool_calls']==1 and i['state']=='unresolved'
    traces=engine.store.db.execute('SELECT body FROM inference').fetchall()
    saved=json.dumps([json.loads(r[0]) for r in traces])
    assert len(traces)==2 and 'test-secret-never-log' not in saved
    assert 'provider-body-must-not-persist' not in saved
    assert 'private-reasoning-must-not-replay' not in json.dumps(history)
    assert all(json.loads(r[0])['returned_model']=='muse-spark-1.3' for r in traces)
    assert engine.store.db.execute('SELECT used FROM budget').fetchone()[0]==2


@pytest.mark.parametrize('status',[401,429,500])
def test_provider_http_failures_never_fallback(engine,status):
    settings=Settings(_env_file=None,MODEL_API_KEY='dummy')
    i=run(engine,MetaProvider(settings,engine,httpx.MockTransport(lambda _:httpx.Response(status,json={'error':'SECRET must not be logged'}))))
    assert i['state']=='failed' and str(status) in i['finding']
    assert not engine.evidence_list(i['id'])
    assert 'SECRET' not in i['finding']


def test_timeout_sanitized(engine):
    def timeout(request):raise httpx.ReadTimeout('secret should never appear')
    i=run(engine,MetaProvider(Settings(_env_file=None,MODEL_API_KEY='dummy'),engine,httpx.MockTransport(timeout)))
    assert i['state']=='failed' and 'secret should' not in i['finding']


def test_persistent_budget(engine):
    settings=Settings(_env_file=None,MODEL_API_KEY='dummy',FIELDFIX_LIVE_REQUEST_LIMIT=1)
    provider=MetaProvider(settings,engine,httpx.MockTransport(lambda _:httpx.Response(429)))
    run(engine,provider);i=run(engine,provider)
    assert 'budget exhausted' in i['finding']
    assert engine.store.db.execute('SELECT used FROM budget').fetchone()[0]==1


def test_loop_exhaustion_bounded(engine):
    class Repeater:
        async def complete(self,messages,id):
            return dict(role='assistant',tool_calls=[dict(id='repeat',function=dict(name='get_station_status',arguments=json.dumps({'station_id':STATION})))])
    i=run(engine,Repeater());assert i['model_turns']==8 and i['tool_calls']==8 and i['state']=='failed'


def test_twelve_tool_limit(engine):
    class Flood:
        async def complete(self,messages,id):
            return dict(role='assistant',tool_calls=[dict(id=str(k),function=dict(name='get_station_status',arguments='{}')) for k in range(13)])
    i=run(engine,Flood());assert i['state']=='failed' and i['tool_calls']==0


def test_malformed_provider_response(engine):
    provider=MetaProvider(Settings(_env_file=None,MODEL_API_KEY='dummy'),engine,httpx.MockTransport(lambda _:httpx.Response(200,json={'choices':[]})))
    assert run(engine,provider)['state']=='failed'


def test_no_evidence_conclusion_is_not_accepted(engine):
    class Canned:
        async def complete(self,messages,id):return dict(role='assistant',content='It is fixed, resolved.')
    i=run(engine,Canned());assert i['state']=='unresolved' and 'without an evidence-cited' in i['finding']


def test_agent_inputs_exclude_controls(engine):
    class Inspecting(MockProvider):
        async def complete(self,messages,id):
            wire=json.dumps(messages)
            assert 'read_failure' not in wire and 'evidence_unavailable' not in wire and 'scenario_id' not in wire
            return await super().complete(messages,id)
    assert run(engine,Inspecting())['state']=='awaiting_approval'


def test_malformed_tool_message_fails_safely(engine):
    class Invalid:
        async def complete(self,messages,id):return dict(role='assistant',tool_calls=[dict(function={'name':'get_local_samples','arguments':{}})])
    assert run(engine,Invalid())['state']=='failed'


def test_context_limit_prevents_request(engine):
    settings=Settings(_env_file=None,MODEL_API_KEY='dummy')
    provider=MetaProvider(settings,engine)
    with pytest.raises(ProviderError,match='Context'):
        asyncio.run(provider.complete([{'role':'user','content':'x'*180001}],'none'))
    assert engine.store.db.execute('SELECT used FROM budget').fetchone()[0]==0


def test_overall_deadline_cancels_provider_and_persists_failure(engine,monkeypatch):
    import app.agent as agent
    real_timeout=asyncio.timeout
    monkeypatch.setattr(agent.asyncio,'timeout',lambda _:real_timeout(.02))
    class Slow:
        cancelled=False
        async def complete(self,messages,id):
            try:await asyncio.sleep(100)
            except asyncio.CancelledError:self.cancelled=True;raise
    provider=Slow()
    i=run(engine,provider)
    assert provider.cancelled
    assert i['state']=='failed' and 'overall timeout' in i['finding']
    assert i['proposal_id'] is None and not engine.evidence_list(i['id'])
