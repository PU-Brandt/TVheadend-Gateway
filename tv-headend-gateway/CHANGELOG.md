# Changelog

## 0.1.1

- Dockerfile nutzt jetzt `BUILD_ARCH` statt `BUILD_FROM`, damit der Supervisor-Build nicht mit leerem Basisimage scheitert.
- Veraltete Architekturen aus der Add-on-Konfiguration entfernt.

## 0.1.0

- Erstversion des Home-Assistant-Add-ons.
- Ingress-Oberflaeche fuer Status, Diagnose, Logs und Konfiguration.
- Kommunikation mit externem TV-Headend Gateway ueber `/api/v1`.
