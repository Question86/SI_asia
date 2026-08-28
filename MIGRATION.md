# MIGRATION — zh-TW finance-weighted fork

上游 / Upstream: `Question86/senna-infoflow` (branch `main`)
分支日期 / Fork date: 2026-08-27

---

## 中文摘要

本分支做兩件事：**（1）文件繁體中文化**，**（2）提高金融市場相關資訊與新聞型態的權重**。

**程式碼未更動。** 只調整了設定檔中既有鍵的數值，並翻譯文件。

### 設計上的核心決定

提高金融權重最直覺的做法，是把 `central_bank` 從 `dominance_guard.dominant_emitters` 拿掉。**本分支刻意不這樣做**，因為那會摧毀上游整套「反擴音器」原則。

改採的路徑：dominance penalty 的觸發條件是

```
single-source, no cross-source resonance, no high-signal term, momentum_delta <= 1
```

「**no high-signal term**」本身就是豁免條件。因此只要擴充 `high_signal_terms`，實質性金融事件即自動脫離懲罰，而例行央行發言仍受限。用既有邏輯達成目的，不動守衛。

---

## Zusammenfassung (DE)

Zwei Dinge: **Dokumentation auf 繁體中文**, und **Finanzmarkt-Muster staerker gewichtet**.

**Kein Code geaendert.** Nur Werte bestehender Schluessel in Configs, plus Uebersetzung.

**Zentrale Entscheidung:** Der naheliegende Weg — `central_bank` aus `dominance_guard.dominant_emitters` entfernen — wurde bewusst *nicht* gegangen. Das haette das Anti-Megafon-Prinzip des Originals zerstoert. Stattdessen wurde `high_signal_terms` erweitert, weil die Penalty-Bedingung ohnehin bei einem High-Signal-Term entfaellt. Substanzielle Finanzereignisse entkommen dem Cap, Routine-Geplauder bleibt gedeckelt.

---

## Geaenderte Dateien / 變更檔案

### `config/resonance_ranking.yaml`

| Feld | Vorher | Nachher |
|---|---|---|
| `early_signal.trigger_terms` | 14 Begriffe, alle physisch/logistisch | **+29** Begriffe: Markt-Mikrostruktur, Kreditstress, Exportkontrolle, Halbleiter-Lieferkette, TW-Physikrisiko |
| `dominance_guard` | — | **unveraendert** (bewusst) |
| `bonus_points_max` | 8 | **unveraendert** |

Neue Begriffe u.a.: `trading halt`, `circuit breaker`, `margin call`, `liquidity squeeze`, `funding stress`, `profit warning`, `credit downgrade`, `fx intervention`, `capital control`, `export control`, `entity list`, `chip ban`, `fab outage`, `wafer shortage`, `earthquake`, `typhoon`, `undersea cable`, `port congestion`.

`earthquake` / `typhoon` / `undersea cable` sind physische Ereignisse, aber fuer einen taiwanesischen Finanzdesk **direkte Markttransmission** (Fab-Ausfall, Konnektivitaet, Logistik). Deshalb stehen sie hier und nicht nur in der Umweltschiene.

### `config/source_governance.yaml`

| Feld | Vorher | Nachher |
|---|---|---|
| `limits.min_early_signal_share` | 0.08 | **0.12** |
| `classes.institutional` | 4 Werte | **+ `central_bank_network`** (Bugfix, s.u.) + 3 reservierte Werte |
| `signals.high_signal_terms` | 13 | **+14** Finanzbegriffe |
| `signals.early_signal_terms` | 16 | **+15** Finanz-/Lieferketten-/TW-Begriffe |
| alle uebrigen `limits` | — | **unveraendert** |

`min_early_signal_share` von 0.08 auf 0.12: bei hoeherer institutioneller Last muss der Boden fuer schwache Signale mitwachsen, sonst degeneriert der Fork genau zu dem Megafon, vor dem das Original warnt.

### `config/macro_sources.yaml`

15 bestehende Quellen **unveraendert uebernommen**. **12 neue Quellen ergaenzt**, alle `enabled: false`:

Taiwan: CBC · FSC · TWSE · TPEx · MOPS · DGBAS · MOEA
Region: BOJ · BOK · HKMA · MAS · PBoC

### `README.md`

Vollstaendig auf 繁體中文. Technische Bezeichner (Pfade, YAML-Keys, `source_class`-Werte, Cron, Feldnamen) bleiben englisch — Uebersetzen wuerde das System brechen.

---

## Zwei Befunde aus dem Upstream-Repo

### 1. BUG: `central_bank_network` ist in keiner Klassenliste

`config/macro_sources.yaml` klassifiziert die drei BIS-Feeds als `source_class: "central_bank_network"`. Dieser Wert kommt in **keiner** der vier Listen unter `classes:` in `source_governance.yaml` vor.

**Folge:** Die BIS-Items fallen in den Unknown-Class-Topf und zaehlen gegen `max_unknown_class_share: 0.20`. Bei drei aktiven BIS-Feeds ist das eine reale Fehlklassifikation.

Im Fork korrigiert. **Vorbestehend, unabhaengig von der Finanzgewichtung.**

### 2. `docs/architecture.md` existiert nicht

Das README verlinkt `docs/architecture.md`. Die Datei liefert **404**. Zusaetzlich ist der Markdown-Link im Original syntaktisch kaputt (fehlende schliessende Klammer):

```
[docs/architecture.md (docs/architecture.md)
```

Im Fork nicht ergaenzt, nur dokumentiert.

---

## 啟用前檢查清單 / Checkliste vor dem Aktivieren

**Die 12 neuen Quellen stehen mit Absicht auf `enabled: false`.** Ich kenne die aktuellen RSS-Endpunkte dieser Institutionen nicht mit Sicherheit. Geratene URLs als `enabled` auszuliefern waere unserioes — das Repo markiert vorhandene tote Quellen selbst mit `disabled:403` / `disabled:429`.

Pro Quelle vor dem Aktivieren:

- [ ] URL aufrufen — existiert der Endpunkt, ist er oeffentlich, liefert er RSS/Atom?
- [ ] Robots/ToS des Hosts pruefen — das Repo verbietet Scraping gegen klare Verbote
- [ ] `verify_url:pending` aus `keywords` entfernen
- [ ] Bei totem Endpunkt: `disabled:404` bzw. `disabled:403` eintragen, Konvention des Repos folgen
- [ ] Erst dann `enabled: true`

### Zwei funktionale Punkte, die sonst still fehlschlagen

**A. Keyword-Sprache.** Alle bestehenden Quellen haben **ausschliesslich englische** `keywords`. Taiwanesische, japanische und koreanische Feeds publizieren in Landessprache — reine ASCII-Keywords matchen dort **nie**. Die neuen Quellen tragen deshalb zweisprachige Keywords. Falls die Pipeline Keyword-Matching case-/unicode-empfindlich macht, ist das vor dem ersten produktiven Lauf zu pruefen.

**B. `high_signal_terms` / `early_signal_terms` Matching.** Ich habe **nicht** geprueft, ob `scripts/resonance_rank_postprocess.py` seine High-Signal-Liste tatsaechlich aus `source_governance.yaml` liest oder eine eigene Kopie haelt. Falls letzteres, greift die Dominance-Exemption nicht, und die Finanzgewichtung wirkt nur ueber `early_signal.trigger_terms`. **Vor dem ersten Lauf im Script nachsehen.**

### Nicht uebernommene Klassenwerte

`classes.institutional` enthaelt zusaetzlich `market_operator`, `financial_regulator`, `statistics_office`. Diese Werte werden von den neuen Quellen **nicht** benutzt — dort stehen nur bestehende Werte (`central_bank`, `policy_institution`, `tier1_official`). Die drei sind reserviert, falls ihr die Klassifikation spaeter feiner ziehen wollt. Inert, solange sie niemand vergibt.

---

## Nicht geaendert

- Alle `scripts/*.py` — unangetastet
- `.github/workflows/monitor.yml` — unangetastet
- `config/sources.yaml`, `config/hot_sources.yaml` — unangetastet
- Budgets, Timeouts, Takt — unangetastet
- `dominance_guard` — bewusst unangetastet

---

## 使用範圍聲明 / Scope statement

本工具輸出的是**「有事情正在發生」的訊號**，不是投資建議。上游 README 已將「從機率或市場資料衍生投注／投資建議」列為不允許項目；本分支保留並強化了該條款，因為提高金融權重會提高被誤用的風險。

使用者若任職於金融機構，其所屬機構的法遵、內線交易與資訊隔離規範，一律優先於本工具的任何輸出。

Der Fork verschiebt Gewichte in der Wahrnehmung. Er trifft keine Aussage darueber, was jemand mit dieser Wahrnehmung tun soll.
