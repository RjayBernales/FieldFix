"""Free public mock demo: opaque-cookie sessions, isolated SQLite stations, bounded resources.

This factory deliberately cannot run Meta inference. The local factory remains available
for genuine Meta demonstrations. A public URL is not a real-world station deployment.
"""
import asyncio
import hashlib
import os
import secrets
import tempfile
import time
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

from .agent import MockProvider
from .core import Engine
from .main import create_app
from .settings import Settings
from .storage import Store

COOKIE = 'fieldfix_demo_session'


@dataclass
class DemoSession:
    engine: Engine
    app: FastAPI
    lifespan: object
    directory: tempfile.TemporaryDirectory
    expires_at: float
    calls: deque = field(default_factory=deque)
    mutations: deque = field(default_factory=deque)
    active: int = 0
    closing: bool = False


class PublicDemo:
    def __init__(self, *, origin, static_dir, data_dir, max_sessions=12, ttl=1800, clock=time.monotonic):
        parsed = urlsplit(origin)
        if parsed.scheme not in {'http', 'https'} or not parsed.netloc or parsed.path not in {'', '/'} or parsed.query or parsed.fragment or parsed.username:
            raise ValueError('Configure one valid FIELDFIX_PUBLIC_ORIGIN without credentials, path, query, or fragment.')
        if parsed.scheme != 'https' and parsed.hostname not in {'127.0.0.1','localhost','::1','testserver'}:
            raise ValueError('Public hosting requires HTTPS.')
        if max_sessions < 1 or ttl < 1:
            raise ValueError('Session bounds must be positive.')
        self.origin = origin.rstrip('/')
        self.host = parsed.netloc.lower()
        self.secure = parsed.scheme == 'https'
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.max_sessions, self.ttl, self.clock = max_sessions, ttl, clock
        self.sessions = {}
        self.created = deque()
        self.lock = asyncio.Lock()

        @asynccontextmanager
        async def lifespan(app):
            task = asyncio.create_task(self.sweep())
            yield
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            for key in list(self.sessions):
                await self.close_session(key)

        self.site = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

        @self.site.get('/healthz')
        async def healthz():
            return dict(status='ok', provider='mock', station_simulated=True, hosted_demo=True)

        self.site.mount('/', StaticFiles(directory=static_dir, html=True), name='dashboard')

    def cookie_key(self, token):
        if not token or len(token) != 64 or any(c not in '0123456789abcdef' for c in token):
            return None
        return hashlib.sha256(token.encode()).hexdigest()

    async def close_session(self, key):
        s = self.sessions.get(key)
        if s and s.active:
            s.closing=True
            s.expires_at=0
            return
        if s:
            self.sessions.pop(key,None)
            await s.lifespan.__aexit__(None, None, None)
            s.engine.store.close()
            s.directory.cleanup()

    async def expire(self):
        for key, s in list(self.sessions.items()):
            if s.expires_at <= self.clock():
                await self.close_session(key)

    async def sweep(self):
        while True:
            await asyncio.sleep(15)
            async with self.lock:
                await self.expire()

    async def respond(self, scope, receive, send, status, body, token=None, clear=False):
        response = JSONResponse(body, status_code=status, headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})
        if token:
            response.set_cookie(COOKIE, token, max_age=self.ttl, httponly=True, secure=self.secure, samesite='strict', path='/')
        if clear:
            response.delete_cookie(COOKIE, httponly=True, secure=self.secure, samesite='strict', path='/')
        await response(scope, receive, send)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.site(scope, receive, send)
        request = Request(scope, receive=receive)
        path, method = scope['path'], scope['method']
        if path == '/healthz' and method == 'GET':
            return await self.site(scope, receive, send)
        if request.headers.get('host','').lower() != self.host:
            return await self.respond(scope,receive,send,403,{'detail':'Host is not allowed.'})
        origin = request.headers.get('origin')
        if (origin and origin != self.origin) or (method not in {'GET','HEAD'} and origin != self.origin):
            return await self.respond(scope,receive,send,403,{'detail':'Same-origin request required.'})
        if request.headers.get('sec-fetch-site') == 'cross-site' and path.startswith('/api/'):
            return await self.respond(scope,receive,send,403,{'detail':'Cross-site API requests are not allowed.'})
        if not path.startswith('/api/'):
            return await self.site(scope, receive, send)
        if method not in {'GET','POST'}:
            return await self.respond(scope,receive,send,405,{'detail':'Method is not allowed.'})
        if path == '/api/session' and method == 'POST':
            # Read before taking the session lock; slow clients must not block other visitors.
            size=0
            try:
                async with asyncio.timeout(5):
                    async for chunk in request.stream():
                        size+=len(chunk)
                        if size>1024:
                            return await self.respond(scope,receive,send,413,{'detail':'Session request too large.'})
            except TimeoutError:
                return await self.respond(scope,receive,send,408,{'detail':'Session request timed out.'})
        key = self.cookie_key(request.cookies.get(COOKIE))
        async with self.lock:
            await self.expire()
            session = self.sessions.get(key)
            if session and session.closing:
                session=None
            if path == '/api/session' and method == 'GET':
                return await self.respond(scope,receive,send,200,dict(hosted_demo=True, provider='mock',
                    authenticated=bool(session), expires_in=max(0,int(session.expires_at-self.clock())) if session else 0))
            if path == '/api/session' and method == 'POST':
                if session:
                    return await self.respond(scope,receive,send,200,dict(authenticated=True,hosted_demo=True,provider='mock'))
                now=self.clock()
                while self.created and self.created[0] <= now-60:
                    self.created.popleft()
                if len(self.sessions)>=self.max_sessions or len(self.created)>=12:
                    return await self.respond(scope,receive,send,429,{'detail':'The free demo is at capacity. Please try again later.'})
                token=secrets.token_hex(32)
                key=self.cookie_key(token)
                directory=tempfile.TemporaryDirectory(prefix='fieldfix-session-',dir=self.data_dir)
                engine=Engine(Store(str(Path(directory.name)/'station.sqlite')))
                settings=Settings(_env_file=None,FIELDFIX_PROVIDER='mock',MODEL_API_KEY='',FIELDFIX_LIVE_REQUEST_LIMIT=0,FIELDFIX_ENABLE_DEMO=True)
                inner=create_app(settings,engine,MockProvider(),_trusted_gateway=True)
                context=inner.router.lifespan_context(inner)
                await context.__aenter__()
                session=DemoSession(engine,inner,context,directory,now+self.ttl)
                self.sessions[key]=session
                self.created.append(now)
                return await self.respond(scope,receive,send,201,dict(authenticated=True,hosted_demo=True,provider='mock',expires_in=self.ttl),token=token)
            if path == '/api/session/end' and method == 'POST':
                if key:
                    await self.close_session(key)
                return await self.respond(scope,receive,send,200,dict(authenticated=False,hosted_demo=True,provider='mock'),clear=True)
            if not session:
                return await self.respond(scope,receive,send,401,{'detail':'Demo session expired. Start a new isolated session.'},clear=True)
            now=self.clock()
            for queue in (session.calls,session.mutations):
                while queue and queue[0] <= now-60:
                    queue.popleft()
            if len(session.calls)>=600 or (method=='POST' and len(session.mutations)>=30):
                return await self.respond(scope,receive,send,429,{'detail':'Demo request limit reached. Please wait a minute.'})
            if path=='/api/incidents' and method=='POST' and len(session.engine.store.all('incidents'))>=10:
                return await self.respond(scope,receive,send,429,{'detail':'This temporary demo session has reached ten investigations. End it and start a new session.'})
            session.active+=1
            session.calls.append(now)
            if method=='POST':
                session.mutations.append(now)
        # This inner app is never directly exposed; the gateway has authorized the opaque cookie
        # and same-origin request. Its ordinary payload and station/proposal checks still apply.
        inner_scope=dict(scope,path=path[4:],raw_path=path[4:].encode(),root_path='')
        started=False
        async def secured_send(message):
            nonlocal started
            if message['type']=='http.response.start':
                started=True
                message=dict(message,headers=list(message.get('headers',[]))+[(b'cache-control',b'no-store'),(b'x-content-type-options',b'nosniff')])
            await send(message)
        try:
            async with asyncio.timeout(20):
                await session.app(inner_scope,receive,secured_send)
        except TimeoutError:
            if not started:
                await self.respond(scope,receive,send,408,{'detail':'Demo request timed out.'})
        finally:
            async with self.lock:
                session.active-=1
                if session.closing or session.expires_at<=self.clock():
                    await self.close_session(key)


def create_hosted_app(*, origin=None, static_dir=None, data_dir=None, max_sessions=12, ttl=1800, clock=time.monotonic):
    # Fail closed instead of silently replacing a requested live provider with a mock.
    if os.getenv('FIELDFIX_PROVIDER','mock') != 'mock' or os.getenv('MODEL_API_KEY'):
        raise RuntimeError('The free public factory requires mock inference and no MODEL_API_KEY. Use the local factory for live Meta.')
    root=Path(__file__).resolve().parents[2]
    origin=origin or os.getenv('FIELDFIX_PUBLIC_ORIGIN') or os.getenv('RENDER_EXTERNAL_URL')
    if not origin:
        raise ValueError('FIELDFIX_PUBLIC_ORIGIN or RENDER_EXTERNAL_URL is required for public hosting.')
    return PublicDemo(origin=origin,static_dir=static_dir or str(root/'frontend/dist'),
                      data_dir=data_dir or os.getenv('FIELDFIX_HOSTED_DATA_DIR',str(root/'.data/hosted')),
                      max_sessions=max_sessions,ttl=ttl,clock=clock)
