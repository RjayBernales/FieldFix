"""Authenticated hosting and global budget tests use mocked HTTP, never live Meta."""
import asyncio
from contextlib import asynccontextmanager

import httpx
import pytest

import app.hosted as module
from app.agent import MetaProvider
from app.settings import Settings

CODE = 'test-access-code-for-hosting-only'
KEY = 'fixture-key-not-a-real-secret'


def settings(tmp_path, limit=1):
    return Settings(_env_file=None, FIELDFIX_PROVIDER='meta', MODEL_API_KEY=KEY,
                    FIELDFIX_DB=str(tmp_path/'budget.sqlite'), FIELDFIX_LIVE_REQUEST_LIMIT=limit)


@asynccontextmanager
async def live(tmp_path, monkeypatch, **kwargs):
    static=tmp_path/'dist';static.mkdir(exist_ok=True);(static/'index.html').write_text('<h1>Demo</h1>')
    def response(_):
        return httpx.Response(200,json={'choices':[{'message':{'role':'assistant','content':'Evidence unavailable.'}}]})
    monkeypatch.setattr(module,'MetaProvider',lambda s,e,**kw:MetaProvider(s,e,httpx.MockTransport(response),**kw))
    limit=kwargs.pop('limit',1)
    app=module.create_live_demo_app(settings=settings(tmp_path,limit), origin='https://live.example',
        static_dir=static,data_dir=tmp_path/'sessions',access_code=CODE,**kwargs)
    async with app.site.router.lifespan_context(app.site):
        transport=httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport,base_url='https://live.example',headers={'Origin':'https://live.example'}) as client:
            yield app,client,transport


def test_live_factory_fails_closed_without_explicit_mode_key_and_access_code(tmp_path):
    for s,code in [(Settings(_env_file=None,FIELDFIX_PROVIDER='mock'),CODE),
                   (Settings(_env_file=None,FIELDFIX_PROVIDER='meta',MODEL_API_KEY=''),CODE),
                   (settings(tmp_path),'short')]:
        with pytest.raises(RuntimeError):
            module.create_live_demo_app(settings=s,origin='https://live.example',static_dir=tmp_path,access_code=code)


def test_live_login_required_and_mode_truthful_without_leaking_secrets(tmp_path,monkeypatch):
    async def check():
        async with live(tmp_path,monkeypatch) as (app,c,_):
            assert (await c.get('/healthz')).json()['provider']=='meta'
            status=(await c.get('/api/session')).json()
            assert status['provider']=='meta' and status['requires_access_code'] and not status['authenticated']
            assert (await c.get('/api/health')).status_code==401
            for body in [{},{'access_code':'wrong'},{'access_code':123},[]]:
                assert (await c.post('/api/session',json=body)).status_code==401
            assert not app.sessions
            assert (await c.post('/api/session',headers={'Origin':'https://evil.example'},json={'access_code':CODE})).status_code==403
            r=await c.post('/api/session',json={'access_code':CODE});assert r.status_code==201
            assert r.json()['provider']=='meta' and 'Secure' in r.headers['set-cookie']
            h=await c.get('/api/health');assert h.json()['provider']=='meta'
            assert KEY not in h.text and CODE not in h.text
            ended=(await c.post('/api/session/end',json={})).json()
            assert ended['provider']=='meta' and ended['requires_access_code'] and not ended['authenticated']
    asyncio.run(check())


async def incident(c):
    i=(await c.post('/api/incidents',json={})).json()
    for _ in range(100):
        detail=(await c.get('/api/incidents/'+i['id'])).json()
        if detail['state']!='investigating':return detail
        await asyncio.sleep(.01)
    raise AssertionError('Mocked HTTP investigation did not finish')


def test_live_budget_shared_across_visitors_and_survives_restart(tmp_path,monkeypatch):
    async def check():
        async with live(tmp_path,monkeypatch) as (app,a,transport):
            await a.post('/api/session',json={'access_code':CODE})
            first=await incident(a)
            assert len(first['inference'])==1
            assert app.budget_store.db.execute('SELECT count(*) FROM inference').fetchone()[0]==1
            async with httpx.AsyncClient(transport=transport,base_url='https://live.example',headers={'Origin':'https://live.example'}) as b:
                await b.post('/api/session',json={'access_code':CODE})
                assert (await b.get('/api/incidents/'+first['id'])).status_code==404
                assert (await b.get('/api/health')).json()['live_requests_used']==1
                blocked=await incident(b)
                assert blocked['state']=='failed' and 'budget exhausted' in blocked['finding'] and not blocked['inference']
                assert (await a.get('/api/health')).json()['live_requests_used']==1
        async with live(tmp_path,monkeypatch) as (_,c,_):
            await c.post('/api/session',json={'access_code':CODE})
            assert (await c.get('/api/health')).json()['live_requests_used']==1
            assert (await incident(c))['state']=='failed'
    asyncio.run(check())


def test_live_login_attempts_bounded(tmp_path,monkeypatch):
    async def check():
        async with live(tmp_path,monkeypatch) as (app,c,_):
            for _ in range(12):
                assert (await c.post('/api/session',json={'access_code':'wrong'})).status_code==401
            assert (await c.post('/api/session',json={'access_code':CODE})).status_code==429
            assert not app.sessions
    asyncio.run(check())


def test_public_judging_session_needs_no_code_but_api_needs_cookie(tmp_path,monkeypatch):
    async def check():
        async with live(tmp_path,monkeypatch,public_live=True) as (app,c,_):
            status=(await c.get('/api/session')).json()
            assert status['provider']=='meta' and status['public_live'] and not status['requires_access_code']
            assert (await c.get('/api/health')).status_code==401
            assert (await c.post('/api/session',json={})).status_code==201
            assert (await c.get('/api/health')).json()['provider']=='meta'
            assert not app.requires_access_code
    asyncio.run(check())


def test_judging_mode_and_origin_use_validated_local_settings(tmp_path):
    configured=settings(tmp_path).model_copy(update={'public_live':True,'public_origin':'https://judging.example'})
    app=module.create_live_demo_app(settings=configured,static_dir=tmp_path,access_code='')
    assert app.public_live and not app.requires_access_code and app.origin=='https://judging.example'
    app.budget_store.close()


def test_public_judging_quota_survives_station_reset(tmp_path,monkeypatch):
    async def check():
        async with live(tmp_path,monkeypatch,public_live=True,limit=10) as (_,c,_):
            await c.post('/api/session',json={})
            await incident(c)
            await c.post('/api/demo/reset',json={'scenario':'mismatch'})
            await incident(c)
            await c.post('/api/demo/reset',json={'scenario':'mismatch'})
            r=await c.post('/api/incidents',json={})
            assert r.status_code==429 and 'two live investigations' in r.json()['detail']
            assert (await c.get('/api/health')).json()['live_requests_used']==2
    asyncio.run(check())


def test_exhausted_public_budget_rejects_without_creating_incident(tmp_path,monkeypatch):
    async def check():
        async with live(tmp_path,monkeypatch,public_live=True) as (app,c,_):
            with app.budget_store.transaction():
                app.budget_store.db.execute('UPDATE budget SET used=1')
            await c.post('/api/session',json={})
            r=await c.post('/api/incidents',json={})
            assert r.status_code==429 and 'budget is exhausted' in r.json()['detail']
            assert (await c.get('/api/incidents')).json()==[]
    asyncio.run(check())
