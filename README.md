# Batrium Kapazitätstest Cockpit

Lokale Webapp für HA/Batrium-Kapazitätstests mit resetfester Rechnung (`cumulkwhdischg` Tagesreset robust).

## Start

```bash
cd /home/tom/.openclaw/workspace/batrium-capacity-app
python3 serve.py
```

Dann im Browser öffnen:

- `http://127.0.0.1:8099`

## Funktionen

- Live-KPIs: SoC, MinCellVolt, CumDischg
- T0/T1 manuell setzen (Start/Ende)
- Resetfeste `kWh_used` Berechnung über HA-Recorder-Historie
- Kapazität in kWh und Ah
- Einheiten-/Entity-Check

## Hinweise

- Token wird nur lokal im Browser `localStorage` gehalten.
- Nach Abschluss Token in Home Assistant wieder löschen/revoken.
- Für valide Kapazität: ausreichender SoC-Drop (Standard >= 5%-Punkte).
