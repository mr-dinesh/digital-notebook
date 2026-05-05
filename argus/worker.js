export default {
  async fetch(request, env) {
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    const url = new URL(request.url);

    // Serve the Argus HTML app at root
    if (request.method === "GET" && (url.pathname === "/" || url.pathname === "/index.html")) {
      const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Argus — Argument Intelligence</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&family=JetBrains+Mono:wght@300;400;500&display=swap');

  :root {
    --bg: #0d0d0f;
    --surface: #16161a;
    --surface2: #1e1e24;
    --border: rgba(255,255,255,0.08);
    --border2: rgba(255,255,255,0.14);
    --text: #e8e6e1;
    --muted: #6b6975;
    --amber: #e8a020;
    --teal: #2ec4b6;
    --accent: #6c63ff;
    --danger: #e05252;
    --success: #2ec47a;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Syne', sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 18px 20px;
    border-bottom: 1px solid var(--border);
  }

  .logo { display: flex; align-items: center; gap: 10px; }

  .logo-eye {
    width: 26px; height: 26px; border-radius: 50%;
    border: 1.5px solid var(--accent);
    display: flex; align-items: center; justify-content: center;
  }
  .logo-eye::after {
    content: ''; width: 8px; height: 8px;
    border-radius: 50%; background: var(--accent);
  }

  .logo-name { font-size: 17px; font-weight: 700; letter-spacing: 0.08em; }
  .logo-tag  { font-size: 10px; color: var(--muted); letter-spacing: 0.05em; font-family: 'JetBrains Mono', monospace; }

  .header-right { display: flex; align-items: center; gap: 8px; }
  .status-dot   { width: 7px; height: 7px; border-radius: 50%; background: var(--success); }
  .status-label { font-size: 10px; color: var(--muted); font-family: 'JetBrains Mono', monospace; }

  main { flex: 1; padding: 24px 20px; max-width: 900px; width: 100%; margin: 0 auto; }

  .input-label {
    font-size: 10px; letter-spacing: 0.12em; color: var(--muted);
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 8px; display: flex; align-items: center; gap: 8px;
  }

  .mode-badge {
    display: inline-flex; align-items: center;
    padding: 2px 8px; border-radius: 4px;
    font-size: 10px; letter-spacing: 0.1em; font-weight: 600;
  }
  .mode-claim   { background: rgba(108,99,255,0.15); color: var(--accent);  border: 1px solid rgba(108,99,255,0.3); }
  .mode-url     { background: rgba(46,196,182,0.12); color: var(--teal);    border: 1px solid rgba(46,196,182,0.25); }
  .mode-article { background: rgba(232,160,32,0.12); color: var(--amber);   border: 1px solid rgba(232,160,32,0.25); }

  textarea {
    width: 100%; min-height: 110px;
    background: var(--surface); border: 1px solid var(--border2);
    border-radius: 10px; padding: 14px 16px;
    color: var(--text); font-size: 14px;
    font-family: 'JetBrains Mono', monospace;
    resize: vertical; outline: none;
    transition: border-color 0.2s; line-height: 1.6;
  }
  textarea::placeholder { color: var(--muted); }
  textarea:focus { border-color: var(--accent); }

  .input-footer {
    display: flex; align-items: center; justify-content: space-between;
    margin-top: 10px; flex-wrap: wrap; gap: 8px;
  }

  .chips { display: flex; gap: 6px; flex-wrap: wrap; }

  .chip {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 6px; padding: 4px 10px;
    font-size: 11px; color: var(--muted); cursor: pointer;
    font-family: 'JetBrains Mono', monospace; transition: all 0.15s;
  }
  .chip:hover { border-color: var(--border2); color: var(--text); }

  .submit-btn {
    background: var(--accent); border: none; border-radius: 8px;
    padding: 10px 22px; color: #fff;
    font-size: 14px; font-weight: 600; font-family: 'Syne', sans-serif;
    cursor: pointer; transition: opacity 0.15s; letter-spacing: 0.04em;
  }
  .submit-btn:hover { opacity: 0.88; }
  .submit-btn:disabled { opacity: 0.35; cursor: not-allowed; }

  .thesis-bar {
    display: none;
    background: var(--surface); border: 1px solid var(--border2);
    border-radius: 8px; padding: 12px 16px; margin: 20px 0 14px;
    font-size: 12px; font-family: 'JetBrains Mono', monospace; line-height: 1.5;
  }
  .thesis-bar.visible { display: block; }
  .thesis-label { font-size: 9px; letter-spacing: 0.12em; color: var(--muted); margin-bottom: 5px; }

  .panels { display: none; flex-direction: column; gap: 12px; }
  .panels.visible { display: flex; }

  .panel { background: var(--surface); border-radius: 12px; border: 1px solid var(--border); }

  .panel-header {
    padding: 14px 18px 10px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 10px;
  }

  .panel-icon { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
  .panel-steelman  .panel-icon { background: var(--teal); }
  .panel-strawman  .panel-icon { background: var(--danger); }
  .panel-synthesis .panel-icon { background: var(--amber); }

  .panel-title { font-size: 12px; font-weight: 600; letter-spacing: 0.06em; }
  .panel-num   { font-size: 10px; color: var(--muted); font-family: 'JetBrains Mono', monospace; margin-left: auto; }

  .panel-body {
    padding: 16px 18px; font-size: 13px; line-height: 1.8;
    color: var(--text); font-family: 'JetBrains Mono', monospace;
    white-space: pre-wrap; word-break: break-word;
  }

  .field-label {
    font-size: 9px; letter-spacing: 0.1em; color: var(--muted);
    margin-top: 14px; margin-bottom: 4px; display: block;
  }

  .loading-state { display: none; text-align: center; padding: 48px 0; }
  .loading-state.visible { display: block; }

  .loader-ring {
    width: 32px; height: 32px;
    border: 2px solid var(--border2); border-top-color: var(--accent);
    border-radius: 50%; animation: spin 0.8s linear infinite;
    margin: 0 auto 12px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .loader-text { font-size: 12px; color: var(--muted); font-family: 'JetBrains Mono', monospace; }

  .error-bar {
    display: none;
    background: rgba(224,82,82,0.08); border: 1px solid rgba(224,82,82,0.25);
    border-radius: 8px; padding: 12px 16px; margin: 14px 0;
    font-size: 12px; font-family: 'JetBrains Mono', monospace;
    color: var(--danger); white-space: pre-wrap; line-height: 1.6;
  }
  .error-bar.visible { display: block; }

  .export-row { display: none; justify-content: flex-end; margin-top: 16px; padding-bottom: 32px; }
  .export-row.visible { display: flex; }

  .export-btn {
    background: transparent; border: 1px solid var(--border2);
    border-radius: 8px; padding: 8px 16px; color: var(--muted);
    font-size: 12px; font-family: 'Syne', sans-serif; cursor: pointer; transition: all 0.15s;
  }
  .export-btn:hover { color: var(--text); border-color: var(--text); }
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-eye"></div>
    <div>
      <div class="logo-name">ARGUS</div>
      <div class="logo-tag">argument intelligence · workers ai</div>
    </div>
  </div>
  <div class="header-right">
    <div class="status-dot"></div>
    <div class="status-label">llama-3.3-70b · groq free tier</div>
  </div>
</header>

<main>
  <div style="margin-bottom: 24px;">
    <div class="input-label">
      INPUT &nbsp;·&nbsp;
      <span class="mode-badge mode-claim" id="modeBadge">CLAIM</span>
    </div>
    <textarea id="mainInput" placeholder="Paste a claim, a URL, or an article — Argus figures out the rest."></textarea>
    <div class="input-footer">
      <div class="chips">
        <div class="chip" data-example="Zero trust architecture eliminates insider threat risk">zero trust</div>
        <div class="chip" data-example="Technical understanding is neither necessary nor sufficient for good security posture">security posture</div>
        <div class="chip" data-example="AI will make junior developers obsolete within five years">AI + devs</div>
      </div>
      <button class="submit-btn" id="submitBtn">Analyse</button>
    </div>
  </div>

  <div class="error-bar" id="errorBar"></div>

  <div class="loading-state" id="loadingState">
    <div class="loader-ring"></div>
    <div class="loader-text" id="loaderText">analysing…</div>
  </div>

  <div class="thesis-bar" id="thesisBar">
    <div class="thesis-label">ARGUS READ THIS AS</div>
    <div id="thesisText"></div>
  </div>

  <div class="panels" id="panels">
    <div class="panel panel-steelman">
      <div class="panel-header">
        <div class="panel-icon"></div>
        <div class="panel-title">Steelman</div>
        <div class="panel-num">01</div>
      </div>
      <div class="panel-body" id="steelmanBody"></div>
    </div>
    <div class="panel panel-strawman">
      <div class="panel-header">
        <div class="panel-icon"></div>
        <div class="panel-title">Strawman</div>
        <div class="panel-num">02</div>
      </div>
      <div class="panel-body" id="strawmanBody"></div>
    </div>
    <div class="panel panel-synthesis">
      <div class="panel-header">
        <div class="panel-icon"></div>
        <div class="panel-title">Synthesis</div>
        <div class="panel-num">03</div>
      </div>
      <div class="panel-body" id="synthesisBody"></div>
    </div>
  </div>

  <div class="export-row" id="exportRow">
    <button class="export-btn" id="exportBtn">Export to markdown</button>
  </div>
</main>

<script>
const WORKER = 'https://argus-proxy.mrdinesh.workers.dev';

const $ = id => document.getElementById(id);
const mainInput    = $('mainInput');
const submitBtn    = $('submitBtn');
const modeBadge    = $('modeBadge');
const thesisBar    = $('thesisBar');
const thesisText   = $('thesisText');
const errorBar     = $('errorBar');
const loadingState = $('loadingState');
const loaderText   = $('loaderText');
const panels       = $('panels');
const exportRow    = $('exportRow');
const exportBtn    = $('exportBtn');

// -- MODE DETECTION ----------------------------------------
function detectMode(v) {
  v = v.trim();
  if (v.startsWith('http://') || v.startsWith('https://')) return 'url';
  if (v.length > 100) return 'article';
  return 'claim';
}

mainInput.addEventListener('input', () => {
  const m = detectMode(mainInput.value);
  modeBadge.textContent = m.toUpperCase();
  modeBadge.className = 'mode-badge mode-' + m;
});

mainInput.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); run(); }
});

submitBtn.addEventListener('click', run);

document.querySelectorAll('.chip').forEach(c =>
  c.addEventListener('click', () => {
    mainInput.value = c.dataset.example;
    mainInput.dispatchEvent(new Event('input'));
  })
);

// -- HTML → TEXT -------------------------------------------
function htmlToText(html) {
  const doc = new DOMParser().parseFromString(html, 'text/html');
  ['script','style','nav','footer','header','aside','noscript']
    .forEach(t => doc.querySelectorAll(t).forEach(el => el.remove()));
  return (doc.body.innerText || doc.body.textContent || '')
    .replace(/\s+/g, ' ').trim().slice(0, 6000);
}

// -- RUN ---------------------------------------------------
async function run() {
  const raw = mainInput.value.trim();
  if (!raw) return;

  const mode = detectMode(raw);
  setError('');
  setLoading(true, 'detecting input…');
  panels.classList.remove('visible');
  thesisBar.classList.remove('visible');
  exportRow.classList.remove('visible');
  submitBtn.disabled = true;

  let content = raw;

  try {
    if (mode === 'url') {
      setLoading(true, 'fetching article…');
      const res = await fetch(\`\${WORKER}/fetch\`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: raw }),
      });
      const data = await res.json();
      if (!data.ok) throw new Error('Fetch failed: ' + data.error);
      content = htmlToText(data.html);
      if (!content || content.length < 80)
        throw new Error('Could not extract text from that URL.\nPaste the article text directly instead.');
    }

    setLoading(true, 'stress-testing…');

    const input = mode === 'url'
      ? \`Article fetched from \${raw}:\n\n\${content}\`
      : mode === 'article'
        ? \`Pasted article or notes:\n\n\${content}\`
        : \`Claim to stress-test: \${content}\`;

    const res = await fetch(\`\${WORKER}/analyse\`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input }),
    });

    const data = await res.json();
    if (!data.ok) throw new Error(data.error + (data.raw ? '\n\nRaw:\n' + data.raw : ''));

    const result = data.result;

    thesisText.textContent = result.core_thesis || '—';
    thesisBar.classList.add('visible');

    renderPanel('steelmanBody', [
      ['', result.steelman],
      ['CRUX', result.steelman_crux],
    ]);
    renderPanel('strawmanBody', [
      ['', result.strawman],
      ['FATAL OBJECTION', result.strawman_crux],
    ]);
    renderPanel('synthesisBody', [
      ['', result.synthesis],
      ['REAL CRUX', result.real_crux],
      ['WHAT WOULD FLIP IT', result.evidence_that_changes_it],
      ['ACTIONABLE', result.actionable],
    ]);

    panels.classList.add('visible');
    exportRow.classList.add('visible');
    submitBtn._lastResult = result;
    submitBtn._lastInput  = raw;

  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
    submitBtn.disabled = false;
  }
}

// -- HELPERS -----------------------------------------------
function renderPanel(id, fields) {
  $(id).innerHTML = fields.map(([label, text]) => {
    if (!text) return '';
    if (!label) return \`<span>\${esc(text)}</span>\`;
    return \`<span class="field-label">\${label}</span><span>\${esc(text)}</span>\`;
  }).join('');
}

const esc = s => String(s || '')
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

function setLoading(on, msg) {
  loadingState.classList.toggle('visible', on);
  if (msg) loaderText.textContent = msg;
}

function setError(msg) {
  errorBar.textContent = msg;
  errorBar.classList.toggle('visible', !!msg);
}

// -- EXPORT ------------------------------------------------
exportBtn.addEventListener('click', async () => {
  const r = submitBtn._lastResult;
  if (!r) return;
  const md = \`# Argus Analysis\n\n**Input:** \${(submitBtn._lastInput||'').slice(0,120)}\n**Core thesis:** \${r.core_thesis}\n\n## ✦ Steelman\n\${r.steelman}\n**Crux:** \${r.steelman_crux}\n\n## ✦ Strawman\n\${r.strawman}\n**Fatal objection:** \${r.strawman_crux}\n\n## ✦ Synthesis\n\${r.synthesis}\n**Real crux:** \${r.real_crux}\n**What would flip it:** \${r.evidence_that_changes_it}\n**Actionable:** \${r.actionable}\`;
  try {
    await navigator.clipboard.writeText(md);
    const o = exportBtn.textContent;
    exportBtn.textContent = 'Copied ✓';
    setTimeout(() => exportBtn.textContent = o, 2000);
  } catch { alert('Copy failed — check clipboard permissions.'); }
});
</script>
</body>
</html>
`;
      return new Response(html, {
        headers: { "Content-Type": "text/html;charset=UTF-8" },
      });
    }

    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405, headers: corsHeaders });
    }

    // ROUTE: /fetch
    if (url.pathname === "/fetch") {
      const limited = await rateLimit(env, request, "/fetch", 20);
      if (limited) return json({ ok: false, error: "Rate limit exceeded. Try again in a minute." }, 429, corsHeaders);
      let body;
      try { body = await request.json(); } catch {
        return json({ ok: false, error: "Invalid JSON" }, 400, corsHeaders);
      }
      const target = body.url;
      if (!target || !target.startsWith("https://")) {
        return json({ ok: false, error: "Missing or invalid url" }, 400, corsHeaders);
      }
      try {
        const res = await fetch(target, {
          headers: {
            "User-Agent": "Mozilla/5.0 (compatible; Argus/1.0)",
            "Accept": "text/html,application/xhtml+xml",
          },
          redirect: "follow",
        });
        const html = await res.text();
        return json({ ok: true, html }, 200, corsHeaders);
      } catch (err) {
        return json({ ok: false, error: err.message }, 502, corsHeaders);
      }
    }

    // ROUTE: /analyse
    if (url.pathname === "/analyse") {
      const limited = await rateLimit(env, request, "/analyse", 10);
      if (limited) return json({ ok: false, error: "Rate limit exceeded. Try again in a minute." }, 429, corsHeaders);
      let body;
      try { body = await request.json(); } catch {
        return json({ ok: false, error: "Invalid JSON" }, 400, corsHeaders);
      }
      const { input } = body;
      if (!input) {
        return json({ ok: false, error: "Missing input" }, 400, corsHeaders);
      }

      const systemPrompt = `You are a rigorous analytical engine. Stress-test arguments without ideological bias.

Return ONLY valid JSON — no markdown fences, no preamble — in this exact structure:
{
  "core_thesis": "One sentence: what is actually being argued?",
  "steelman": "Strongest possible version of the argument. Assume the most informed defender. Genuinely hard to refute.",
  "steelman_crux": "What must be true for the steelman to hold?",
  "strawman": "Weakest, most attackable version. What a hostile critic dismantles. What is left out or assumed.",
  "strawman_crux": "The most devastating single objection.",
  "synthesis": "What a rigorous, disinterested thinker concludes after seeing both sides.",
  "real_crux": "The single resolvable question separating believers from sceptics. Not it depends.",
  "evidence_that_changes_it": "What specific evidence would flip the synthesis?",
  "actionable": "One concrete implication for someone who accepts the synthesis."
}

Rules: Do NOT validate the input. The steelman must be genuinely strong. Return ONLY the JSON object, nothing else.`;

      try {
        const groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${env.GROQ_API_KEY}`,
          },
          body: JSON.stringify({
            model: "llama-3.3-70b-versatile",
            messages: [
              { role: "system", content: systemPrompt },
              { role: "user", content: input },
            ],
            temperature: 0.4,
            max_tokens: 1200,
            response_format: { type: "json_object" },
          }),
        });
        const groqJson = await groqRes.json();
        if (!groqRes.ok || groqJson?.error) {
          return json({ ok: false, error: groqJson?.error?.message || `Groq HTTP ${groqRes.status}` }, 502, corsHeaders);
        }
        const rawText = groqJson?.choices?.[0]?.message?.content || "";
        let result;
        try {
          const cleaned = rawText.replace(/```json|```/g, "").trim();
          const match = cleaned.match(/\{[\s\S]*\}/);
          result = JSON.parse(match ? match[0] : cleaned);
        } catch {
          return json({ ok: false, error: "Parse failed", raw: rawText.slice(0, 300) }, 502, corsHeaders);
        }
        return json({ ok: true, result }, 200, corsHeaders);
      } catch (err) {
        return json({ ok: false, error: err.message }, 502, corsHeaders);
      }
    }

    return new Response("Not found", { status: 404, headers: corsHeaders });
  },
};

function json(data, status = 200, headers = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

async function rateLimit(env, request, route, limit) {
  if (!env.RATE_LIMIT) return false;
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const minute = Math.floor(Date.now() / 60000);
  const key = `${ip}:${route}:${minute}`;
  const current = parseInt(await env.RATE_LIMIT.get(key) || "0");
  if (current >= limit) return true;
  await env.RATE_LIMIT.put(key, String(current + 1), { expirationTtl: 90 });
  return false;
}
