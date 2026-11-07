/* Connects the Overview app to the ML engine (ml/api.py).
   - Future tab: real A/B/C timelines, person details and recommendations from the engine
   - Report tab: link to the full printable A4 report
   - Falls back to the built-in example data if the engine isn't running. */
(function () {
  const API = location.protocol.startsWith("http") ? "" : "http://localhost:8001";
  const params = new URLSearchParams(location.search);
  let CID = params.get("customer") || "jordan";

  // Overview question index -> ML answer field, by option index
  const MAP = {
    1: ["worry", ["Unexpected bills", "Not saving enough", "Debt", "Not saving enough"]],
    2: ["goal", ["Build savings", "Buy a home", "Manage monthly expenses", "Manage monthly expenses"]],
    3: ["life_changes", ["New child", "New job", "Moving home", "None"]],
    4: ["shock_500", ["Savings", "Credit card", "Borrowing from family/friends", "I couldn't cover it"]],
  };
  function query() {
    const q = new URLSearchParams();
    for (const [i, [k, vals]] of Object.entries(MAP)) if (ans[+i] !== undefined) q.set(k, vals[ans[+i]]);
    const sup = [];
    if (ans[0] === 2) sup.push("I find it hard to keep track of bills");   // "managing money is hard"
    if (ans[8] === 0) sup.push("I prefer simple explanations");            // "explain things simply"
    if (sup.length) q.set("support_needs", sup.join(","));
    return q.toString();
  }

  let ML = null, lastKey = null, loading = null;
  function load() {
    const key = CID + "?" + query();
    if (ML && key === lastKey) return Promise.resolve(ML);
    if (loading && loading.key === key) return loading.p;
    const p = fetch(`${API}/customers/${CID}/timelines?${query()}`)
      .then(r => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(d => { ML = d; lastKey = key; apply(); return d; })
      .catch(e => { console.warn("ML engine not reachable, showing example data.", e); setStatus(false); })
      .finally(() => { loading = null; });
    loading = { key, p };
    return p;
  }

  function apply() {
    SAM.name = ML.person.name;
    Object.assign(SAM.now, ML.person.now);
    ACTS.splice(0, ACTS.length, ...ML.actions);
    PLAN.clear();
    setStatus(true);
    reportLink();
    const badge = document.querySelector("#s-future .badge");
    if (badge) badge.textContent = `Live forecast: ${ML.person.name}, ${ML.person.persona}`;
    const ph = document.querySelector("#s-future .ph");
    if (ph) ph.hidden = true;
  }

  const mock = TimeTravelEngine.getTimelines.bind(TimeTravelEngine);
  TimeTravelEngine.getTimelines = a => (ML ? ML.timelines : mock(a));

  const origDraw = window.drawTl;
  window.drawTl = function () {
    origDraw();
    const d = document.querySelector("#chartdesc");
    if (ML && d) d.textContent = d.textContent.replace("Example data.", "Live data.");
  };

  const origGo = window.go;
  window.go = function (id) {
    origGo(id);
    if (id === "future") load().then(() => { if (!document.querySelector("#s-future").hidden) drawTl(); });
    if (id === "report") reportLink();
  };

  // ---- small UI additions
  function setStatus(ok) {
    const el = document.querySelector("#ml-status");
    if (el) el.textContent = ok ? `✅ Live data: ${ML.person.name} (${ML.person.persona})` : "ℹ️ Example data (ML engine not running)";
  }
  function reportLink() {
    const box = document.querySelector("#ml-report");
    if (!box) return;
    const url = `${API}/customers/${CID}/report?${query()}`;
    box.innerHTML = `<div class="card"><h3 style="margin-top:0">🖨️ Your full forecast report</h3>
      <p class="lead">Four A4 pages: your 12-month forecast, alerts written for you, what's coming up, and your action plan.</p>
      <a class="btn pri" href="${url}" target="_blank" rel="noopener">Open my printable report →</a></div>`;
  }

  document.addEventListener("DOMContentLoaded", init);
  if (document.readyState !== "loading") init();
  let inited = false;
  function init() {
    if (inited) return; inited = true;
    const main = document.querySelector("#main");
    const bar = document.createElement("div");
    bar.className = "card";
    bar.style.cssText = "display:flex;flex-wrap:wrap;gap:.6rem;align-items:center;margin-bottom:1rem";
    bar.innerHTML = `<label for="ml-cust"><b>Demo customer</b></label>
      <select id="ml-cust" style="font:inherit;padding:.3rem .5rem">
        <option value="jordan">Jordan – hours cut, one child</option>
        <option value="priya">Priya – student</option>
        <option value="margaret">Margaret – retired</option></select>
      <span id="ml-status" class="lead" style="margin:0">Loading forecast…</span>`;
    main && main.prepend(bar);
    const sel = document.querySelector("#ml-cust");
    sel.value = CID;
    sel.onchange = () => { CID = sel.value; ML = null; load().then(() => { if (!document.querySelector("#s-future").hidden) drawTl(); }); };
    // links to the rest of the team's apps (started by ./start.sh)
    const link = (sel, html) => { const el = document.querySelector(sel); if (el) { const d = document.createElement("div"); d.className = "card"; d.innerHTML = html; el.append(d); } };
    link("#s-learn", `<h3 style="margin-top:0">🎓 More lessons</h3><p class="lead">Life-situation journeys with scenario quizzes and progress tracking.</p>
      <a class="btn pri" href="http://127.0.0.1:3000" target="_blank" rel="noopener">Open the learning module →</a>`);
    link("#s-support", `<h3 style="margin-top:0">📬 Prefer paper and people?</h3><p class="lead">A plain-English monthly letter, and a helper who answers your questions.</p>
      <a class="btn pri" href="http://localhost:5173" target="_blank" rel="noopener">Open dashboard &amp; letters →</a>`);
    const rep = document.querySelector("#s-report");
    if (rep) { const d = document.createElement("div"); d.id = "ml-report"; rep.prepend(d); }
    load().then(() => { const h = location.hash.slice(1); if (["future", "report", "support", "wrapped", "learn"].includes(h)) go(h); });
  }
})();
