import asyncio
import json
import time
from pathlib import Path

import httpx

from ..core import STATION
from ..tools import execute, schemas

SYSTEM = Path(__file__).with_name('system.txt').read_text()


class ProviderError(RuntimeError):
    pass


class MetaProvider:
    """Documented Chat Completions protocol; no SDK-specific coupling or silent retry."""
    def __init__(self, settings, engine, transport=None):
        self.settings, self.engine, self.transport = settings, engine, transport

    async def complete(self, messages, incident_id):
        s = self.settings
        if not s.api_key:
            raise ProviderError('MODEL_API_KEY is missing; live inference was not attempted.')
        if not s.base_url.startswith('https://'):
            raise ProviderError('Meta base URL must use HTTPS.')
        if len(json.dumps(messages)) > 180000:
            raise ProviderError('Context size limit reached.')
        with self.engine.store.transaction():
            used = self.engine.store.db.execute('SELECT used FROM budget WHERE id=1').fetchone()[0]
            if used >= s.live_limit:
                raise ProviderError('Persistent live request budget exhausted; review usage before increasing the limit.')
            self.engine.store.db.execute('UPDATE budget SET used=used+1 WHERE id=1')
        started = time.monotonic()
        metadata = dict(provider='meta', model=s.model, returned_model=None, request_id=None, usage=None, outcome='error', failure_kind=None)
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(25), transport=self.transport) as client:
                response = await client.post(s.base_url.rstrip('/')+'/chat/completions',
                    headers={'Authorization': 'Bearer '+s.api_key},
                    json=dict(model=s.model, messages=messages, tools=schemas(), tool_choice='auto',
                              max_completion_tokens=1600, reasoning_effort=s.reasoning_effort))
            metadata['request_id'] = response.headers.get('x-request-id')
            if response.status_code != 200:
                metadata['failure_kind']='http_status'
                metadata['http_status']=response.status_code
                raise ProviderError(f'Meta returned HTTP {response.status_code}; no fallback was used.')
            if len(response.content) > 1000000:
                metadata['failure_kind']='response_size'
                raise ProviderError('Meta response exceeded size limit.')
            body = response.json()
            message = body['choices'][0]['message']
            if message.get('role') != 'assistant':
                raise ValueError()
            # Never persist reasoning fields or authorization data.
            output = {k: message[k] for k in ('role', 'content', 'tool_calls') if k in message}
            if output.get('content') is not None and not isinstance(output['content'], str):
                raise ValueError()
            if not isinstance(output.get('tool_calls', []), list):
                raise ValueError()
            usage=body.get('usage')
            safe_usage={k:v for k,v in usage.items() if k in {'prompt_tokens','completion_tokens','total_tokens'} and type(v) is int} if isinstance(usage,dict) else None
            metadata.update(outcome='ok', usage=safe_usage, returned_model=body.get('model'), request_id=metadata['request_id'] or body.get('id'))
            return output
        except httpx.HTTPError as exc:
            metadata['failure_kind']='timeout' if isinstance(exc,httpx.TimeoutException) else 'connection'
            raise ProviderError('Meta '+metadata['failure_kind']+' failure; no fallback was used.') from exc
        except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
            metadata['failure_kind']='response_protocol'
            raise ProviderError('Meta response protocol failure; no fallback was used.') from exc
        finally:
            metadata['latency_ms'] = round((time.monotonic()-started)*1000)
            with self.engine.store.transaction():
                self.engine.store.db.execute('INSERT INTO inference(incident_id,body) VALUES(?,?)', (incident_id, json.dumps(metadata)))


class MockProvider:
    """Deterministic offline contract fixture; never used on the live path."""
    async def complete(self, messages, incident_id):
        results = [json.loads(m['content']) for m in messages if m['role']=='tool']
        def call(name, args, count):
            return dict(id=f'mock_{count}', type='function', function=dict(name=name, arguments=json.dumps(args)))
        if not results:
            names = ['get_station_status','get_local_samples','get_received_samples','get_device_logs','get_transport_config']
            return dict(role='assistant', content=None, tool_calls=[call(n, dict(station_id=STATION), j) for j,n in enumerate(names)])
        by_name = {e['tool_name']:e for e in results}
        refs = ' '.join(e['evidence_id'] for e in results)
        if any(e['status']!='ok' for e in results):
            return dict(role='assistant', content='Diagnostic evidence is unavailable or local acquisition failed. Request a physical check or restore diagnostic access. '+refs)
        c = by_name['get_transport_config']['payload']
        if c['publish_topic'] != c['subscription_topic'] and 'propose_subscription_update' not in by_name:
            return dict(role='assistant', content=None, tool_calls=[call('propose_subscription_update',dict(station_id=STATION,
                subscription_topic=c['publish_topic'], expected_version=c['version'],
                evidence_ids=[by_name[n]['evidence_id'] for n in ('get_local_samples','get_received_samples','get_transport_config')]), 5)])
        return dict(role='assistant', content='No fault found in collected evidence; no repair proposed. '+refs)


async def investigate(engine, incident_id, provider):
    i = engine.store.get('incidents', incident_id)
    messages = [dict(role='developer', content=SYSTEM), dict(role='user', content=f"Station {STATION}. {i['question']}")]
    calls = 0
    try:
        async with asyncio.timeout(120):
            for turn in range(8):
                i = engine.store.get('incidents', incident_id)
                if i['state'] != 'investigating':
                    return
                message = await provider.complete(messages, incident_id)
                with engine.store.transaction():
                    i = engine.store.get('incidents', incident_id)
                    if i['state'] != 'investigating':
                        return
                    i['model_turns'] = turn+1
                    engine.store.put('incidents', incident_id, i)
                tool_calls = message.get('tool_calls') or []
                if len(tool_calls)+calls > 12:
                    raise ProviderError('Tool-call limit reached.')
                messages.append(message)
                if not tool_calls:
                    finding = (message.get('content') or 'No supported conclusion returned.')[:6000]
                    evidence = engine.evidence_list(incident_id)
                    if not evidence or not any(e['evidence_id'] in finding for e in evidence):
                        finding = 'Provider ended without an evidence-cited conclusion. Investigation unresolved.'
                    with engine.store.transaction():
                        i = engine.store.get('incidents', incident_id)
                        engine.transition(i, 'unresolved', finding)
                    return
                ids = set()
                for call in tool_calls:
                    if not isinstance(call, dict) or not isinstance(call.get('id'), str) or call['id'] in ids:
                        raise ProviderError('Malformed tool-call protocol.')
                    ids.add(call['id'])
                    function = call.get('function', {})
                    if not isinstance(function.get('name'), str) or not isinstance(function.get('arguments'), str):
                        raise ProviderError('Malformed tool-call arguments.')
                    i = engine.store.get('incidents', incident_id)
                    if i['state'] != 'investigating':
                        break
                    result = execute(engine, incident_id, function['name'], function['arguments'])
                    calls += 1
                    messages.append(dict(role='tool', tool_call_id=call['id'], content=json.dumps(result)))
                    with engine.store.transaction():
                        i = engine.store.get('incidents', incident_id)
                        i['tool_calls'] = calls
                        engine.store.put('incidents', incident_id, i)
                if engine.store.get('incidents', incident_id)['state'] == 'awaiting_approval':
                    return
            raise ProviderError('Model turn limit reached.')
    except asyncio.CancelledError:
        with engine.store.transaction():
            i = engine.store.get('incidents', incident_id)
            if i['state']=='investigating':
                engine.transition(i, 'unresolved', 'Investigation cancelled or server stopped.')
        raise
    except Exception as exc:
        with engine.store.transaction():
            i = engine.store.get('incidents', incident_id)
            if i['state']=='investigating':
                message = ('Investigation exceeded the 120-second overall timeout.' if isinstance(exc,TimeoutError)
                           else str(exc) if isinstance(exc,ProviderError) else 'Provider or tool protocol failed safely.')
                engine.transition(i, 'failed', message)
