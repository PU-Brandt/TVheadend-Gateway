# Home-Assistant-Beispiele

Die Dateien in diesem Ordner zeigen die Assist-Anbindung an das externe
TVHeadend Gateway. Sie sind Beispiele und duerfen nicht blind eine bestehende
Home-Assistant-Konfiguration ersetzen.

- `befehlsreferenz.yaml`: unterstuetzte Sprachvarianten
- `tvheadend_automation.yaml`: Automation mit fortlaufendem Programmdialog
- `tvheadend_scripts.yaml`: Gateway-Aufruf und Dialogschleife

Der Dialog gibt einen Sendeplatz pro Schritt aus und versteht unter anderem
`weiter`, `wiederholen`, `beenden` und `nimm die zweite Sendung auf`.

Die Automation ermittelt den ausloesenden Assist-Satelliten dynamisch. Anfragen
aus der Home-Assistant-App werden ueber die normale Konversationsantwort auf dem
Handy beantwortet und nicht an einen fest eingetragenen ESPHome-Satelliten gesendet.
