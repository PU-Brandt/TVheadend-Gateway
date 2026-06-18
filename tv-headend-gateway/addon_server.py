#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import urllib.error
import urllib.request


INGRESS_PORT = 8099
OPTIONS_PATH = Path("/data/options.json")
ADDON_VERSION = "0.1.3"


def load_options() -> dict[str, Any]:
    if OPTIONS_PATH.exists():
        return json.loads(OPTIONS_PATH.read_text(encoding="utf-8"))
    return {
        "external_host": "",
        "external_port": 8088,
        "api_base_path": "/api/v1",
        "api_token": "",
        "request_timeout_seconds": 30,
    }


def build_base_url(options: dict[str, Any]) -> str:
    host = str(options.get("external_host") or "").strip()
    port = int(options.get("external_port") or 8088)
    base_path = str(options.get("api_base_path") or "/api/v1").strip()
    if not host:
        return ""
    if not host.startswith(("http://", "https://")):
        host = f"http://{host}"
    parsed = urlparse(host)
    netloc = parsed.netloc
    if ":" not in netloc:
        netloc = f"{netloc}:{port}"
    root = f"{parsed.scheme}://{netloc}"
    return urljoin(root.rstrip("/") + "/", base_path.strip("/") + "/")


def tool_request(method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    options = load_options()
    base_url = build_base_url(options)
    if not base_url:
        return 400, {"status": "error", "message": "Die Gateway-Adresse ist in den Add-on-Optionen noch nicht gesetzt."}

    headers: dict[str, str] = {"Accept": "application/json"}
    token = str(options.get("api_token") or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-Api-Token"] = token

    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    timeout = int(options.get("request_timeout_seconds") or 30)
    request = urllib.request.Request(
        urljoin(base_url, path.lstrip("/")),
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8")
            body = json.loads(text) if text else {}
            return response.status, normalize_response(body)
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(text)
        except ValueError:
            body = {"message": text}
        return exc.code, normalize_response(body)
    except Exception as exc:
        return 502, {"status": "error", "message": str(exc), "base_url": base_url}


def raw_gateway_request(path: str) -> tuple[int, dict[str, Any]]:
    options = load_options()
    base_url = build_base_url(options)
    if not base_url:
        return 400, {"status": "error", "message": "Die Gateway-Adresse ist in den Add-on-Optionen noch nicht gesetzt."}
    root = base_url.removesuffix("/api/v1/")
    url = urljoin(root.rstrip("/") + "/", path.lstrip("/"))
    timeout = int(options.get("request_timeout_seconds") or 30)
    request = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8")
            return response.status, json.loads(text) if text else {}
    except Exception as exc:
        return 502, {"status": "error", "message": str(exc)}


def normalize_response(body: Any) -> dict[str, Any]:
    if not isinstance(body, dict):
        return {"status": "ok", "value": body}
    body = dict(body)
    if "status" not in body:
        body["status"] = "ok" if body.get("ok", True) else "error"
    if "message" not in body and "detail" in body:
        body["message"] = str(body["detail"])
    return body


def render_page() -> bytes:
    options = load_options()
    gateway_url = build_base_url(options) or "nicht konfiguriert"
    html = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TV-Headend Gateway</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Segoe UI, system-ui, sans-serif; }}
    body {{ margin: 0; background: #f5f7f9; color: #1f2933; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 22px; }}
    h1 {{ font-size: 26px; margin: 0 0 16px; display: flex; gap: 10px; align-items: center; }}
    h2 {{ font-size: 17px; margin: 0 0 12px; }}
    section {{ background: #fff; border: 1px solid #d8e0e8; border-radius: 8px; padding: 16px; margin-bottom: 14px; }}
    .badge {{ font-size: 12px; font-weight: 600; color: #52606d; background: #e8eef5; border-radius: 999px; padding: 4px 8px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
    .tile {{ border: 1px solid #d8e0e8; border-radius: 6px; padding: 12px; background: #f9fbfd; }}
    .label {{ color: #596673; font-size: 12px; margin-bottom: 4px; }}
    .value {{ font-size: 15px; font-weight: 600; word-break: break-word; }}
    .banner {{ padding: 12px; border-radius: 6px; border: 1px solid #fed7aa; background: #fff7ed; margin: 12px 0; }}
    .banner.ok {{ border-color: #bbf7d0; background: #ecfdf5; }}
    .banner.error {{ border-color: #fecaca; background: #fef2f2; }}
    label {{ display: block; font-size: 12px; color: #596673; margin-bottom: 5px; }}
    input, select, textarea {{ width: 100%; box-sizing: border-box; border: 1px solid #b8c4d0; border-radius: 6px; padding: 8px 9px; font: inherit; background: #fff; color: #1f2933; }}
    textarea {{ min-height: 260px; font: 13px Consolas, monospace; resize: vertical; }}
    .form-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
    .field {{ min-width: 0; }}
    .subhead {{ font-size: 15px; font-weight: 700; margin: 18px 0 10px; }}
    button {{ border: 0; border-radius: 6px; background: #2563eb; color: white; padding: 9px 13px; font: inherit; cursor: pointer; }}
    button.secondary {{ background: #52606d; }}
    button.danger {{ background: #b42318; }}
    .actions {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }}
    .muted {{ color: #596673; font-size: 13px; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #f8fafc; border: 1px solid #d8e0e8; border-radius: 6px; padding: 12px; max-height: 300px; overflow: auto; }}
    #message {{ min-height: 22px; }}
    @media (prefers-color-scheme: dark) {{
      body {{ background: #11161c; color: #e6edf3; }}
      section, textarea, input, select {{ background: #171d24; color: #e6edf3; border-color: #344250; }}
      .tile, pre {{ background: #111820; border-color: #344250; }}
      .label, label, .muted {{ color: #aab6c2; }}
      .badge {{ background: #273444; color: #d6e0ea; }}
      .banner {{ background: #332414; border-color: #7a4b18; }}
      .banner.ok {{ background: #133226; border-color: #246b4a; }}
      .banner.error {{ background: #371818; border-color: #7a3030; }}
    }}
  </style>
</head>
<body>
<main>
  <h1>TV-Headend Gateway <span class="badge" id="versionBadge">Add-on {ADDON_VERSION}</span></h1>

  <section>
    <h2>Gateway-Verbindung</h2>
    <p class="muted">Diese Verbindung wird in den Add-on-Optionen gesetzt. Hier wird sie nur angezeigt und getestet.</p>
    <div class="grid">
      <div class="tile"><div class="label">Gateway-API</div><div class="value">{gateway_url}</div></div>
      <div class="tile"><div class="label">Timeout</div><div class="value">{options.get("request_timeout_seconds", 30)} Sekunden</div></div>
      <div class="tile"><div class="label">API-Token</div><div class="value">{"gesetzt" if options.get("api_token") else "nicht gesetzt"}</div></div>
    </div>
  </section>

  <section>
    <div class="actions">
      <h2 style="margin-right:auto">Status</h2>
      <button onclick="loadAll()">Aktualisieren</button>
      <button class="secondary" onclick="runAction('test_connection')">Gateway testen</button>
      <button class="secondary" onclick="runAction('refresh_epg')">EPG neu abfragen</button>
      <button class="secondary" onclick="runAction('reload')">Gateway neu laden</button>
    </div>
    <p id="message"></p>
    <div id="statusBanner" class="banner">Status noch nicht geladen.</div>
    <div class="grid">
      <div class="tile"><div class="label">TVHeadend</div><div class="value" id="tileTvheadend">-</div></div>
      <div class="tile"><div class="label">Sender</div><div class="value" id="tileChannels">-</div></div>
      <div class="tile"><div class="label">Gateway-Schreibschutz</div><div class="value" id="tileToken">-</div></div>
      <div class="tile"><div class="label">Letzter Fehler</div><div class="value" id="tileError">-</div></div>
    </div>
  </section>

  <section>
    <div class="actions">
      <h2 style="margin-right:auto">TVHeadend-Konfiguration</h2>
      <button class="secondary" onclick="loadConfig()">Einlesen</button>
      <button onclick="saveConfig()">Speichern</button>
      <button class="secondary" onclick="toggleAdvanced()">JSON anzeigen</button>
    </div>
    <p class="muted">Diese Werte beschreiben ausschliesslich die Verbindung vom Gateway zum TVHeadend-Server.</p>
    <div class="form-grid">
      <div class="field"><label for="tvhScheme">Protokoll</label><select id="tvhScheme"><option>http</option><option>https</option></select></div>
      <div class="field"><label for="tvhHost">TVHeadend IP oder Host</label><input id="tvhHost" placeholder="192.168.200.105"></div>
      <div class="field"><label for="tvhPort">TVHeadend Port</label><input id="tvhPort" type="number" min="1" max="65535" placeholder="9981"></div>
      <div class="field"><label for="tvhUsername">Benutzername optional</label><input id="tvhUsername" autocomplete="username"></div>
      <div class="field"><label for="tvhPassword">Passwort optional</label><input id="tvhPassword" type="password" autocomplete="new-password" placeholder="leer lassen, wenn unveraendert"></div>
      <div class="field"><label for="cacheSeconds">Cache Sekunden</label><input id="cacheSeconds" type="number" min="0" max="3600"></div>
    </div>

    <div class="subhead">EPG-Test</div>
    <div class="form-grid">
      <div class="field"><label for="testChannel">Sender fuer Vorlesetext</label><input id="testChannel" placeholder="Das Erste"></div>
      <div class="field"><label for="searchQuery">EPG-Suche</label><input id="searchQuery" placeholder="Tatort"></div>
    </div>
    <div class="actions" style="margin-top:12px">
      <button class="secondary" onclick="testSpeak()">Vorlesetext testen</button>
      <button class="secondary" onclick="searchEpg()">EPG suchen</button>
    </div>
    <pre id="epgResult">Noch keine EPG-Abfrage.</pre>

    <div id="advancedConfig" style="display:none; margin-top:18px">
      <div class="subhead">Gespeicherte Gateway-Konfiguration</div>
      <textarea id="configText" spellcheck="false"></textarea>
    </div>
  </section>

  <section>
    <div class="actions">
      <h2 style="margin-right:auto">Logs</h2>
      <button class="secondary" onclick="loadLogs()">Aktualisieren</button>
      <button class="secondary" onclick="clearLogs()">Leeren</button>
    </div>
    <pre id="logs">Noch keine Logs.</pre>
  </section>

  <section>
    <h2>Diagnose</h2>
    <pre id="diagnostics">Noch keine Daten.</pre>
  </section>
</main>
<script>
async function requestJson(url, options) {{
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok || data.status === 'error') {{
    throw new Error(data.message || data.detail || `HTTP ${{response.status}}`);
  }}
  return data;
}}

let currentConfig = {{}};
let advancedVisible = false;

function value(id) {{ return document.getElementById(id).value.trim(); }}
function setValue(id, nextValue) {{ document.getElementById(id).value = nextValue ?? ''; }}
function numberValue(id, fallback) {{
  const raw = value(id);
  if (raw === '') return fallback;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : fallback;
}}

function parseBaseUrl(url) {{
  try {{
    const parsed = new URL(url || 'http://192.168.200.105:9981');
    return {{scheme: parsed.protocol.replace(':', ''), host: parsed.hostname, port: parsed.port || (parsed.protocol === 'https:' ? '443' : '80')}};
  }} catch {{
    return {{scheme: 'http', host: '192.168.200.105', port: '9981'}};
  }}
}}

function buildBaseUrl() {{
  const scheme = value('tvhScheme') || 'http';
  const host = value('tvhHost') || '192.168.200.105';
  const port = numberValue('tvhPort', 9981);
  return `${{scheme}}://${{host}}:${{port}}`;
}}

async function loadAll() {{
  const [manifest, health, status] = await Promise.all([
    requestJson('./api/manifest').catch(error => ({{status: 'error', message: String(error)}})),
    requestJson('./api/health').catch(error => ({{status: 'error', message: String(error)}})),
    requestJson('./api/status').catch(error => ({{status: 'error', message: String(error)}})),
  ]);
  document.getElementById('versionBadge').textContent = `Add-on {ADDON_VERSION} | Dienst ${{manifest.version || '-'}}`;
  renderStatus(status, health);
  document.getElementById('diagnostics').textContent = JSON.stringify({{manifest, health, status}}, null, 2);
}}

function renderStatus(status, health) {{
  const ok = status.ok === true || status.status === 'ok';
  const banner = document.getElementById('statusBanner');
  banner.className = ok ? 'banner ok' : 'banner error';
  banner.textContent = ok ? 'TV-Headend Gateway ist erreichbar.' : (status.message || status.last_error || 'Gateway meldet einen Fehler.');
  document.getElementById('tileTvheadend').textContent = status.tvheadend || health.tvheadend || '-';
  document.getElementById('tileChannels').textContent = String(status.channels ?? health.channels ?? '-');
  document.getElementById('tileToken').textContent = status.token_required_for_writes ? 'Token aktiv' : 'kein Token';
  document.getElementById('tileError').textContent = status.last_error || '-';
}}

async function loadConfig() {{
  const data = await requestJson('./api/config');
  currentConfig = data.config || data;
  renderConfigForm();
}}

async function saveConfig() {{
  const message = document.getElementById('message');
  try {{
    const config = advancedVisible
      ? JSON.parse(document.getElementById('configText').value || '{{}}')
      : collectTvheadendConfig();
    const data = await requestJson('./api/config', {{
      method: 'PUT',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(config)
    }});
    currentConfig = config;
    renderConfigForm();
    message.textContent = data.message || 'Gespeichert.';
    await loadAll();
  }} catch (error) {{
    message.textContent = error.message;
  }}
}}

function renderConfigForm() {{
  const cfg = currentConfig || {{}};
  const tvh = cfg.tvheadend || {{}};
  const parsed = parseBaseUrl(tvh.base_url);
  setValue('tvhScheme', parsed.scheme);
  setValue('tvhHost', parsed.host);
  setValue('tvhPort', parsed.port || 9981);
  setValue('tvhUsername', tvh.username || '');
  setValue('tvhPassword', tvh.password === '********' ? '' : (tvh.password || ''));
  setValue('cacheSeconds', tvh.cache_seconds ?? 20);
  document.getElementById('configText').value = JSON.stringify(stripToTvheadendConfig(cfg), null, 2);
}}

function collectTvheadendConfig() {{
  const oldTvh = (currentConfig || {{}}).tvheadend || {{}};
  return {{
    tvheadend: {{
      base_url: buildBaseUrl(),
      username: value('tvhUsername'),
      password: value('tvhPassword') || (oldTvh.password === '********' ? '********' : ''),
      cache_seconds: numberValue('cacheSeconds', 20)
    }},
    home_assistant: {{
      url: window.location.origin,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'Europe/Berlin',
      location_name: ''
    }}
  }};
}}

function stripToTvheadendConfig(cfg) {{
  return {{
    tvheadend: (cfg || {{}}).tvheadend || {{}},
    home_assistant: (cfg || {{}}).home_assistant || {{
      url: window.location.origin,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'Europe/Berlin',
      location_name: ''
    }}
  }};
}}

function toggleAdvanced() {{
  advancedVisible = !advancedVisible;
  const panel = document.getElementById('advancedConfig');
  panel.style.display = advancedVisible ? 'block' : 'none';
  if (advancedVisible) {{
    document.getElementById('configText').value = JSON.stringify(collectTvheadendConfig(), null, 2);
  }}
}}

async function runAction(action) {{
  const message = document.getElementById('message');
  try {{
    const data = await requestJson(`./api/actions/${{action}}`, {{method: 'POST'}});
    message.textContent = data.message || JSON.stringify(data);
    await loadAll();
  }} catch (error) {{
    message.textContent = error.message;
  }}
}}

async function testSpeak() {{
  const channel = encodeURIComponent(value('testChannel') || 'Das Erste');
  const data = await fetch(`./proxy/speak/now?channel=${{channel}}`).then(response => response.json());
  document.getElementById('epgResult').textContent = JSON.stringify(data, null, 2);
}}

async function searchEpg() {{
  const q = encodeURIComponent(value('searchQuery') || 'Tatort');
  const data = await fetch(`./proxy/epg/search?q=${{q}}&limit=5`).then(response => response.json());
  document.getElementById('epgResult').textContent = JSON.stringify(data, null, 2);
}}

async function loadLogs() {{
  const data = await requestJson('./api/logs/recent');
  const entries = data.entries || [];
  document.getElementById('logs').textContent = entries.map(entry => `${{entry.time_utc || ''}} [${{entry.level || ''}}] ${{entry.message || JSON.stringify(entry)}}`).join('\\n') || 'Keine Logs.';
}}

async function clearLogs() {{
  await requestJson('./api/logs/clear', {{method: 'POST'}});
  await loadLogs();
}}

loadAll();
loadConfig().catch(() => {{}});
loadLogs().catch(() => {{}});
setInterval(loadAll, 10000);
setInterval(loadLogs, 4000);
</script>
</body>
</html>"""
    return html.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self.write_html(render_page())
            return
        if self.path.startswith("/api/"):
            self.proxy_api("GET", self.path.removeprefix("/api/"))
            return
        if self.path.startswith("/proxy/"):
            self.proxy_raw(self.path.removeprefix("/proxy/"))
            return
        self.write_json(404, {"status": "error", "message": "not found"})

    def do_POST(self) -> None:
        if self.path.startswith("/api/"):
            self.proxy_api("POST", self.path.removeprefix("/api/"))
            return
        self.write_json(404, {"status": "error", "message": "not found"})

    def do_PUT(self) -> None:
        if self.path.startswith("/api/"):
            self.proxy_api("PUT", self.path.removeprefix("/api/"))
            return
        self.write_json(404, {"status": "error", "message": "not found"})

    def proxy_api(self, method: str, path: str) -> None:
        payload = None
        if method in {"POST", "PUT"}:
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw or "{}")
        self.write_json(*tool_request(method, path, payload))

    def proxy_raw(self, path: str) -> None:
        self.write_json(*raw_gateway_request(path))

    def log_message(self, format: str, *args: Any) -> None:
        return

    def write_html(self, body: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def write_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    port = int(os.environ.get("PORT", INGRESS_PORT))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"TV-Headend Gateway Control listening on port {port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
