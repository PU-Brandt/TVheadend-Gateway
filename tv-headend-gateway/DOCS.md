# Dokumentation

## Voraussetzung

Das externe TV-Headend Gateway muss erreichbar sein.

Pruefung vom Home-Assistant-Netz aus:

```text
http://GATEWAY-IP:8088/api/v1/health
```

Eine erfolgreiche Antwort sieht ungefaehr so aus:

```json
{
  "ok": true,
  "tvheadend": "http://192.168.200.105:9981",
  "channels": 41
}
```

## Add-on-Konfiguration

```yaml
external_host: "192.168.x.x"
external_port: 8088
api_base_path: "/api/v1"
api_token: ""
request_timeout_seconds: 30
```

Wenn `api_token` leer ist, werden keine Token-Header gesendet.

## Sicherheit

Das Add-on zeigt Tokens nicht an. Wenn im externen Gateway ein Token gesetzt ist, muss dasselbe Token in der Add-on-Konfiguration hinterlegt werden.

Das externe Gateway sollte nicht ins Internet veroeffentlicht werden.

