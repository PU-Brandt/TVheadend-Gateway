# Changelog

## 0.1.5

- Buttons zum Neustarten und Beenden des externen Gateways ergaenzt.
- Gateway-Aktionen fuer Neustart und Beenden koennen ueber die Konfigurationsseite ausgeloest werden.

## 0.1.4

- Add-on prueft jetzt hart, ob der verbundene Dienst wirklich `tv-headend-gateway` ist.
- Bei falschem Dienst werden Status, Konfiguration und Aktionen blockiert, statt fremde Gateway-Daten anzuzeigen.
- Speichern und erneutes Einlesen der TVHeadend-Konfiguration im externen Gateway korrigiert.
- Standardport des TVHeadend-Gateways auf `8089` geaendert, um Konflikte mit anderen Gateway-Diensten auf `8088` zu vermeiden.

## 0.1.3

- Konfigurationsseite auf TVHeadend-relevante Einstellungen reduziert.
- Gateway-Host und Gateway-Port aus der fachlichen Konfigurationsmaske entfernt und nur noch als Add-on-Verbindungsstatus angezeigt.
- Nicht benoetigte Fremdstrukturen werden beim Speichern nicht mehr geschrieben.
- Home-Assistant-URL und Zeitzone werden im Browser automatisch aus dem laufenden Home-Assistant-Kontext abgeleitet.

## 0.1.2

- Ingress-Konfigurationsseite an den bestehenden Add-on-Aufbau angeglichen.
- Formularfelder fuer TVHeadend-Adresse, Port, Benutzername, Passwort und Cache ergaenzt.
- Status-Kacheln, EPG-Testaktionen, Log-Anzeige und JSON-Expertenmodus erweitert.

## 0.1.1

- Dockerfile nutzt jetzt `BUILD_ARCH` statt `BUILD_FROM`, damit der Supervisor-Build nicht mit leerem Basisimage scheitert.
- Veraltete Architekturen aus der Add-on-Konfiguration entfernt.

## 0.1.0

- Erstversion des Home-Assistant-Add-ons.
- Ingress-Oberflaeche fuer Status, Diagnose, Logs und Konfiguration.
- Kommunikation mit externem TV-Headend Gateway ueber `/api/v1`.
