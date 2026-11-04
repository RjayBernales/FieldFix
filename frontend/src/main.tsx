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
function Chart({data,now}:{data:Samples;now:number}){
 const all=data.local; if(!all.length)return <div className="empty">Waiting for station samples…</div>
 const start=Math.min(new Date(all[0].sampled_at).getTime(),now-16000),end=now
 const x=(s:Sample)=>50+(new Date(s.sampled_at).getTime()-start)/(end-start)*680
 const y=(s:Sample)=>190-(s.value-12)/12*150
 const line=(samples:Sample[])=>samples.map(s=>`${x(s)},${y(s)}`).join(' ')
 const latest=data.received.at(-1)
 const staleStart=latest?50+(new Date(latest.sampled_at).getTime()+6000-start)/(end-start)*680:50
 return <svg className="chart" viewBox="0 0 780 250" role="img" aria-label="Synthetic turbidity chart: local device samples versus delivered dashboard samples. Shaded area indicates stale dashboard data.">
 {[12,16,20,24].map(v=><g key={v}><line x1="50" y1={190-(v-12)/12*150} x2="730" y2={190-(v-12)/12*150} stroke="#dfe7e3" strokeDasharray="3 6"/><text x="15" y={195-(v-12)/12*150}>{v}</text></g>)}
 {staleStart<730&&<><rect x={Math.max(50,staleStart)} y="20" width={730-Math.max(50,staleStart)} height="180" fill="#f3e8d1" opacity=".65"/><text x={Math.max(60,staleStart+10)} y="36">Stale interval</text></>}
 <polyline points={line(all)} fill="none" stroke="#789b98" strokeWidth="2" strokeDasharray="5 5"/>
 <polyline points={line(data.received)} fill="none" stroke="#136653" strokeWidth="3"/>
 {data.received.map(s=><circle key={s.sequence} cx={x(s)} cy={y(s)} r="3" fill="#136653"/>)}
 <text x="50" y="230">{time(new Date(start).toISOString())}</text><text x="674" y="230">Now</text>
 </svg>
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
 return <><a className="skip-link" href="#main">Skip to station content</a><aside className="sidebar"><a className="brand" href="#main"><span className="brand-icon"><Icon name="wave"/></span>FieldFix<span className="brand-dot">.</span></a><div className="workspace-label">TECHNICIAN WORKSPACE</div><a className="nav-item selected" href="#main"><Icon name="wave"/>Station overview<span>01</span></a><a className="nav-item" href="#investigation"><Icon name="bolt"/>Investigation</a><div className="sidebar-bottom"><div className="avatar">RB</div><div>Station technician<small>Local demo workspace</small></div></div></aside>
 <div className="shell"><header><span>Workspace <span className="slash">/</span> Station operations</span><span className="mode"><i/>Simulated station · {!health?'loading inference mode':health.provider==='meta'?'live Meta inference':'mock inference'}</span></header>
 <main id="main" tabIndex={-1}><div className="page-heading"><div><div className="eyebrow">STATION OPERATIONS</div><h1>A clear path to recovery.</h1><p>Inspect the evidence. Approve the change. Verify the result.</p></div><div className="demo-mark">SOFTWARE STATION<span>In-process simulated transport</span></div></div>
 {paused&&<div className="pause-note" role="status">Updates paused. Readings and freshness are frozen at {time(samples.server_time)}. Resume before investigating.</div>}
 {(error||connectionError)&&<div className="error" role="alert">{error||connectionError}<button onClick={()=>{setError('');setConnectionError('')}} aria-label="Dismiss error">×</button></div>}
 <section className="station-bar"><div className="station-symbol"><Icon name="wave"/></div><div><h2>River station 01</h2><p>Water turbidity <span>·</span> {station}</p></div><div className="station-badges"><span className={'badge '+(local&&age(local.sampled_at,now)!<=6?'good':'warn')}>Device sampling {local&&age(local.sampled_at,now)!<=6?'active':'stale'}</span><span className={'badge '+(stale?'warn':'good')}>Dashboard {stale?'stale':'fresh'}</span></div></section>
 <section className="metrics" aria-label="Station readings"><article><div className="metric-label">DASHBOARD READING <span className={stale?'amber-dot':'green-dot'}/></div><div className="metric-value">{received?.value.toFixed(2)||'—'}<span>NTU</span></div><p>{receivedAge===null?'No delivered sample':`Sampled ${receivedAge}s ago`} <span className={stale?'warning-text':''}>{stale?'· Needs investigation':'· Fresh'}</span></p></article><article><div className="metric-label">LOCAL DEVICE READING</div><div className="metric-value">{local?.value.toFixed(2)||'—'}<span>NTU</span></div><p>Sampled {age(local?.sampled_at,now)??'—'}s ago · Synthetic data</p></article><article><div className="metric-label">INVESTIGATION STATUS</div><div className="status-value">{label}</div><p>{incident?`${incident.tool_calls} tool calls · ${incident.model_turns} model turns`:'Technician approval required for repairs'}</p></article></section>
 <div className="work-grid"><div className="left-column"><section className="panel telemetry"><div className="panel-heading"><div><h2>Station telemetry</h2><p>Local acquisition and dashboard delivery</p></div><button className="text-button" onClick={()=>setPaused(!paused)}>{paused?'Resume updates':'Pause updates'}</button></div><div className="chart-legend"><span><i className="solid-line"/>Dashboard received</span><span><i className="dashed-line"/>Local device</span><span className="chart-unit">NTU · synthetic samples</span></div><Chart data={samples} now={now}/><div className="chart-foot">{stale?'The dashboard is stale. Local readings provide an independent diagnostic signal.':'Dashboard samples are arriving. Fresh data alone does not establish environmental safety.'}</div></section>
 <section className="panel evidence-panel"><div className="panel-heading"><div><h2>Evidence timeline</h2><p>Observed results, with traceable evidence references</p></div><span className="count">{incident?.evidence.length||0} results</span></div>{incident?.evidence.length?<ol className="timeline">{incident.evidence.map((e,index)=><li key={e.evidence_id}><span className={'step '+(e.status==='ok'?'':'step-warning')}>{e.status==='ok'?<Icon name="check"/>:'!'}</span><div><div className="evidence-heading"><h3>{e.tool_name.replaceAll('_',' ')}</h3><time>{time(e.observed_at)}</time></div><p>{e.status==='ok'?'Observed':'Diagnostic '+e.status} <code>{e.evidence_id}</code></p><details><summary>Inspect result {index+1}</summary><pre>{JSON.stringify(e.payload,null,2)}</pre></details></div></li>)}</ol>:<div className="empty"><span className="empty-icon"><Icon name="bolt"/></span><h3>Evidence comes first.</h3><p>Start an investigation to collect device status,<br/>samples, logs, and transport configuration.</p></div>}</section></div>
 <section className="panel investigation" id="investigation"><div className="agent-heading"><span className="agent-icon"><Icon name="bolt"/></span><div><h2>FieldFix assistant</h2><p>{health?.provider==='meta'?health.model:'Offline contract fixture'}</p></div><span className="badge neutral">{health?.provider==='meta'?'META':'MOCK'}</span></div>
 <div className="investigation-body"><div className="eyebrow">EVIDENCE-LED TROUBLESHOOTING</div><h3>Let’s find the break.</h3><p>FieldFix checks the station, proposes a bounded change, and waits for your approval.</p><label htmlFor="question">What are you observing?</label><textarea id="question" maxLength={1000} value={question} onChange={e=>setQuestion(e.target.value)} disabled={!!active}/><button className="primary" disabled={busy||!!active||!health||!question.trim()||paused} onClick={()=>void start()}>{incident?.state==='investigating'?'Collecting evidence…':incident?.state==='verifying'?'Verifying recovery…':'Investigate station'}<Icon name="arrow"/></button>
 {incident&&<div className={'finding '+(incident.state==='resolved'?'recovered':'')} role="status"><div className="eyebrow">{label.toUpperCase()}</div><p>{incident.finding}</p><p className="record-mode">Record provider: {incident.provider==='meta'?'Meta API':'mock fixture'}.</p>{incident.verification&&<div className="progress"><progress max={3} value={Math.min(3,incident.verification.count)}/><span>{incident.verification.count} / 3 post-repair samples</span></div>}</div>}
 {incident?.proposal&&<div className="proposal"><h3>Proposed subscription change</h3><p>Configuration v{incident.proposal.version} · {incident.proposal.status}</p><div className="diff removed"><span>− Before</span><code>{incident.proposal.before}</code></div><div className="diff added"><span>+ After</span><code>{incident.proposal.after}</code></div><small>Expires {time(incident.proposal.expires_at)}. Approval applies only to this exact change.</small>{incident.state==='awaiting_approval'&&<div className="decision"><button className="primary" disabled={busy} onClick={()=>void decide(true)}>Approve repair</button><button className="secondary" disabled={busy} onClick={()=>void decide(false)}>Reject</button></div>}</div>}
 {incident?.state==='investigating'&&<button className="text-button" disabled={busy} onClick={()=>void act(async()=>{await api(`/incidents/${incident.id}/cancel`,{});setIncident(await api('/incidents/'+incident.id))})}>Cancel investigation</button>}
 <div className="safeguard"><Icon name="check"/><span>Repairs need your approval.<br/>Recovery is verified from fresh samples.</span></div>
 {history.length>0&&<div className="history"><label htmlFor="history">Investigation history</label><select id="history" value={activeId===null?(history[0]?.id||''):activeId} onChange={e=>setActiveId(e.target.value)}><option value="">New investigation</option>{history.map(i=><option key={i.id} value={i.id}>{i.id.slice(-6)} · {i.state}</option>)}</select></div>}
 </div><div className="provider-note">{health?.provider==='meta'?`Live request budget: ${health.live_requests_used} / ${health.live_request_limit}. No automatic fallback.`:'Mock inference is deterministic and is not live Meta validation.'}</div></section></div>
 {health?.demo_enabled&&<section className="demo-controls"><div><span className="eyebrow">DEVELOPMENT CONTROLS</span><p>Reset synthetic station state. This interrupts active investigations.</p></div><label className="sr-only" htmlFor="scenario">Demo scenario</label><select id="scenario" value={scenario} onChange={e=>setScenario(e.target.value)}><option value="mismatch">Transport mismatch</option><option value="healthy">Healthy station</option><option value="sensor_failure">Sensor read failure</option><option value="unavailable">Unavailable evidence</option></select><button className="secondary" disabled={busy} onClick={()=>void act(async()=>{await api('/demo/reset',{scenario});setActiveId('');setIncident(null);setSamples(await api(`/stations/${station}/samples`))})}>Reset demo</button></section>}
 <footer><span>FieldFix · Evidence before action.</span><span>Simulated station. No field deployment or safety assessment.</span></footer></main></div></>
}

type SessionStatus={hosted_demo:boolean;authenticated:boolean;expires_in?:number}
function SessionGate(){
 const [status,setStatus]=useState<SessionStatus|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false)
 async function check(){setError('');try{const r=await fetch('/api/session',{signal:AbortSignal.timeout(12000)});if(r.status===404){setStatus({hosted_demo:false,authenticated:true});return}if(!r.ok)throw new Error('Cannot reach the demo server. Retry after it wakes up.');setStatus(await r.json())}catch{setError('The server is starting or unavailable. Free hosting may take a little time to wake up.')}}
 useEffect(()=>{void check();const expired=()=>setStatus({hosted_demo:true,authenticated:false});window.addEventListener('fieldfix-session-expired',expired);return()=>window.removeEventListener('fieldfix-session-expired',expired)},[])
 async function start(){setBusy(true);setError('');try{setStatus(await api<SessionStatus>('/session',{}))}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function end(){setBusy(true);try{await api('/session/end',{});setStatus({hosted_demo:true,authenticated:false})}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 if(!status||!status.authenticated)return <main className="welcome"><a className="brand welcome-brand" href="#"><span className="brand-icon"><Icon name="wave"/></span>FieldFix.</a><section className="welcome-card"><span className="eyebrow">FREE INTERACTIVE DEMO</span><h1>Try a station recovery.</h1><p>Start an isolated software station, inspect its evidence, and approve a repair. Your session is private to this browser and expires after 30 minutes.</p><div className="welcome-disclosure"><strong>Simulated station · mock inference</strong><p>This free hosted demo makes no Meta API calls. Genuine Meta validation results are documented in the repository. No real field station is connected.</p></div>{error&&<p className="error" role="alert">{error}</p>}{status?<button className="primary" disabled={busy} onClick={()=>void start()}>{busy?'Starting…':'Start my demo session'}<Icon name="arrow"/></button>:<button className="primary" onClick={()=>void check()}>{error?'Retry connection':'Connecting to server…'}</button>}<a className="guide-link" href="https://github.com/RjayBernales/FieldFix/blob/dev/fieldfix-mvp/docu/SELF_TEST_GUIDE.md" target="_blank" rel="noreferrer">Read the hands-on testing guide ↗</a><small>Temporary sessions and data reset when the free service restarts. Do not enter secrets or personal data.</small></section></main>
 return <>{status.hosted_demo&&<div className="hosted-banner"><span>Free online demo · mock inference · isolated temporary station</span><button disabled={busy} onClick={()=>void end()}>End my session</button></div>}{error&&<div className="error" role="alert">{error}</div>}<App/></>
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><SessionGate/></React.StrictMode>)
