import asyncio
from contextlib import asynccontextmanager

import httpx
import pytest

from app.hosted import create_hosted_app


@asynccontextmanager
async def hosted(tmp_path, **kwargs):
    static=tmp_path/'dist';static.mkdir(exist_ok=True);(static/'index.html').write_text('<h1>FieldFix test</h1>')
    app=create_hosted_app(origin='https://demo.example',static_dir=str(static),data_dir=tmp_path/'sessions',**kwargs)
    async with app.site.router.lifespan_context(app.site):
        transport=httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport,base_url='https://demo.example',headers={'Origin':'https://demo.example'}) as client:
            yield app,client,transport


def test_anonymous_api_requires_session_and_cookie_is_secure(tmp_path,monkeypatch):
    monkeypatch.delenv('MODEL_API_KEY',raising=False);monkeypatch.setenv('FIELDFIX_PROVIDER','mock')
    async def check():
        async with hosted(tmp_path) as (app,c,_):
            assert (await c.get('/api/health')).status_code==401
            assert (await c.get('/api/session')).json()['authenticated'] is False
            r=await c.post('/api/session',json={});assert r.status_code==201
            cookie=r.headers['set-cookie'];assert 'HttpOnly' in cookie and 'Secure' in cookie and 'SameSite=strict' in cookie
            h=(await c.get('/api/health')).json();assert h['provider']=='mock' and not h['credentials_configured'] and h['live_request_limit']==0
            assert (await c.get('/')).status_code==200
            assert (await c.post('/api/session/end',json={})).status_code==200
            assert (await c.get('/api/incidents')).status_code==401
            assert not app.sessions
    asyncio.run(check())


def test_sessions_cannot_read_or_mutate_each_other(tmp_path,monkeypatch):
    monkeypatch.delenv('MODEL_API_KEY',raising=False);monkeypatch.setenv('FIELDFIX_PROVIDER','mock')
    async def check():
        async with hosted(tmp_path) as (app,a,transport):
            async with httpx.AsyncClient(transport=transport,base_url='https://demo.example',headers={'Origin':'https://demo.example'}) as b:
                await a.post('/api/session',json={});await b.post('/api/session',json={})
                i=(await a.post('/api/incidents',json={})).json()
                for _ in range(30):
                    detail=(await a.get('/api/incidents/'+i['id'])).json()
                    if detail['state']!='investigating':break
                    await asyncio.sleep(.01)
                assert detail['state']=='awaiting_approval'
                assert (await b.get('/api/incidents')).json()==[]
                assert (await b.get('/api/incidents/'+i['id'])).status_code==404
                assert (await b.post('/api/proposals/'+detail['proposal']['id']+'/approve',json={})).status_code==400
                await b.post('/api/demo/reset',json={'scenario':'healthy'})
                assert (await a.get('/api/incidents/'+i['id'])).json()['state']=='awaiting_approval'
                assert len(app.sessions)==2
    asyncio.run(check())


def test_cross_origin_host_and_forged_cookie_blocked(tmp_path,monkeypatch):
    monkeypatch.delenv('MODEL_API_KEY',raising=False);monkeypatch.setenv('FIELDFIX_PROVIDER','mock')
    async def check():
        async with hosted(tmp_path) as (app,c,_):
            assert (await c.post('/api/session',headers={'Origin':'https://evil.example'},json={})).status_code==403
            assert (await c.post('/api/session',headers={'Host':'evil.example'},json={})).status_code==403
            assert (await c.post('/api/session',headers={'Sec-Fetch-Site':'cross-site'},json={})).status_code==403
            c.cookies.set('fieldfix_demo_session','a'*64)
            assert (await c.get('/api/health')).status_code==401
            assert not app.sessions
    asyncio.run(check())


def test_expiry_closes_jobs_and_removes_station_data(tmp_path,monkeypatch):
    monkeypatch.delenv('MODEL_API_KEY',raising=False);monkeypatch.setenv('FIELDFIX_PROVIDER','mock')
    class Clock:
        now=100
        def __call__(self):return self.now
    clock=Clock()
    async def check():
        async with hosted(tmp_path,clock=clock,ttl=10) as (app,c,_):
            await c.post('/api/session',json={})
            assert list((tmp_path/'sessions').iterdir())
            clock.now+=11
            assert (await c.get('/api/health')).status_code==401
            assert not app.sessions and not list((tmp_path/'sessions').iterdir())
    asyncio.run(check())


def test_capacity_and_mutation_rate_are_bounded(tmp_path,monkeypatch):
    monkeypatch.delenv('MODEL_API_KEY',raising=False);monkeypatch.setenv('FIELDFIX_PROVIDER','mock')
    async def check():
        async with hosted(tmp_path,max_sessions=1) as (app,c,transport):
            await c.post('/api/session',json={})
            async with httpx.AsyncClient(transport=transport,base_url='https://demo.example',headers={'Origin':'https://demo.example'}) as other:
                assert (await other.post('/api/session',json={})).status_code==429
            session=next(iter(app.sessions.values()))
            session.mutations.extend([app.clock()]*30)
            assert (await c.post('/api/demo/reset',json={})).status_code==429
            assert (await c.get('/api/health')).status_code==200
    asyncio.run(check())


def test_free_hosting_refuses_live_provider_or_api_key(tmp_path,monkeypatch):
    monkeypatch.setenv('FIELDFIX_PROVIDER','meta')
    with pytest.raises(RuntimeError):create_hosted_app(origin='https://demo.example',static_dir=str(tmp_path))
    monkeypatch.setenv('FIELDFIX_PROVIDER','mock');monkeypatch.setenv('MODEL_API_KEY','dummy-not-a-real-key')
    with pytest.raises(RuntimeError):create_hosted_app(origin='https://demo.example',static_dir=str(tmp_path))


def test_hosted_body_bounds_and_public_health(tmp_path,monkeypatch):
    monkeypatch.delenv('MODEL_API_KEY',raising=False);monkeypatch.setenv('FIELDFIX_PROVIDER','mock')
    async def check():
        async with hosted(tmp_path) as (_,c,_):
            assert (await c.get('/healthz',headers={'Host':'internal-probe'})).status_code==200
            assert (await c.post('/api/session',content='x'*1025)).status_code==413
            await c.post('/api/session',json={})
            assert (await c.post('/api/incidents',content='x'*16001)).status_code==413
    asyncio.run(check())


def test_slow_session_body_times_out_without_holding_global_lock(tmp_path,monkeypatch):
    import app.hosted as module
    monkeypatch.delenv('MODEL_API_KEY',raising=False);monkeypatch.setenv('FIELDFIX_PROVIDER','mock')
    real_timeout=asyncio.timeout
    monkeypatch.setattr(module.asyncio,'timeout',lambda _:real_timeout(.02))
    async def body():
        yield b'{'
        await asyncio.sleep(100)
    async def check():
        async with hosted(tmp_path) as (app,c,_):
            assert (await c.post('/api/session',content=body())).status_code==408
            assert not app.lock.locked() and not app.sessions
    asyncio.run(check())
