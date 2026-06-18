# TV-Headend Gateway Add-on

Dieses Add-on stellt eine Home-Assistant-Oberflaeche fuer ein extern laufendes TV-Headend Gateway bereit.

Aktuelle Add-on-Version: `0.1.2`

Das Gateway selbst muss separat laufen, zum Beispiel als Windows-Dienst per NSSM.

## Konfiguration

Pflicht:

- `external_host`: IP oder Hostname des Rechners, auf dem das Gateway laeuft
- `external_port`: Port des Gateways, Standard `8088`

Optional:

- `api_base_path`: Standard `/api/v1`
- `api_token`: Token, falls im Gateway gesetzt
- `request_timeout_seconds`: Timeout fuer Gateway-Anfragen

## Funktionen

- Verbindung testen
- Status und Health anzeigen
- Manifest anzeigen
- Gateway-Konfiguration lesen und speichern
- TVHeadend-Adresse, Port, Benutzername und Passwort konfigurieren
- EPG-Vorlesetext und EPG-Suche testen
- Gateway-Aktionen ausloesen
- sichtbare Gateway-Logs anzeigen und loeschen
