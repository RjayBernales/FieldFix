# Try FieldFix yourself

This guide takes about 10–15 minutes. You will deliberately freeze a dashboard, examine the evidence, reject a repair, approve a new repair, and watch the system prove recovery.

**Every station reading is synthetic.** The free online app uses clearly labeled mock inference and makes no Meta API calls. It runs the same Python simulator, tools, approval rules, database, and recovery verifier. Genuine Meta inference was separately validated locally; its actual results and failures are in [VALIDATION.md](VALIDATION.md).

## Open the app

Use the **App / live preview** link at the top of the repository README. If the free server has been asleep, give it time to start. If the README calls the link temporary, it works only while the preview host/tunnel is running; do not treat it as permanent production hosting.

On the free hosted version, click **Start my demo session**. No account or API key is needed. Your browser receives its own temporary station session. Other visitors cannot read your incidents or approve your proposals. It expires after 30 minutes; a service restart also resets demo data. Do not enter personal data or secrets.

On the local version, follow README setup/start commands and open http://127.0.0.1:5173. Local mode opens the dashboard directly. Use the provider badge to confirm whether you selected mock or live Meta inference.

## 1. Understand the dashboard

| Area | What it tells you |
| --- | --- |
| Dashboard reading | The latest sample actually delivered to the dashboard, with its original sampling age |
| Local device reading | The device continues sampling independently of dashboard delivery |
| Chart | Dashed local acquisition versus solid delivered readings; shaded intervals indicate stale dashboard data |
| Evidence timeline | The actual structured results used in this investigation, with evidence IDs |
| Assistant | Finding, exact repair proposal, approval/rejection, and recovery progress |
| Development controls | Deliberately configure a simulated fault; these controls are not agent tools |

NTU is the displayed turbidity unit. FieldFix does not turn these readings into environmental safety advice.

## 2. Create the primary fault

1. At the bottom, choose **Transport mismatch** and click **Reset demo**.
2. Confirm the previous investigation view clears to **New investigation**.
3. Wait about 6–10 seconds. The **local device reading** should keep changing, while the **dashboard reading** remains old and shows **stale**.
4. The chart should show the difference between continued acquisition and broken delivery.

What is happening: the simulator generates a sample every two seconds, but its publishing topic differs from the dashboard subscription. The in-process router delivers only when they match. This is software transport, not an MQTT broker.

## 3. Investigate and inspect the evidence

1. Leave the question as “Why are dashboard readings stale?” or enter a short technician observation.
2. Click **Investigate station** once. The button disables while it is running.
3. Expand several **Inspect result** rows in the evidence timeline:
   - **Station status**: heartbeat/connection.
   - **Local samples**: recent sampling timestamps and sequences.
   - **Received samples**: older delivered readings.
   - **Transport config**: publishing topic, subscription topic, and configuration version.
4. Read the proposal's exact **Before** and **After** topics. It should correct the subscription to the observed publishing topic and cite supporting evidence.

In mock mode, tool selection is a deterministic offline fixture. In local Meta mode, the hosted model chooses the tools through real API calls. Neither mode receives hidden simulator fault labels in its diagnostic tool inputs.

**Before approval, the proposal must not change configuration.** Watch briefly: the dashboard should remain stale while local samples continue.

## 4. Reject a repair first

1. Click **Reject**.
2. Expect an **unresolved** finding explaining that no configuration was changed.
3. The dashboard should remain stale. Rejection is a real workflow outcome, not a hidden repair.
4. Select this record in **Investigation history** to revisit its evidence. Each record identifies its provider.

## 5. Approve and verify recovery

1. Reset **Transport mismatch** again and start a new investigation.
2. Inspect the new proposal. Approve only if its exact topic change is the one you intend.
3. Click **Approve repair** once.
4. The incident should move into **verifying**, and delivered readings should resume.
5. Watch the counter reach **3 / 3 post-repair samples**. With two-second sampling, this normally takes around six seconds after approval.
6. Expect **resolved** only after those distinct samples are received, newer than the pre-repair sequence, sampled after the repair, and with a fresh latest timestamp.

A configuration write alone is insufficient. If delivery does not recover within 20 seconds, the verifier leaves the incident unresolved. Expired, stale-version, replayed, wrong-station, and invalidated approvals are rejected server-side. Do not infer safety of real water from a successful software repair.

## 6. Try the healthy baseline

1. Select **Healthy station**, reset, and investigate.
2. Expect fresh local and dashboard samples, a no-fault finding, and **no repair proposal**.
3. This MVP uses terminal state **unresolved** for a healthy no-repair investigation; read the “No fault found” finding. The `resolved` state is reserved for verified recovery after repair.

## 7. Try the other simulated problems

- **Sensor read failure**: reset and investigate. Heartbeat remains active, acquisition evidence fails, and the assistant should request a physical check rather than propose a topic repair.
- **Unavailable evidence**: reset and investigate. Some tools return unavailable. Expect a statement of missing evidence and no fabricated repair.

The free online fixture reports these safe outcomes deterministically. Actual hosted-model validation of these two secondary faults is not claimed.

## 8. Check session and interface behavior

- Click **Pause updates**. A visible notice should explain that displayed readings/freshness are frozen, and investigation is disabled until **Resume updates**.
- Resize the browser or use a phone; essential controls should remain available.
- Open an incognito/private window and start a second online session. Its history starts empty and its reset must not affect your first window.
- Click **End my session** on the free online app. That browser's station data is discarded, and the start screen returns. Other visitors' sessions continue.
- If a request limit is reached, wait as instructed. A session permits up to ten investigations; end it/start a new session for additional testing. These limits protect the free demonstration.

## Use genuine Meta inference locally

The online free demo is intentionally mock-only. To reproduce the real model path, configure a valid **replacement** key in your ignored local `.env`, set `FIELDFIX_PROVIDER=meta`, and restart the local backend using README instructions. Never put a key in `.env.example`, the browser, screenshots, or chat.

You should then see **Simulated station · live Meta inference** and the configured model. Repeat the same fault/approval/recovery steps. Requests consume the persistent budget; inspect `/health` or the UI budget display before testing. Previous validation used 16 of the original 30 reserved requests. Review usage before increasing the limit. No automatic mock fallback occurs after a provider error.

## What to capture for a useful bug report

Record your browser, provider badge, selected scenario, incident ID, expected versus observed behavior, and a screenshot with no credentials or personal information. Keep the original timestamps and evidence IDs. Do not describe a mock result as Meta behavior or a simulated station as a field deployment.

For the competition video, use [DEMO_SCRIPT.md](DEMO_SCRIPT.md) and state the actual mode throughout. Do not submit the entry or upload a video until you choose to do so yourself.
