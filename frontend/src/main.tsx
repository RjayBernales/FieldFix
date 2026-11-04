import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

type Sample={sequence:number;sampled_at:string;received_at:string|null;value:number;unit:string}
type Evidence={evidence_id:string;tool_name:string;observed_at:string;status:string;payload:Record<string,unknown>}
type Proposal={id:string;before:string;after:string;version:number;status:string;expires_at:string;evidence_ids:string[]}
type Incident={id:string;state:string;finding:string;provider:string;tool_calls:number;model_turns:number;evidence:Evidence[];proposal:Proposal|null;verification:{count:number;required:number}|null;inference:{model:string;latency_ms:number;request_id:string;outcome:string}[]}
type Health={provider:string;model:string;demo_enabled:boolean;credentials_configured:boolean;live_requests_used:number;live_request_limit:number;server_time:string}
type Samples={local:Sample[];received:Sample[];server_time:string}
const station='station-01'
async function api<T>(path:string,body?:unknown):Promise<T>{
 let r:Response
 try{r=await fetch('/api'+path,{signal:AbortSignal.timeout(12000),...(body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})})}
 catch{throw new Error('Cannot reach the FieldFix backend. Check that it is running, then retry.')}
 let data:unknown
 try{data=await r.json()}catch{throw new Error('The backend is unavailable or returned an invalid response. Check the backend server.')}
 if(r.status===401)window.dispatchEvent(new Event('fieldfix-session-expired'))
 if(!r.ok){const detail=(data as {detail?:unknown})?.detail;throw new Error(typeof detail==='string'?detail:`Request rejected (HTTP ${r.status}).`)}
 return data as T
}
const time=(s:string)=>new Date(s).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'})
const age=(s?:string,now=Date.now())=>s?Math.max(0,Math.round((now-new Date(s).getTime())/1000)):null
function Icon({name}:{name:'wave'|'arrow'|'check'|'bolt'}){return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">{name==='wave'?<path d="M2 12h4l3-8 5 16 3-8h5"/>:name==='arrow'?<path d="M5 12h14m-6-6 6 6-6 6"/>:name==='check'?<path d="m5 12 4 4L19 6"/>:<path d="m13 2-9 12h7l-1 8 10-12h-7z"/>}</svg>}
function Chart({data,now}:{data:Samples;now:number}) {
 const all=data.local
 const start=all.length?Math.min(new Date(all[0].sampled_at).getTime(),now-16000):now-16000
 const span=Math.max(1,now-start)
 const x=(s:Sample)=>48+(new Date(s.sampled_at).getTime()-start)/span*648
 const y=(s:Sample)=>176-(s.value-12)/12*140
 const points=(rows:Sample[])=>rows.map(s=>`${x(s)},${y(s)}`).join(' ')
 const latest=data.received.at(-1)
 const staleX=latest?48+(new Date(latest.sampled_at).getTime()+6000-start)/span*648:48
 return <div className="chart-frame"><svg className="chart" viewBox="0 0 720 220" role="img" aria-label="Synthetic turbidity over time. Solid green is delivered data; dashed grey is local acquisition. Amber shading indicates stale delivery.">
  {[12,16,20,24].map(v=><g key={v}><line x1="48" y1={176-(v-12)/12*140} x2="696" y2={176-(v-12)/12*140} className="gridline"/><text x="32" textAnchor="end" y={180-(v-12)/12*140}>{v}</text></g>)}
  {staleX<696&&<rect x={Math.max(48,staleX)} y="24" width={696-Math.max(48,staleX)} height="160" className="stale-span"/>}
  {!!all.length&&<polyline points={points(all)} className="local-series"/>}
  {!!data.received.length&&<polyline points={points(data.received)} className="received-series"/>}
  {[0,1,2,3].map(i=><text key={i} x={48+i*216} y="210" textAnchor={i===0?'start':i===3?'end':'middle'}>{i===3?'Now':time(new Date(start+span*i/3).toISOString())}</text>)}
  {!all.length&&<text x="372" y="105" textAnchor="middle">Waiting for station samples</text>}
 </svg></div>
}
function DeliveryPath({localFresh,deliveredFresh}:{localFresh:boolean;deliveredFresh:boolean}) {
 return <div className="delivery-path" role="group" aria-label="Observed sample delivery path">
  <div><span className={'path-dot '+(localFresh?'positive':'caution')}/><strong>Acquisition</strong><small>{localFresh?'Fresh local samples':'Awaiting fresh samples'}</small></div>
  <span className={'path-link '+(deliveredFresh?'':'interrupted')} aria-hidden="true"/>
  <div><span className={'path-dot '+(deliveredFresh?'positive':'caution')}/><strong>Topic delivery</strong><small>{deliveredFresh?'Samples arriving':'Delivery delayed'}</small></div>
  <span className={'path-link '+(deliveredFresh?'':'interrupted')} aria-hidden="true"/>
  <div><span className={'path-dot '+(deliveredFresh?'positive':'caution')}/><strong>Dashboard</strong><small>{deliveredFresh?'Fresh within 6s':'Stale beyond 6s'}</small></div>
 </div>
}
function EvidenceTimeline({evidence}:{evidence:Evidence[]}) {
 return <section className="panel evidence-panel" aria-labelledby="evidence-title">
  <div className="panel-heading"><div><h2 id="evidence-title">Diagnostic evidence</h2><p>Immutable observations from station tools</p></div><span className="count">{evidence.length} results</span></div>
  {evidence.length?<ol className="timeline">{evidence.map((e,index)=><li key={e.evidence_id}>
   <details><summary><span className={'result-mark '+(e.status==='ok'?'':'result-warning')}>{e.status==='ok'?<Icon name="check"/>:'!'}</span><span className="evidence-name"><strong>{e.tool_name.replaceAll('_',' ')}</strong><span>{e.status==='ok'?'Observed':e.status} · <time>{time(e.observed_at)}</time></span></span><span className="inspect-label">Inspect <span aria-hidden="true">↗</span></span></summary>
   <div className="evidence-detail"><p>Result {index+1} · <code>{e.evidence_id}</code></p><pre>{JSON.stringify(e.payload,null,2)}</pre></div></details>
  </li>)}</ol>:<div className="empty"><h3>No diagnostic evidence yet</h3><p>Investigate this station to inspect acquisition, logs, and transport configuration.</p><span>Each result will include its source, timestamp, and evidence reference.</span></div>}
 </section>
}
function App(){
 const [health,setHealth]=useState<Health|null>(null),[samples,setSamples]=useState<Samples>({local:[],received:[],server_time:new Date().toISOString()})
 const [incident,setIncident]=useState<Incident|null>(null),[activeId,setActiveId]=useState<string|null>(null)
 const [error,setError]=useState(''),[connectionError,setConnectionError]=useState(''),[busy,setBusy]=useState(false),[scenario,setScenario]=useState('mismatch'),[question,setQuestion]=useState('Why are dashboard readings stale?'),[paused,setPaused]=useState(false)
 const [history,setHistory]=useState<{id:string;state:string}[]>([])
 useEffect(()=>{let alive=true;let timer:ReturnType<typeof setTimeout>
 async function refresh(){try{
  const [h,s,list]=await Promise.all([api<Health>('/health'),api<Samples>(`/stations/${station}/samples`),api<{id:string;state:string}[]>('/incidents')])
  if(!alive)return;setHealth(h);setSamples(s);setHistory(list);setConnectionError('')
  const id=activeId===null?list[0]?.id:activeId
  if(id){const i=await api<Incident>('/incidents/'+id);if(alive)setIncident(i)}else setIncident(null)
 }catch(e){if(alive)setConnectionError((e as Error).message)}finally{if(alive&&!paused)timer=setTimeout(refresh,1000)}}
 void refresh();return()=>{alive=false;clearTimeout(timer)}
 },[activeId,paused])
 async function act(fn:()=>Promise<void>){setBusy(true);setError('');try{await fn()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function start(){await act(async()=>{const i=await api<Incident>('/incidents',{station_id:station,question});setActiveId(i.id);setIncident({...i,evidence:[],proposal:null,inference:[]})})}
 async function decide(approve:boolean){await act(async()=>{await api(`/proposals/${incident?.proposal?.id}/${approve?'approve':'reject'}`,{station_id:station});if(activeId)setIncident(await api<Incident>('/incidents/'+activeId))})}
 const now=new Date(samples.server_time).getTime(),received=samples.received.at(-1),local=samples.local.at(-1)
 const receivedAge=age(received?.sampled_at,now),stale=receivedAge===null||receivedAge>6
 const active=incident&&['investigating','awaiting_approval','repairing','verifying'].includes(incident.state)
 const label=incident?.state.replaceAll('_',' ')||'Ready to investigate'
 const localFresh=!!local&&(age(local.sampled_at,now)??Infinity)<=6
 return <>
  <a className="skip-link" href="#main">Skip to station content</a>
  <header className="app-header"><a className="brand" href="#main"><Icon name="wave"/>FieldFix<span className="product-scope">Station operations</span></a><span className="mode">Simulated station · {!health?'connecting':health.provider==='meta'?'live Meta inference':'mock inference'}</span></header>
  <main id="main" tabIndex={-1} className="workspace">
   <div className="page-heading"><div><div className="station-id">{station} <span> / </span> Water turbidity</div><h1>River station 01</h1><p>{!health?'Connecting to station…':stale?'Dashboard delivery needs attention. Inspect the station before making a change.':'Dashboard samples are arriving. Review the evidence before closing your investigation.'}</p></div><div className="heading-status"><span className={'badge '+(stale?'warn':'good')}>{stale?'Delivery stale':'Delivery fresh'}</span><span className="updated">{paused?'Paused at':'Updated'} {time(samples.server_time)}</span></div></div>
   {paused&&<div className="pause-note" role="status">Updates paused at {time(samples.server_time)}. Readings and freshness are frozen. Resume before investigating.</div>}
   {(error||connectionError)&&<div className="error" role="alert"><span>{error||connectionError}</span><button onClick={()=>{setError('');setConnectionError('')}} aria-label="Dismiss error">×</button></div>}
   <div className="work-grid">
    <section className="panel telemetry" aria-labelledby="telemetry-title">
     <div className="panel-heading"><div><h2 id="telemetry-title">Acquisition & delivery</h2><p>Independent device and dashboard observations</p></div><button className="text-button" onClick={()=>setPaused(!paused)}>{paused?'Resume updates':'Pause updates'}</button></div>
     <div className="metrics" role="group" aria-label="Station readings"><article><div className="metric-label">Dashboard reading</div><div className="metric-value">{received?.value.toFixed(2)||'—'}<span>NTU</span></div><p>{receivedAge===null?'No delivered sample':`Sampled ${receivedAge}s ago`}</p></article><article><div className="metric-label">Local device</div><div className="metric-value">{local?.value.toFixed(2)||'—'}<span>NTU</span></div><p>Sampled {age(local?.sampled_at,now)??'—'}s ago</p></article><article><div className="metric-label">Delivery freshness</div><div className={'metric-value freshness '+(stale?'warning-text':'')}>{receivedAge??'—'}<span>sec</span></div><p>Freshness threshold: 6s</p></article></div>
     <DeliveryPath localFresh={localFresh} deliveredFresh={!stale}/>
     <div className="chart-legend"><span><i className="solid-line"/>Dashboard received</span><span><i className="dashed-line"/>Local device</span><span className="chart-unit">NTU · synthetic</span></div>
     <Chart data={samples} now={now}/>
     <div className="chart-foot">{stale?'Amber interval: dashboard samples exceed the 6-second freshness threshold.':'Delivery is fresh. These synthetic readings do not establish environmental safety.'}</div>
    </section>
    <section className="panel investigation" id="investigation" aria-labelledby="investigation-title">
     <div className="panel-heading"><div><h2 id="investigation-title">Station investigation</h2><p>{health?.provider==='meta'?health.model:'Deterministic mock fixture'}</p></div><span className="badge neutral">{health?.provider==='meta'?'Meta API':'Mock'}</span></div>
     <div className="investigation-body">
      {!incident&&<div className="investigation-intro"><h3>Find the break in delivery.</h3><p>Collect evidence, review an exact repair, then verify recovery from new samples.</p></div>}
      {incident&&<div className={'finding '+(incident.state==='resolved'?'recovered':'')} role="status"><div className="finding-title"><span className={'status-dot '+(incident.state==='resolved'?'positive':'')}/><h3>{label}</h3></div><p>{incident.finding||'Inspecting station evidence…'}</p><div className="run-meta"><span>{incident.tool_calls} tool calls</span><span>{incident.model_turns} model turns</span><span>{incident.provider==='meta'?'Meta API':'Mock fixture'}</span></div>{incident.verification&&<div className="progress"><progress aria-label="Post-repair verification" max={incident.verification.required} value={Math.min(incident.verification.required,incident.verification.count)}/><span>{incident.verification.count} / {incident.verification.required} post-repair samples</span></div>}</div>}
      {incident?.proposal&&<div className="proposal"><div className="proposal-heading"><h3>Subscription repair</h3><span className="badge neutral">{incident.proposal.status}</span></div><p>Configuration v{incident.proposal.version} · exact topic change</p><div className="diff removed"><span>Current subscription</span><code>{incident.proposal.before}</code></div><div className="diff added"><span>Proposed subscription</span><code>{incident.proposal.after}</code></div><small>Expires {time(incident.proposal.expires_at)}. Approval applies only to this exact change.</small><details className="proposal-refs"><summary>Supporting evidence ({incident.proposal.evidence_ids.length})</summary><ul>{incident.proposal.evidence_ids.map(id=><li key={id}><code>{id}</code></li>)}</ul></details>{incident.state==='awaiting_approval'&&<div className="decision"><button className="primary" disabled={busy} onClick={()=>void decide(true)}>Approve repair <Icon name="check"/></button><button className="secondary" disabled={busy} onClick={()=>void decide(false)}>Reject</button></div>}</div>}
      <details className="question-form" open={!incident||undefined}><summary>{incident?'Investigate another observation':'Your observation'}</summary><label htmlFor="question">What are you observing?</label><textarea id="question" maxLength={1000} value={question} onChange={e=>setQuestion(e.target.value)} disabled={!!active}/><button className="primary" disabled={busy||!!active||!health||!question.trim()||paused} onClick={()=>void start()}>{incident?.state==='investigating'?'Collecting evidence…':incident?.state==='verifying'?'Verifying recovery…':'Investigate station'}<Icon name="arrow"/></button>{paused&&<p className="field-help">Resume station updates to start an investigation.</p>}{active&&<p className="field-help">Complete or cancel the current investigation before starting another.</p>}</details>
      {incident?.state==='investigating'&&<button className="text-button cancel-action" disabled={busy} onClick={()=>void act(async()=>{await api(`/incidents/${incident.id}/cancel`,{});setIncident(await api('/incidents/'+incident.id))})}>Cancel investigation</button>}
      <div className="safeguard"><Icon name="check"/><span>Your approval controls the repair.<br/>Fresh post-repair samples establish recovery.</span></div>
      {history.length>0&&<div className="history"><label htmlFor="history">Investigation history</label><select id="history" value={activeId===null?(history[0]?.id||''):activeId} onChange={e=>setActiveId(e.target.value)}><option value="">New investigation</option>{history.map(i=><option key={i.id} value={i.id}>{i.id.slice(-6)} · {i.state.replaceAll('_',' ')}</option>)}</select></div>}
     </div>
     <div className="provider-note">{health?.provider==='meta'?`Live request budget: ${health.live_requests_used} / ${health.live_request_limit}. No automatic fallback.`:'Mock inference · not live Meta validation. Station data and transport are simulated.'}</div>
    </section>
    <EvidenceTimeline evidence={incident?.evidence||[]}/>
   </div>
   {health?.demo_enabled&&<section className="demo-controls" aria-labelledby="demo-title"><div><h2 id="demo-title">Simulator controls</h2><p>Reset the synthetic station. Active investigations will be interrupted.</p></div><div className="reset-fields"><label className="sr-only" htmlFor="scenario">Demo scenario</label><select id="scenario" value={scenario} onChange={e=>setScenario(e.target.value)}><option value="mismatch">Transport mismatch</option><option value="healthy">Healthy station</option><option value="sensor_failure">Sensor read failure</option><option value="unavailable">Unavailable evidence</option></select><button className="secondary" disabled={busy} onClick={()=>void act(async()=>{await api('/demo/reset',{scenario});setActiveId('');setIncident(null);setSamples(await api(`/stations/${station}/samples`))})}>Reset demo</button></div></section>}
   <footer><span>FieldFix · Evidence before action.</span><a href="https://github.com/RjayBernales/FieldFix/blob/main/docu/SELF_TEST_GUIDE.md" target="_blank" rel="noreferrer">Hands-on testing guide ↗</a><span>Simulated station. No field deployment.</span></footer>
  </main>
 </>
}

type SessionStatus={hosted_demo:boolean;authenticated:boolean;expires_in?:number}
function SessionGate(){
 const [status,setStatus]=useState<SessionStatus|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false)
 async function check(){setError('');try{const r=await fetch('/api/session',{signal:AbortSignal.timeout(12000)});if(r.status===404){setStatus({hosted_demo:false,authenticated:true});return}if(!r.ok)throw new Error('Cannot reach the demo server. Retry after it wakes up.');setStatus(await r.json())}catch{setError('The server is starting or unavailable. Free hosting may take a little time to wake up.')}}
 useEffect(()=>{void check();const expired=()=>setStatus({hosted_demo:true,authenticated:false});window.addEventListener('fieldfix-session-expired',expired);return()=>window.removeEventListener('fieldfix-session-expired',expired)},[])
 async function start(){setBusy(true);setError('');try{setStatus(await api<SessionStatus>('/session',{}))}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function end(){setBusy(true);try{await api('/session/end',{});setStatus({hosted_demo:true,authenticated:false})}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 if(!status||!status.authenticated)return <main className="welcome"><a className="brand" href="#"><Icon name="wave"/>FieldFix<span className="product-scope">Interactive demo</span></a><div className="welcome-layout"><section className="welcome-card"><span className="welcome-kicker">A technician's view</span><h1>From stale readings<br/>to verified recovery.</h1><p>Work through a station delivery fault. Inspect what happened, approve the exact change, and watch fresh samples return.</p><div className="welcome-disclosure"><strong>Simulated station · mock inference</strong><p>This free demo makes no Meta API calls. Genuine Meta validation is documented in the repository.</p></div>{error&&<p className="error" role="alert">{error}</p>}{status?<button className="primary" disabled={busy} onClick={()=>void start()}>{busy?'Starting your station…':'Start my demo session'}<Icon name="arrow"/></button>:<button className="primary" disabled={!error} onClick={()=>void check()}>{error?'Retry connection':'Connecting to server…'}</button>}<a className="guide-link" href="https://github.com/RjayBernales/FieldFix/blob/main/docu/SELF_TEST_GUIDE.md" target="_blank" rel="noreferrer">Read the hands-on testing guide ↗</a><small>An isolated session, private to this browser, expires after 30 minutes. Do not enter secrets or personal data.</small></section><aside className="welcome-process" aria-label="Demo workflow"><div className="process-heading"><Icon name="wave"/><span>Station recovery workflow</span></div><ol><li><strong>Observe the gap</strong><p>The device keeps sampling while dashboard delivery falls behind.</p></li><li><strong>Follow the evidence</strong><p>Inspect diagnostic results and compare the exact subscription topics.</p></li><li><strong>Approve & verify</strong><p>Authorize a bounded repair. Recovery needs three new post-repair samples.</p></li></ol><div className="welcome-footnote">Software station · in-process transport<br/>No hardware connection or field deployment</div></aside></div></main>
 return <>{status.hosted_demo&&<div className="hosted-banner"><span>Free online demo · mock inference · isolated temporary station</span><button disabled={busy} onClick={()=>void end()}>End my session</button></div>}{error&&<div className="error" role="alert">{error}</div>}<App/></>
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><SessionGate/></React.StrictMode>)
