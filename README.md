# TVHeadend Gateway Home Assistant Add-on Repository

Dieses Repository enthaelt das Home-Assistant-Add-on fuer das externe TV-Headend Gateway.

Das Add-on ersetzt das externe Gateway nicht. Es dient als Konfigurations-, Diagnose- und Steueroberflaeche in Home Assistant und kommuniziert mit dem Gateway ueber dessen `/api/v1`-Schnittstelle.

## Add-on

- Ordner: `tv-headend-gateway`
- Ingress-Oberflaeche: ja
- Externer Dienst: `TV-Headend Gateway`
- Standard-Port des externen Dienstes: `8089`

## Installation

1. Dieses Repository in Home Assistant als Add-on-Repository hinzufuegen.
2. Add-on `TV-Headend Gateway` installieren.
3. In der Add-on-Konfiguration `external_host` und `external_port` setzen.
4. Add-on starten.
5. Add-on ueber die Seitenleiste oeffnen.

Secrets und echte lokale Konfigurationen gehoeren nicht in dieses Repository.

Beispiele fuer die Assist-Anbindung liegen unter `home-assistant-examples`.
