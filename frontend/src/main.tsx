import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

type Sample = {
  sequence: number;
  sampled_at: string;
  received_at: string | null;
  value: number;
  unit: string;
};
type Evidence = {
  evidence_id: string;
  tool_name: string;
  observed_at: string;
  status: string;
  payload: Record<string, unknown>;
};
type Proposal = {
  id: string;
  before: string;
  after: string;
  version: number;
  status: string;
  expires_at: string;
  evidence_ids: string[];
};
type Incident = {
  id: string;
  state: string;
  finding: string;
  provider: string;
  tool_calls: number;
  model_turns: number;
  evidence: Evidence[];
  proposal: Proposal | null;
  verification: { count: number; required: number } | null;
  inference: {
    model: string;
    latency_ms: number;
    request_id: string;
    outcome: string;
  }[];
};
type Health = {
  provider: string;
  model: string;
  demo_enabled: boolean;
  credentials_configured: boolean;
  live_requests_used: number;
  live_request_limit: number;
  server_time: string;
};
type Samples = { local: Sample[]; received: Sample[]; server_time: string };
const station = "station-01";
async function api<T>(path: string, body?: unknown): Promise<T> {
  let r: Response;
  try {
    r = await fetch("/api" + path, {
      signal: AbortSignal.timeout(12000),
      ...(body === undefined
        ? {}
        : {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          }),
    });
  } catch {
    throw new Error(
      "Cannot reach the FieldFix backend. Check that it is running, then retry.",
    );
  }
  let data: unknown;
  try {
    data = await r.json();
  } catch {
    throw new Error(
      "The backend is unavailable or returned an invalid response. Check the backend server.",
    );
  }
  if (r.status === 401)
    window.dispatchEvent(new Event("fieldfix-session-expired"));
  if (!r.ok) {
    const detail = (data as { detail?: unknown })?.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : `Request rejected (HTTP ${r.status}).`,
    );
  }
  return data as T;
}
const chartTime = (s: string) =>
  new Date(s).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
const time = (s: string) =>
  new Date(s).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
const age = (s?: string, now = Date.now()) =>
  s ? Math.max(0, Math.round((now - new Date(s).getTime()) / 1000)) : null;
function Brand({ context }: { context?: string }) {
  return (
    <div className={"brand-lockup" + (context ? " brand-lockup--welcome" : "")}>
      <a className="brand" href="#overview" aria-label="FieldFix home">
        <img
          className="brand-logo"
          src="/brand/fieldfix-logo-v1.png"
          width={2172}
          height={724}
          alt="FieldFix"
          decoding="async"
          fetchPriority="high"
        />
      </a>
      {context && <span className="product-scope">{context}</span>}
    </div>
  );
}

function Icon({ name }: { name: "wave" | "arrow" | "check" | "bolt" }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      aria-hidden="true"
    >
      {name === "wave" ? (
        <path d="M2 12h4l3-8 5 16 3-8h5" />
      ) : name === "arrow" ? (
        <path d="M5 12h14m-6-6 6 6-6 6" />
      ) : name === "check" ? (
        <path d="m5 12 4 4L19 6" />
      ) : (
        <path d="m13 2-9 12h7l-1 8 10-12h-7z" />
      )}
    </svg>
  );
}
function Chart({ data, now }: { data: Samples; now: number }) {
  const frame = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 720, height: 168 });
  useEffect(() => {
    if (!frame.current) return;
    const observer = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      if (width > 0 && height > 0) setSize({ width, height });
    });
    observer.observe(frame.current);
    return () => observer.disconnect();
  }, []);
  const { width, height } = size;
  const left = 48,
    right = width - 24,
    top = 24,
    bottom = height - 40;
  const plotWidth = Math.max(1, right - left),
    plotHeight = Math.max(1, bottom - top);
  const all = data.local;
  const start = all.length
    ? Math.min(new Date(all[0].sampled_at).getTime(), now - 16000)
    : now - 16000;
  const span = Math.max(1, now - start);
  const x = (s: Sample) =>
    left + ((new Date(s.sampled_at).getTime() - start) / span) * plotWidth;
  const y = (v: number) => bottom - ((v - 12) / 12) * plotHeight;
  const points = (rows: Sample[]) =>
    rows.map((s) => `${x(s)},${y(s.value)}`).join(" ");
  const latest = data.received.at(-1);
  const staleX = latest
    ? left +
      ((new Date(latest.sampled_at).getTime() + 6000 - start) / span) *
        plotWidth
    : left;
  return (
    <div className="chart-frame" ref={frame}>
      <svg
        className="chart"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Synthetic turbidity over time. Solid green is delivered data; dashed grey is local acquisition. Amber shading indicates stale delivery."
      >
        <defs>
          <clipPath id="telemetry-plot">
            <rect x={left} y={top} width={plotWidth} height={plotHeight} />
          </clipPath>
        </defs>
        {[12, 16, 20, 24].map((v) => (
          <g key={v}>
            <line
              x1={left}
              y1={y(v)}
              x2={right}
              y2={y(v)}
              className="gridline"
            />
            <text x={left - 12} y={y(v) + 4} textAnchor="end">
              {v}
            </text>
          </g>
        ))}
        <g clipPath="url(#telemetry-plot)">
          {staleX < right && (
            <rect
              x={Math.max(left, staleX)}
              y={top}
              width={right - Math.max(left, staleX)}
              height={plotHeight}
              className="stale-span"
            />
          )}
          {!!all.length && (
            <polyline points={points(all)} className="local-series" />
          )}
          {!!data.received.length && (
            <polyline
              points={points(data.received)}
              className="received-series"
            />
          )}
        </g>
        {[0, 1, 2, 3].map((i) => (
          <text
            key={i}
            x={left + (i * plotWidth) / 3}
            y={height - 10}
            textAnchor={i === 0 ? "start" : i === 3 ? "end" : "middle"}
          >
            {i === 3
              ? "Now"
              : chartTime(new Date(start + (span * i) / 3).toISOString())}
          </text>
        ))}
        {!all.length && (
          <text
            x={(left + right) / 2}
            y={(top + bottom) / 2}
            textAnchor="middle"
          >
            Waiting for station samples
          </text>
        )}
      </svg>
    </div>
  );
}
function DeliveryPath({
  localFresh,
  deliveredFresh,
}: {
  localFresh: boolean;
  deliveredFresh: boolean;
}) {
  return (
    <div
      className="delivery-path"
      role="group"
      aria-label="Observed sample delivery path"
    >
      <div>
        <span className={"path-dot " + (localFresh ? "positive" : "caution")} />
        <strong>Acquisition</strong>
        <small>
          {localFresh ? "Fresh local samples" : "Awaiting fresh samples"}
        </small>
      </div>
      <span
        className={"path-link " + (deliveredFresh ? "" : "interrupted")}
        aria-hidden="true"
      />
      <div>
        <span
          className={"path-dot " + (deliveredFresh ? "positive" : "caution")}
        />
        <strong>Topic delivery</strong>
        <small>
          {deliveredFresh ? "Samples arriving" : "Delivery delayed"}
        </small>
      </div>
      <span
        className={"path-link " + (deliveredFresh ? "" : "interrupted")}
        aria-hidden="true"
      />
      <div>
        <span
          className={"path-dot " + (deliveredFresh ? "positive" : "caution")}
        />
        <strong>Dashboard</strong>
        <small>{deliveredFresh ? "Fresh within 6s" : "Stale beyond 6s"}</small>
      </div>
    </div>
  );
}
function EvidenceTimeline({ evidence }: { evidence: Evidence[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);
  const shown = showAll ? evidence : evidence.slice(0, 5);
  return (
    <section className="panel evidence-panel" aria-labelledby="evidence-title">
      <div className="panel-heading">
        <div>
          <h2 id="evidence-title">Diagnostic activity</h2>
          <p>Tool observations · select a result to inspect its evidence</p>
        </div>
        <span className="count">{evidence.length} results</span>
      </div>
      <div className="evidence-table-wrap">
        <table className="evidence-table">
          <thead>
            <tr>
              <th scope="col">Diagnostic tool</th>
              <th scope="col">Result</th>
              <th scope="col">Observed</th>
              <th scope="col">
                <span className="sr-only">Inspect evidence</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {shown.map((e) => (
              <React.Fragment key={e.evidence_id}>
                <tr>
                  <th scope="row">{e.tool_name.replaceAll("_", " ")}</th>
                  <td>
                    <span
                      className={
                        e.status === "ok" ? "result-ok" : "warning-text"
                      }
                    >
                      {e.status === "ok" ? "Observed" : e.status}
                    </span>
                  </td>
                  <td>
                    <time dateTime={e.observed_at}>
                      {chartTime(e.observed_at)}
                    </time>
                  </td>
                  <td>
                    <button
                      className="inspect-button"
                      aria-label={`Inspect ${e.tool_name.replaceAll("_", " ")}`}
                      aria-expanded={expanded === e.evidence_id}
                      aria-controls={"result-" + e.evidence_id}
                      onClick={() =>
                        setExpanded(
                          expanded === e.evidence_id ? null : e.evidence_id,
                        )
                      }
                    >
                      {expanded === e.evidence_id ? "−" : "+"}
                    </button>
                  </td>
                </tr>
                <tr
                  id={"result-" + e.evidence_id}
                  hidden={expanded !== e.evidence_id}
                >
                  <td colSpan={4} className="evidence-detail">
                    {expanded === e.evidence_id && (
                      <>
                        <p>
                          Evidence reference <code>{e.evidence_id}</code>
                        </p>
                        <pre tabIndex={0}>
                          {JSON.stringify(e.payload, null, 2)}
                        </pre>
                      </>
                    )}
                  </td>
                </tr>
              </React.Fragment>
            ))}
            {!evidence.length && (
              <tr>
                <td colSpan={4} className="empty">
                  <strong>No diagnostic results yet</strong>
                  <p>
                    Investigate the station to collect acquisition, sample, log,
                    and transport evidence.
                  </p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {!evidence.length && (
        <div className="evidence-guide">
          <h3>Available diagnostic checks</h3>
          <ul>
            <li>Device status and local acquisition</li>
            <li>Delivered samples and device logs</li>
            <li>Publishing and subscription topics</li>
          </ul>
          <p>Checks become evidence only after an investigation runs.</p>
        </div>
      )}
      {evidence.length > 5 && (
        <div className="table-footer">
          <button className="text-button" onClick={() => setShowAll(!showAll)}>
            {showAll
              ? "Show first 5 results"
              : `View all ${evidence.length} results`}
          </button>
        </div>
      )}
    </section>
  );
}
type View = "overview" | "investigations" | "simulator";
const currentView = (): View =>
  window.location.hash === "#investigations"
    ? "investigations"
    : window.location.hash === "#simulator"
      ? "simulator"
      : "overview";
function App() {
  const [view, setView] = useState<View>(currentView);
  const [menuOpen, setMenuOpen] = useState(false);
  useEffect(() => {
    const update = () => {
      setView(currentView());
      setMenuOpen(false);
    };
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);
  function focusInvestigation() {
    document.getElementById("investigation-title")?.focus();
    document
      .getElementById("investigation")
      ?.scrollIntoView({ block: "nearest" });
  }

  const [health, setHealth] = useState<Health | null>(null),
    [samples, setSamples] = useState<Samples>({
      local: [],
      received: [],
      server_time: new Date().toISOString(),
    });
  const [incident, setIncident] = useState<Incident | null>(null),
    [activeId, setActiveId] = useState<string | null>(null);
  const [error, setError] = useState(""),
    [connectionError, setConnectionError] = useState(""),
    [busy, setBusy] = useState(false),
    [scenario, setScenario] = useState("mismatch"),
    [question, setQuestion] = useState("Why are dashboard readings stale?"),
    [paused, setPaused] = useState(false);
  const [history, setHistory] = useState<{ id: string; state: string }[]>([]);
  useEffect(() => {
    let alive = true;
    let timer: ReturnType<typeof setTimeout>;
    async function refresh() {
      try {
        const [h, s, list] = await Promise.all([
          api<Health>("/health"),
          api<Samples>(`/stations/${station}/samples`),
          api<{ id: string; state: string }[]>("/incidents"),
        ]);
        if (!alive) return;
        setHealth(h);
        setSamples(s);
        setHistory(list);
        setConnectionError("");
        const id = activeId === null ? list[0]?.id : activeId;
        if (id) {
          const i = await api<Incident>("/incidents/" + id);
          if (alive) setIncident(i);
        } else setIncident(null);
      } catch (e) {
        if (alive) setConnectionError((e as Error).message);
      } finally {
        if (alive && !paused) timer = setTimeout(refresh, 1000);
      }
    }
    void refresh();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [activeId, paused]);
  async function act(fn: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function start() {
    await act(async () => {
      const i = await api<Incident>("/incidents", {
        station_id: station,
        question,
      });
      setActiveId(i.id);
      setIncident({ ...i, evidence: [], proposal: null, inference: [] });
    });
  }
  async function decide(approve: boolean) {
    await act(async () => {
      await api(
        `/proposals/${incident?.proposal?.id}/${approve ? "approve" : "reject"}`,
        { station_id: station },
      );
      if (activeId) setIncident(await api<Incident>("/incidents/" + activeId));
    });
  }
  const now = new Date(samples.server_time).getTime(),
    received = samples.received.at(-1),
    local = samples.local.at(-1);
  const receivedAge = age(received?.sampled_at, now),
    stale = receivedAge === null || receivedAge > 6;
  const active =
    incident &&
    ["investigating", "awaiting_approval", "repairing", "verifying"].includes(
      incident.state,
    );
  const label = incident?.state.replaceAll("_", " ") || "Ready to investigate";
  const localFresh = !!local && (age(local.sampled_at, now) ?? Infinity) <= 6;
  const investigationPanel = (
    <section
      className={"panel investigation " + (incident?.state || "ready")}
      id="investigation"
      aria-labelledby="investigation-title"
    >
      <div className="panel-heading">
        <div>
          <h2 id="investigation-title" tabIndex={-1}>
            Investigation
          </h2>
          <p>
            {!health
              ? "Confirming inference mode…"
              : health.provider === "meta"
                ? health.model
                : "Deterministic mock fixture"}
          </p>
        </div>
        <span className="badge neutral">
          {!health
            ? "Connecting"
            : health.provider === "meta"
              ? "Meta API"
              : "Mock"}
        </span>
      </div>
      <div className="investigation-body">
        {incident && (
          <div
            className={
              "finding " + (incident.state === "resolved" ? "recovered" : "")
            }
            role="status"
          >
            <div className="finding-title">
              <span
                className={
                  "status-dot " +
                  (incident.state === "resolved" ? "positive" : "")
                }
              />
              <h3>{label}</h3>
            </div>
            <p>{incident.finding || "Inspecting station evidence…"}</p>
            <div className="run-meta">
              <span>{incident.tool_calls} tool calls</span>
              <span>{incident.model_turns} model turns</span>
              <span>
                {incident.provider === "meta" ? "Meta API" : "Mock fixture"}
              </span>
            </div>
            {incident.verification && (
              <div className="progress">
                <progress
                  aria-label="Post-repair verification"
                  max={incident.verification.required}
                  value={Math.min(
                    incident.verification.required,
                    incident.verification.count,
                  )}
                />
                <span>
                  {incident.verification.count} /{" "}
                  {incident.verification.required} post-repair samples
                </span>
              </div>
            )}
          </div>
        )}
        {incident?.proposal && (
          <div className="proposal">
            <div className="proposal-heading">
              <h3>Subscription repair</h3>
              <span className="badge neutral">{incident.proposal.status}</span>
            </div>
            <p>
              Configuration v{incident.proposal.version} · exact topic change
            </p>
            <div className="topic-diff">
              <div className="diff removed">
                <span>− Current subscription</span>
                <code>{incident.proposal.before}</code>
              </div>
              <div className="diff added">
                <span>+ Proposed subscription</span>
                <code>{incident.proposal.after}</code>
              </div>
            </div>
            <small>
              Expires {time(incident.proposal.expires_at)}. Approval applies
              only to this exact change.
            </small>
            <details className="proposal-refs">
              <summary>
                Supporting evidence ({incident.proposal.evidence_ids.length})
              </summary>
              <ul>
                {incident.proposal.evidence_ids.map((id) => (
                  <li key={id}>
                    <code>{id}</code>
                  </li>
                ))}
              </ul>
            </details>
          </div>
        )}
        <details className="question-form" open={!incident || undefined}>
          <summary>
            {incident ? "Investigate another observation" : "Your observation"}
          </summary>
          <label htmlFor="question">What are you observing?</label>
          <textarea
            id="question"
            maxLength={1000}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={!!active}
          />
          <button
            className={
              incident?.state === "awaiting_approval" ? "secondary" : "primary"
            }
            disabled={busy || !!active || !health || !question.trim() || paused}
            onClick={() => void start()}
          >
            {incident?.state === "investigating"
              ? "Collecting evidence…"
              : incident?.state === "verifying"
                ? "Verifying recovery…"
                : "Start investigation"}
            <Icon name="arrow" />
          </button>
          {paused && (
            <p className="field-help">
              Resume station updates to start an investigation.
            </p>
          )}
          {active && (
            <p className="field-help">
              Complete or cancel the current investigation before starting
              another.
            </p>
          )}
        </details>
        {incident?.state === "investigating" && (
          <button
            className="text-button cancel-action"
            disabled={busy}
            onClick={() =>
              void act(async () => {
                await api(`/incidents/${incident.id}/cancel`, {});
                setIncident(await api("/incidents/" + incident.id));
              })
            }
          >
            Cancel investigation
          </button>
        )}
      </div>
      {incident?.state === "awaiting_approval" && (
        <div className="decision">
          <button
            className="primary"
            disabled={busy}
            onClick={() => void decide(true)}
          >
            Approve repair
            <Icon name="check" />
          </button>
          <button
            className="secondary"
            disabled={busy}
            onClick={() => void decide(false)}
          >
            Reject
          </button>
        </div>
      )}
      <div className="provider-note">
        {!health
          ? "Confirming provider and request budget…"
          : health.provider === "meta"
            ? `Live request budget: ${health.live_requests_used} / ${health.live_request_limit}. No automatic fallback.`
            : "Mock inference · not live Meta validation."}
      </div>
    </section>
  );
  const historyControl = (
    <div className="history">
      <label htmlFor="history">Investigation history</label>
      <select
        id="history"
        value={activeId === null ? history[0]?.id || "" : activeId}
        onChange={(e) => setActiveId(e.target.value)}
      >
        <option value="">New investigation</option>
        {history.map((i) => (
          <option key={i.id} value={i.id}>
            {i.id.slice(-6)} · {i.state.replaceAll("_", " ")}
          </option>
        ))}
      </select>
    </div>
  );
  const simulator = (
    <details
      className="demo-controls"
      id="simulator-controls"
      open={view === "simulator" ? true : undefined}
    >
      <summary>
        <span>Simulator controls</span>
        <span className="summary-note">Synthetic station scenarios</span>
      </summary>
      <div className="simulator-body">
        <div>
          <h2>Reset station state</h2>
          <p>
            This interrupts active investigations and invalidates pending
            repairs.
          </p>
        </div>
        <div className="reset-fields">
          <label className="sr-only" htmlFor="scenario">
            Demo scenario
          </label>
          <select
            id="scenario"
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
          >
            <option value="mismatch">Transport mismatch</option>
            <option value="healthy">Healthy station</option>
            <option value="sensor_failure">Sensor read failure</option>
            <option value="unavailable">Unavailable evidence</option>
          </select>
          <button
            className="secondary"
            disabled={busy}
            onClick={() =>
              void act(async () => {
                await api("/demo/reset", { scenario });
                setActiveId("");
                setIncident(null);
                setSamples(await api(`/stations/${station}/samples`));
              })
            }
          >
            Reset demo
          </button>
        </div>
      </div>
    </details>
  );
  return (
    <>
      <nav aria-label="Skip links">
        <a
          className="skip-link"
          href="#main"
          onClick={(e) => {
            e.preventDefault();
            document.getElementById("main")?.focus();
          }}
        >
          Skip to station content
        </a>
      </nav>
      <header className="app-header">
        <Brand />
        <button
          className="menu-toggle secondary"
          aria-expanded={menuOpen}
          aria-controls="workspace-nav"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          {menuOpen ? "Close menu" : "Menu"}
        </button>
        <nav
          id="workspace-nav"
          className={"workspace-nav " + (menuOpen ? "is-open" : "")}
          aria-label="Workspace views"
        >
          <a
            href="#overview"
            aria-current={view === "overview" ? "page" : undefined}
          >
            Overview
          </a>
          <a
            href="#investigations"
            aria-current={view === "investigations" ? "page" : undefined}
          >
            Investigations
          </a>
          {health?.demo_enabled && (
            <a
              href="#simulator"
              aria-current={view === "simulator" ? "page" : undefined}
            >
              Simulator
            </a>
          )}
          <a
            href="https://github.com/RjayBernales/FieldFix/blob/main/docu/SELF_TEST_GUIDE.md"
            target="_blank"
            rel="noreferrer"
          >
            Guide ↗
          </a>
        </nav>
        <span className="mode">
          Simulated station ·{" "}
          {!health
            ? "connecting"
            : health.provider === "meta"
              ? "live Meta inference"
              : "mock inference"}
        </span>
      </header>
      <main id="main" tabIndex={-1} className="workspace" data-view={view}>
        <div className="page-heading">
          <div>
            <h1>
              {view === "overview"
                ? "Station overview"
                : view === "investigations"
                  ? "Investigations"
                  : "Simulator"}
            </h1>
            <p>
              River station 01 <span aria-hidden="true">·</span> Water turbidity{" "}
              <span aria-hidden="true">·</span> <code>{station}</code>
            </p>
          </div>
          {view === "overview" && (
            <button
              className="secondary heading-action"
              disabled={busy || !health || paused || !question.trim()}
              onClick={() => {
                if (active) focusInvestigation();
                else void start();
              }}
            >
              {active
                ? incident?.state === "awaiting_approval"
                  ? "Review repair"
                  : "View investigation"
                : "Investigate station"}
              <Icon name="arrow" />
            </button>
          )}
        </div>
        <div className="station-status">
          <span
            className={"status-label " + (localFresh ? "" : "warning-text")}
          >
            <i
              className={"status-dot " + (localFresh ? "positive" : "caution")}
            />
            {localFresh ? "Device sampling" : "Device samples stale"}
          </span>
          <span className={"status-label " + (stale ? "warning-text" : "")}>
            <i className={"status-dot " + (stale ? "caution" : "positive")} />
            {stale ? "Delivery stale" : "Delivery fresh"}
          </span>
          <span className="updated">
            {paused ? "Paused at" : "Updated"} {time(samples.server_time)}
          </span>
          <button className="text-button" onClick={() => setPaused(!paused)}>
            {paused ? "Resume updates" : "Pause updates"}
          </button>
        </div>
        {paused && (
          <div className="pause-note" role="status">
            Updates paused at {time(samples.server_time)}. Readings and
            freshness are frozen. Resume before investigating.
          </div>
        )}
        {(error || connectionError) && (
          <div className="error" role="alert">
            <span>{error || connectionError}</span>
            <button
              onClick={() => {
                setError("");
                setConnectionError("");
              }}
              aria-label="Dismiss error"
            >
              ×
            </button>
          </div>
        )}
        {view === "overview" && (
          <>
            <div className="work-grid">
              <section
                className="panel telemetry"
                aria-labelledby="telemetry-title"
              >
                <div className="panel-heading">
                  <div>
                    <h2 id="telemetry-title">Station telemetry</h2>
                    <p>Local acquisition versus dashboard delivery</p>
                  </div>
                  <span className="chart-unit">NTU</span>
                </div>
                <div className="chart-legend">
                  <span>
                    <i className="solid-line" />
                    Dashboard received
                  </span>
                  <span>
                    <i className="dashed-line" />
                    Local device
                  </span>
                  <span>
                    <i className="stale-swatch" />
                    Stale interval
                  </span>
                </div>
                <Chart data={samples} now={now} />
                <div className="chart-foot">
                  {stale
                    ? "Delivered samples exceed the 6-second freshness threshold."
                    : "Delivery is fresh. Synthetic readings do not establish environmental safety."}
                </div>
              </section>
              <section
                className="panel station-summary"
                aria-labelledby="readings-title"
              >
                <div className="panel-heading">
                  <h2 id="readings-title">Station readings</h2>
                  <span className="badge neutral">Synthetic</span>
                </div>
                <div
                  className="metrics"
                  role="group"
                  aria-label="Station readings"
                >
                  <article>
                    <div className="metric-label">Dashboard reading</div>
                    <div className="metric-value">
                      {received?.value.toFixed(2) || "—"}
                      <span>NTU</span>
                    </div>
                  </article>
                  <article>
                    <div className="metric-label">Local device</div>
                    <div className="metric-value">
                      {local?.value.toFixed(2) || "—"}
                      <span>NTU</span>
                    </div>
                  </article>
                  <article>
                    <div className="metric-label">Delivery age</div>
                    <div
                      className={
                        "metric-value " + (stale ? "warning-text" : "")
                      }
                    >
                      {receivedAge ?? "—"}
                      <span>sec</span>
                    </div>
                  </article>
                  <article>
                    <div className="metric-label">Investigation</div>
                    <div className="metric-state">
                      {incident ? label : "Ready"}
                    </div>
                    <p>
                      {incident
                        ? `${incident.tool_calls} tool calls`
                        : "No active investigation"}
                    </p>
                  </article>
                </div>
                <div className="path-heading sr-only">
                  Observed delivery path
                </div>
                <DeliveryPath localFresh={localFresh} deliveredFresh={!stale} />
              </section>
              <EvidenceTimeline evidence={incident?.evidence || []} />
              {investigationPanel}
            </div>
            {history.length > 0 && historyControl}
            {health?.demo_enabled && simulator}
          </>
        )}
        {view === "investigations" && (
          <div className="investigations-view">
            {historyControl}
            <div className="review-grid">
              <EvidenceTimeline evidence={incident?.evidence || []} />
              {investigationPanel}
            </div>
          </div>
        )}
        {view === "simulator" && (
          <section className="simulator-view">
            <div className="view-description">
              <h2>Controlled software station</h2>
              <p>
                Choose a reproducible scenario, then return to Overview to
                inspect delivery and investigate. These controls are separate
                from diagnostic tools.
              </p>
            </div>
            {health?.demo_enabled ? (
              simulator
            ) : (
              <p>Simulator controls are disabled for this server.</p>
            )}
          </section>
        )}
        <footer>
          <span>FieldFix · Evidence before action.</span>
          <span>Simulated station · no field deployment.</span>
        </footer>
      </main>
    </>
  );
}
type RecordedRun = {
  recorded_at: string;
  model: string;
  incident: Incident;
  usage: { total_tokens: number };
};
function RecordedPreview() {
  const [run, setRun] = useState<RecordedRun | null>(null);
  const [selected, setSelected] = useState(0);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    fetch("/recorded-run.json")
      .then((r) => {
        if (!r.ok) throw new Error();
        return r.json();
      })
      .then(setRun)
      .catch(() => setFailed(true));
  }, []);
  const names = [
    "get_local_samples",
    "get_received_samples",
    "get_transport_config",
  ];
  const evidence = run?.incident.evidence.find(
    (e) => e.tool_name === names[selected],
  );
  const samples = (evidence?.payload.samples as Sample[] | undefined) || [];
  const latest = samples[samples.length - 1];
  return (
    <section
      className="landing-preview"
      data-ui
      aria-labelledby="preview-title"
    >
      <div className="preview-heading landing-enter">
        <h2 id="preview-title">Inspect the evidence.</h2>
        <span>Recorded genuine Meta run</span>
      </div>
      <p className="preview-caption landing-enter">
        {run
          ? `${run.model} · ${new Date(run.recorded_at).toLocaleDateString("en", { year: "numeric", month: "short", day: "numeric", timeZone: "UTC" })} UTC`
          : "Loading the recorded evidence…"}
      </p>
      <div
        className="preview-tabs landing-enter"
        role="group"
        aria-label="Recorded diagnostic evidence"
      >
        {["Local samples", "Delivered samples", "Transport topics"].map(
          (label, i) => (
            <button
              key={label}
              aria-pressed={selected === i}
              onClick={() => setSelected(i)}
            >
              {label}
            </button>
          ),
        )}
      </div>
      <div className="preview-observation landing-enter" key={selected}>
        {failed ? (
          <p>
            The evidence file is unavailable.{" "}
            <a href="/recorded-demo.html">Open the recorded walkthrough.</a>
          </p>
        ) : evidence ? (
          <>
            {latest ? (
              <>
                <p>
                  {selected === 0
                    ? "Device-side reading"
                    : "Last delivered reading"}
                </p>
                <div className="preview-reading">
                  {latest.value.toFixed(2)} <span>{latest.unit}</span>
                </div>
                <dl>
                  <div>
                    <dt>Original sequence</dt>
                    <dd>{latest.sequence}</dd>
                  </div>
                  <div>
                    <dt>Sampled at</dt>
                    <dd>{latest.sampled_at.slice(11, 19)} UTC</dd>
                  </div>
                </dl>
              </>
            ) : (
              <dl className="preview-topics">
                <div>
                  <dt>Publishing topic</dt>
                  <dd>{String(evidence.payload.publish_topic)}</dd>
                </div>
                <div>
                  <dt>Dashboard subscription</dt>
                  <dd>{String(evidence.payload.subscription_topic)}</dd>
                </div>
              </dl>
            )}
            <p className="preview-ref">Evidence {evidence.evidence_id}</p>
          </>
        ) : (
          <p>Original samples and tool results will appear here.</p>
        )}
      </div>
      <div className="preview-outcome landing-enter">
        <span>Verified outcome</span>
        <strong>
          {run?.incident.verification
            ? `${run.incident.verification.count} / ${run.incident.verification.required} fresh samples`
            : "Recorded recovery"}
        </strong>
      </div>
      <p className="preview-footnote landing-enter">
        A recorded observation, available without model calls.{" "}
        <a href="/recorded-demo.html">Read the complete trace ↗</a>
      </p>
    </section>
  );
}
type SessionStatus = {
  hosted_demo: boolean;
  authenticated: boolean;
  expires_in?: number;
  provider?: "meta" | "mock";
  requires_access_code?: boolean;
  public_live?: boolean;
};
function SessionGate() {
  const [status, setStatus] = useState<SessionStatus | null>(null),
    [accessCode, setAccessCode] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function check() {
    setError("");
    try {
      const r = await fetch("/api/session", {
        signal: AbortSignal.timeout(12000),
      });
      if (r.status === 404) {
        setStatus({ hosted_demo: false, authenticated: true });
        return;
      }
      if (!r.ok)
        throw new Error(
          "Cannot reach the demo server. Retry after it wakes up.",
        );
      setStatus(await r.json());
    } catch {
      setError(
        "The FieldFix server is starting or unavailable. Check the backend, then retry. Free hosting may need time to wake up.",
      );
    }
  }
  useEffect(() => {
    void check();
    const expired = () =>
      setStatus((s) => (s ? { ...s, authenticated: false } : null));
    window.addEventListener("fieldfix-session-expired", expired);
    return () =>
      window.removeEventListener("fieldfix-session-expired", expired);
  }, []);
  async function start() {
    setBusy(true);
    setError("");
    try {
      setStatus(
        await api<SessionStatus>("/session", { access_code: accessCode }),
      );
      setAccessCode("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function end() {
    setBusy(true);
    try {
      setStatus(await api<SessionStatus>("/session/end", {}));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (!status || !status.authenticated) {
    return (
      <main className="landing">
        <header className="landing-header">
          <Brand context="" />
          <nav aria-label="About FieldFix">
            <a href="#workflow">How it works</a>
            <a href="#validation">Evidence</a>
            <a href="#demo-entry">Open demo</a>
          </nav>
        </header>
        <section
          className="landing-hero"
          aria-label="FieldFix live demonstration"
        >
          <div className="landing-copy">
            <h1 className="landing-enter">
              Find the fault.
              <br />
              Prove the fix.
            </h1>
            <p className="landing-lede landing-enter">
              FieldFix uses Meta Muse to investigate monitoring-station faults,
              propose exact repairs, and verify that fresh data returns.
            </p>
            <div className="landing-mode landing-enter">
              <span className="status-dot" />
              <span>
                {status?.hosted_demo
                  ? status.provider === "meta"
                    ? "Live Meta inference · simulated station"
                    : "Mock inference · simulated station"
                  : "Connecting to confirm inference mode"}
              </span>
            </div>
            <div className="landing-entry landing-enter" id="demo-entry">
              {error && (
                <p className="error" role="alert">
                  {error}
                </p>
              )}
              {status ? (
                <form
                  className="session-login"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void start();
                  }}
                >
                  {status.requires_access_code && (
                    <label htmlFor="demo-access-code">
                      Demo access code
                      <input
                        id="demo-access-code"
                        type="password"
                        autoComplete="current-password"
                        value={accessCode}
                        onChange={(e) => setAccessCode(e.target.value)}
                        maxLength={200}
                        required
                        aria-describedby="demo-access-help"
                      />
                      <small id="demo-access-help">
                        Use the private code shared by the presenter. Never
                        enter a Meta API key.
                      </small>
                    </label>
                  )}
                  <button className="primary" disabled={busy} type="submit">
                    {busy
                      ? "Starting your station…"
                      : status.provider === "meta"
                        ? "Start live demo"
                        : "Start my demo session"}
                    <Icon name="arrow" />
                  </button>
                </form>
              ) : (
                <button
                  className="primary"
                  disabled={!error}
                  onClick={() => void check()}
                >
                  {error ? "Retry connection" : "Connecting to server…"}
                </button>
              )}
            </div>
            <p className="landing-limits landing-enter">
              {status?.requires_access_code
                ? "This private demo requires the presenter's access code."
                : status?.provider === "meta"
                  ? "No account or access code. Two investigations per session, within the shared API budget."
                  : "An isolated demo session. Provider mode is confirmed by the server."}
            </p>
            <a
              className="landing-recorded landing-enter"
              href="/recorded-demo.html"
            >
              Review the recorded Meta run ↗
            </a>
          </div>
          <RecordedPreview />
        </section>
        <section
          id="workflow"
          className="landing-workflow"
          aria-labelledby="workflow-title"
        >
          <h2 id="workflow-title" className="landing-enter">
            Evidence to recovery.
          </h2>
          <p className="landing-section-copy">
            A frozen dashboard is a symptom. FieldFix follows the data before
            suggesting a repair.
          </p>
          <ol>
            <li>
              <strong>Observe</strong>
              <p>Compare original device and delivered samples.</p>
            </li>
            <li>
              <strong>Investigate</strong>
              <p>Meta chooses typed diagnostic tools and cites observations.</p>
            </li>
            <li>
              <strong>Approve</strong>
              <p>The technician authorizes one exact configuration change.</p>
            </li>
            <li>
              <strong>Verify</strong>
              <p>Three distinct fresh samples prove delivery has recovered.</p>
            </li>
          </ol>
          <div className="landing-observations">
            <figure>
              <a
                href="/evidence/navy-tool-evidence.png"
                target="_blank"
                rel="noreferrer"
              >
                <img
                  src="/evidence/navy-tool-evidence.png"
                  width="1440"
                  height="1000"
                  loading="lazy"
                  alt="Actual diagnostic tool observations and original local sample payload in FieldFix"
                />
              </a>
              <figcaption>
                Observed tool payloads. Original samples and evidence references
                are available to inspect.
              </figcaption>
            </figure>
            <figure>
              <a
                href="/evidence/navy-repair-verification.png"
                target="_blank"
                rel="noreferrer"
              >
                <img
                  src="/evidence/navy-repair-verification.png"
                  width="1440"
                  height="1000"
                  loading="lazy"
                  alt="Actual approved subscription-topic correction and verified recovery in FieldFix"
                />
              </a>
              <figcaption>
                The exact approved change and the recorded recovery check. Open
                either capture at full size.
              </figcaption>
            </figure>
          </div>
        </section>
        <section
          id="validation"
          className="landing-proof"
          aria-labelledby="validation-title"
        >
          <div>
            <h2 id="validation-title">Proof you can inspect.</h2>
            <p>
              Real model responses, documented checks, and explicit limits. All
              stations and transport are software simulations.
            </p>
            <a href="/recorded-demo.html">Open the evidence report ↗</a>
          </div>
          <div className="landing-proof-list">
            <p>
              <strong>Genuine Meta tool use</strong>
              <span>
                Inspect the returned model metadata and the original diagnostic
                tool results.
              </span>
            </p>
            <p>
              <strong>Technician control</strong>
              <span>
                Exact approval is required before the subscription changes.
              </span>
            </p>
            <p>
              <strong>Deterministic recovery</strong>
              <span>
                Recovery requires distinct post-repair samples and a fresh
                latest reading.
              </span>
            </p>
          </div>
          <figure className="landing-capture">
            <a
              href="/evidence/navy-dashboard.png"
              target="_blank"
              rel="noreferrer"
            >
              <img
                src="/evidence/navy-dashboard.png"
                alt="Actual FieldFix navy dashboard with station telemetry, diagnostic observations and repair review"
                width="1440"
                height="1100"
                loading="lazy"
              />
            </a>
            <figcaption>
              Actual application capture · software station. Open the image to
              inspect it at full size.
            </figcaption>
          </figure>
        </section>
        <footer className="landing-footer">
          <span>FieldFix · Evidence before action.</span>
          <span>Software station. No field-deployment or safety claim.</span>
        </footer>
      </main>
    );
  }
  return (
    <>
      {status.hosted_demo && (
        <aside className="hosted-banner" aria-label="Demo session">
          <span>
            {status.provider === "meta"
              ? "Live Meta demo · shared request budget"
              : "Free online demo · mock inference"}{" "}
            · isolated temporary station
          </span>
          <a href="/recorded-demo.html" target="_blank" rel="noreferrer">
            Recorded Meta evidence ↗
          </a>
          <button disabled={busy} onClick={() => void end()}>
            End my session
          </button>
        </aside>
      )}
      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}
      <App />
    </>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <SessionGate />
  </React.StrictMode>,
);
