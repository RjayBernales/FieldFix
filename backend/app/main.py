import asyncio
import json
from contextlib import asynccontextmanager
from ipaddress import ip_address

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .agent import MetaProvider, MockProvider, investigate
from .core import Conflict, Engine, STATION, utc
from .settings import Settings
from .storage import Store


class StationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    station_id: str = STATION


class IncidentRequest(StationRequest):
    question: str = Field('Why are dashboard readings stale? Investigate using station evidence.', min_length=1, max_length=1000)


class ResetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    scenario: str = 'mismatch'
    topic: str = Field('stations/river-01/turbidity', max_length=120)


def create_app(settings=None, engine=None, provider=None, *, _trusted_gateway=False):
    settings = settings or Settings()
    owned_store = engine is None
    engine = engine or Engine(Store(settings.db))
    provider = provider or (MetaProvider(settings, engine) if settings.provider=='meta' else MockProvider())
    jobs = set()
    incident_jobs = {}

    def spawn(coro, key=None):
        task = asyncio.create_task(coro)
        jobs.add(task)
        if key:
            incident_jobs[key] = task
            task.add_done_callback(lambda _: incident_jobs.pop(key, None))
        task.add_done_callback(jobs.discard)

    async def simulator():
        while True:
            await asyncio.sleep(2)
            engine.tick()

    async def verify(id):
        while not engine.verify_step(id):
            await asyncio.sleep(.5)

    @asynccontextmanager
    async def lifespan(app):
        spawn(simulator())
        yield
        for task in list(jobs):
            task.cancel()
        await asyncio.gather(*jobs, return_exceptions=True)
        if owned_store:
            engine.store.close()

    app = FastAPI(title='FieldFix', lifespan=lifespan)
    app.state.engine = engine
    app.state.settings = settings

    @app.middleware('http')
    async def local_only(request: Request, call_next):
        # Local MVP, not an unauthenticated public deployment. Protect against DNS rebinding and CSRF.
        host = request.url.hostname
        client = request.client.host if request.client else ''
        try:
            loopback = ip_address(client).is_loopback
        except ValueError:
            loopback = client == 'testclient'
        if not _trusted_gateway and (not loopback or host not in {'localhost','127.0.0.1','::1','testserver'}):
            return JSONResponse({'detail':'This MVP accepts loopback requests only.'}, status_code=403)
        origin = request.headers.get('origin')
        if not _trusted_gateway and origin and origin not in {'http://127.0.0.1:5173','http://localhost:5173','http://127.0.0.1:8000','http://localhost:8000'}:
            return JSONResponse({'detail':'Origin is not allowed.'}, status_code=403)
        try:
            length = int(request.headers.get('content-length', '0'))
        except ValueError:
            return JSONResponse({'detail':'Invalid content length.'}, status_code=400)
        if length < 0 or length > 16000:
            return JSONResponse({'detail':'Request too large.'}, status_code=413)
        if request.method in {'POST','PUT','PATCH'}:
            size=0
            chunks=[]
            async for chunk in request.stream():
                size+=len(chunk)
                if size>16000:
                    return JSONResponse({'detail':'Request too large.'},status_code=413)
                chunks.append(chunk)
            request._body=b''.join(chunks)
        return await call_next(request)

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        return JSONResponse({'detail':str(exc)}, status_code=409)

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({'detail':str(exc)}, status_code=400)

    @app.get('/health')
    async def health():
        budget_store = getattr(provider, 'budget_store', engine.store)
        with budget_store.lock:
            used = budget_store.db.execute('SELECT used FROM budget WHERE id=1').fetchone()[0]
        return dict(status='ok', provider=settings.provider, model=settings.model if settings.provider=='meta' else 'deterministic-offline-fixture',
                    credentials_configured=bool(settings.api_key), live_requests_used=used,
                    live_request_limit=settings.live_limit, demo_enabled=settings.enable_demo, station_simulated=True,
                    server_time=utc(engine.clock()))

    @app.get('/stations')
    async def stations():
        c = engine.config()
        return [dict(station_id=STATION, name='River station 01', unit='NTU', last_heartbeat=utc(c['heartbeat']),
                     connected=engine.clock()-c['heartbeat']<=6, transport='In-process simulated topic router')]

    @app.get('/stations/{station}/samples')
    async def samples(station: str):
        engine.check_station(station)
        return dict(local=engine.samples(), received=engine.samples(True), server_time=utc(engine.clock()))

    @app.post('/incidents', status_code=202)
    async def start(body: IncidentRequest):
        engine.check_station(body.station_id)
        if settings.provider=='meta' and not settings.api_key:
            raise HTTPException(503, 'MODEL_API_KEY is required for live Meta inference. No mock fallback.')
        i = engine.new_incident(settings.provider, body.question)
        spawn(investigate(engine, i['id'], provider), i['id'])
        return i

    @app.get('/incidents')
    async def incidents():
        return engine.store.all('incidents')[-30:][::-1]

    @app.get('/incidents/{id}')
    async def incident(id: str):
        i = engine.store.get('incidents', id)
        if not i:
            raise HTTPException(404, 'Unknown incident')
        with engine.store.lock:
            traces = [json.loads(r[0]) for r in engine.store.db.execute('SELECT body FROM inference WHERE incident_id=? ORDER BY id', (id,))]
        return dict(**i, evidence=engine.evidence_list(id), proposal=engine.store.get('proposals',i['proposal_id']) if i['proposal_id'] else None,
                    inference=traces)

    @app.post('/proposals/{id}/approve')
    async def approve(id: str, body: StationRequest):
        i = engine.decide(id, body.station_id, True)
        spawn(verify(i['id']))
        return i

    @app.post('/proposals/{id}/reject')
    async def reject(id: str, body: StationRequest):
        return engine.decide(id, body.station_id, False)

    @app.post('/demo/reset')
    async def reset(body: ResetRequest):
        if not settings.enable_demo:
            raise HTTPException(404, 'Development controls disabled')
        engine.reset(body.scenario, body.topic)
        return dict(status='reset', station_id=STATION)

    @app.post('/incidents/{id}/cancel')
    async def cancel(id: str):
        with engine.store.transaction():
            i = engine.store.get('incidents', id)
            if not i:
                raise HTTPException(404, 'Unknown incident')
            if i['state']!='investigating':
                raise Conflict('Only an active investigation can be cancelled.')
            engine.transition(i, 'unresolved', 'Technician cancelled investigation.')
        task=incident_jobs.get(id)
        if task:
            task.cancel()
        return i

    return app
