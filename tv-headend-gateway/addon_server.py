#!/usr/bin/env python3
from __future__ import annotations

from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import urllib.error
import urllib.parse
import urllib.request


OPTIONS_FILE = "/data/options.json"
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 8099


def load_options() -> dict:
    try:
        with open(OPTIONS_FILE, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return {
            "external_host": "",
            "external_port": 8088,
            "api_base_path": "/api/v1",
            "api_token": "",
            "request_timeout_seconds": 30,
        }


def gateway_base_url(options: dict) -> str | None:
    host = str(options.get("external_host", "")).strip()
    if not host:
        return None
    port = int(options.get("external_port", 8088))
    base_path = str(options.get("api_base_path", "/api/v1")).strip() or "/api/v1"
    if not base_path.startswith("/"):
        base_path = "/" + base_path
    return f"http://{host}:{port}{base_path.rstrip('/')}"


def request_gateway(method: str, path: str, body: dict | None = None) -> tuple[int, dict | str]:
    options = load_options()
    base_url = gateway_base_url(options)
    if not base_url:
        return 400, {"detail": "external_host ist noch nicht konfiguriert."}

    timeout = int(options.get("request_timeout_seconds", 30))
    url = base_url + path
    data = None
    headers = {"Accept": "application/json"}
    token = str(options.get("api_token", "")).strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-Api-Token"] = token
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
            try:
                return response.status, json.loads(payload) if payload else {}
            except json.JSONDecodeError:
                return response.status, payload
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(payload)
        except json.JSONDecodeError:
            return exc.code, {"detail": payload}
    except Exception as exc:
        return 502, {"detail": str(exc)}


def compact_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def render_page() -> bytes:
    options = load_options()
    base_url = gateway_base_url(options)
    manifest_status, manifest = request_gateway("GET", "/manifest")
    health_status, health = request_gateway("GET", "/health")
    status_status, status = request_gateway("GET", "/status")
    config_status, config = request_gateway("GET", "/config")
    logs_status, logs = request_gateway("GET", "/logs/recent?limit=80")

    configured = bool(base_url)
    html = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TV-Headend Gateway</title>
  <style>
    :root {{
      color-scheme: light dark;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    body {{ margin: 0; background: #f6f7f9; color: #111827; }}
    header {{ padding: 18px 22px; background: #1f2937; color: white; }}
    main {{ padding: 18px 22px; max-width: 1180px; margin: 0 auto; }}
    section {{ margin: 0 0 18px; padding: 16px; background: white; border: 1px solid #d8dde6; border-radius: 8px; }}
    h1 {{ margin: 0; font-size: 22px; }}
    h2 {{ margin: 0 0 12px; font-size: 17px; }}
    code, pre, textarea {{ font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }}
    pre {{ overflow: auto; background: #111827; color: #e5e7eb; padding: 12px; border-radius: 6px; max-height: 320px; }}
    textarea {{ width: 100%; min-height: 260px; box-sizing: border-box; padding: 10px; border-radius: 6px; border: 1px solid #cbd5e1; }}
    button {{ padding: 8px 12px; margin: 0 8px 8px 0; border: 0; border-radius: 6px; background: #2563eb; color: white; cursor: pointer; }}
    button.secondary {{ background: #475569; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }}
    .ok {{ color: #047857; font-weight: 700; }}
    .bad {{ color: #b91c1c; font-weight: 700; }}
    .muted {{ color: #64748b; }}
    @media (prefers-color-scheme: dark) {{
      body {{ background: #0f172a; color: #e5e7eb; }}
      section {{ background: #111827; border-color: #334155; }}
      pre {{ background: #020617; }}
      textarea {{ background: #020617; color: #e5e7eb; border-color: #475569; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>TV-Headend Gateway</h1>
    <div class="muted">Home-Assistant-Add-on fuer Konfiguration, Diagnose und Steuerung</div>
  </header>
  <main>
    <section>
      <h2>Verbindung</h2>
      <div>Externer Dienst: <code>{escape(base_url or "nicht konfiguriert")}</code></div>
      <div>Status: <span class="{ "ok" if health_status == 200 else "bad" }">{health_status}</span></div>
      {"" if configured else "<p class='bad'>Bitte external_host in der Add-on-Konfiguration setzen.</p>"}
      <form method="post" action="/action/test_connection"><button>Verbindung testen</button></form>
      <form method="post" action="/action/refresh_epg"><button class="secondary">EPG neu abfragen</button></form>
      <form method="post" action="/action/reload"><button class="secondary">Konfiguration neu laden</button></form>
      <form method="post" action="/logs/clear"><button class="secondary">Logs leeren</button></form>
    </section>

    <div class="grid">
      <section>
        <h2>Health</h2>
        <pre>{escape(compact_json(health))}</pre>
      </section>
      <section>
        <h2>Status</h2>
        <pre>{escape(compact_json(status))}</pre>
      </section>
    </div>

    <section>
      <h2>Fachliche Konfiguration</h2>
      <p class="muted">Diese Konfiguration wird im externen Gateway gespeichert. Secrets werden vom Gateway maskiert.</p>
      <form method="post" action="/config">
        <textarea name="config_json">{escape(compact_json(config if config_status == 200 else {}))}</textarea>
        <br>
        <button>Konfiguration speichern</button>
      </form>
    </section>

    <section>
      <h2>Manifest</h2>
      <pre>{escape(compact_json(manifest))}</pre>
    </section>

    <section>
      <h2>Logs</h2>
      <pre id="logs">{escape(compact_json(logs))}</pre>
    </section>
  </main>
  <script>
    const logs = document.getElementById("logs");
    if (logs) logs.scrollTop = logs.scrollHeight;
  </script>
</body>
</html>"""
    return html.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(render_page())
            return
        if self.path.startswith("/proxy/"):
            path = "/" + self.path.split("/proxy/", 1)[1]
            status, payload = request_gateway("GET", path)
            self.write_json(status, payload)
            return
        self.write_json(404, {"detail": "Not found"})

    def do_POST(self) -> None:
        if self.path.startswith("/action/"):
            action_id = self.path.rsplit("/", 1)[-1]
            status, payload = request_gateway("POST", f"/actions/{urllib.parse.quote(action_id)}")
            self.redirect_with_message(status, payload)
            return
        if self.path == "/logs/clear":
            status, payload = request_gateway("POST", "/logs/clear")
            self.redirect_with_message(status, payload)
            return
        if self.path == "/config":
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            values = urllib.parse.parse_qs(raw)
            config_json = values.get("config_json", ["{}"])[0]
            try:
                payload = json.loads(config_json)
            except json.JSONDecodeError as exc:
                self.write_html(400, f"Ungueltiges JSON: {escape(str(exc))}")
                return
            status, response = request_gateway("PUT", "/config", payload)
            self.redirect_with_message(status, response)
            return
        self.write_json(404, {"detail": "Not found"})

    def redirect_with_message(self, status: int, payload) -> None:
        if 200 <= status < 300:
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
        else:
            self.write_html(status, f"<pre>{escape(compact_json(payload))}</pre><p><a href='/'>Zurueck</a></p>")

    def write_json(self, status: int, payload) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def write_html(self, status: int, html: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


if __name__ == "__main__":
    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), Handler)
    print(f"Listening on {LISTEN_HOST}:{LISTEN_PORT}", flush=True)
    server.serve_forever()

