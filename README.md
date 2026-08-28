# senna-infoflow（繁體中文・金融加權分支）

senna-infoflow 是一套供 User Yps / AXI0M 使用的公開來源訊號過濾器。

> **本分支說明**
> 這是上游 `Question86/senna-infoflow` 的繁體中文分支，並針對**金融市場相關的資訊與新聞型態**提高權重。
> 變更內容與理由完整記錄於 [`MIGRATION.md`](MIGRATION.md)。
> 程式邏輯未更動，僅調整設定檔數值與文件語言。

本系統**不是**完整的新聞服務，也不宣稱能全面監看世界局勢。它只讀取已設定、公開、獲授權的來源。不使用私人帳號、不登入、不繞過付費牆或資料庫、不對明確禁止抓取的對象進行抓取。

---

## 基本原則

**並非每一個資訊來源都同等重要。**

像 FED、ECB、BIS、CBC（中央銀行）、CISA 或 NOAA 這類官方大型發布者具有可信度，但**不會因為體量大就自動取得排序上的支配地位**。相對地，一個規模小但出現得早的訊號——地方森林火災、停電、罷工、港口或管線中斷、程式庫資安通報、供應鏈異常——只要具體、新穎或具動態性，就會保持可見。

```
可信度：是。
擴音器式支配：否。
微小的初期動態必須保持可見。
供應商／自有來源不等同於世界局勢。
```

---

## 一句話架構

```
已設定的公開來源
↓ Lane 合併
↓ 帶預算與逾時的擷取
↓ 去重與當日資料池
↓ 去偏（debias）
↓ 網路／共振排序
↓ 健康度／清單／簡報
↓ 交付給 Senna
```

> 註：上游 README 連結的 `docs/architecture.md` **目前不存在**（回傳 404），且該連結的 Markdown 語法本身也有缺漏括號的錯誤。本分支未補上該文件。

---

## 來源與通道（Lanes）

來源在工作流程中由多個設定檔組合而成：

```
config/sources.yaml        # 基礎來源
config/hot_sources.yaml    # 5 分鐘快速通道
config/macro_sources.yaml  # 經濟／政治／總體，15 分鐘通道或手動觸發
```

在 GitHub Action 執行期間，hot 與 macro 疊加層會暫時合併進 `config/sources.yaml`。每次執行後，系統另外寫出：

```
briefings/source_manifest.json
briefings/source_manifest.md
```

其中記錄本次執行實際啟用的來源，包含通道、類型、類別與主機。

### 快速通道（Hot-Lane）

每 5 分鐘執行一次。典型來源：

- GitHub／開發訊號
- HN 等公開快速技術訊號
- GDACS／USGS／GEOFON／NOAA
- 手動公開提示
- 選定的公開風險／機率代理來源（若可取得）

此通道速度快，但容易受特定來源偏誤影響。因此以去偏、共振排序與來源治理加以限制。

### 總體／政策通道（Macro-Lane）

每 15 分鐘執行一次，或手動觸發。典型來源：

- Federal Reserve
- European Central Bank
- Bank for International Settlements
- OECD
- GDELT 總體／政治感測器
- **本分支新增：** 中央銀行（CBC）、金管會（FSC）、證交所（TWSE）、櫃買中心（TPEx）、公開資訊觀測站（MOPS）、主計總處（DGBAS）、經濟部（MOEA），以及 BOJ／BOK／HKMA／MAS／PBoC

此通道補足經濟、政治、利率、央行、制裁、市場、選舉、動盪與全球政策訊號。它可以重要，但不得單獨主導整體局勢圖像。

> **重要：新增來源一律以 `enabled: false` 交付**，並在 `keywords` 中標記 `verify_url:pending`。啟用前必須逐一確認 RSS 端點確實存在且可公開存取。

---

## 支援的來源類型

| 類型 | 用途 |
|---|---|
| `rss` | 讀取 RSS/Atom 訂閱 |
| `github_search` | 使用 GitHub Search API，可搭配 `GITHUB_TOKEN` |
| `reddit_json` | 公開 Reddit JSON 端點；目前常出現 403／不穩定 |
| `hackernews` | 透過 Algolia 的公開 Hacker News 搜尋 |
| `webpage_check` | 有禮貌且有限度地檢查單一網頁 |
| `manual_note` | User Yps 從 Inbox 檔案釋出的提示 |

---

## 預排序與排序

相關性由多個層次共同構成：

```
keyword score
+ recency
+ watchgraph modules
+ source credibility
+ source breadth
+ momentum
+ baseline deviation
+ early-signal bonus
- duplicate/noise pressure
- dominance penalty
- source-bias caps
```

重要檔案：

```
scripts/debias_findings_postprocess.py
scripts/network_hub_postprocess.py
scripts/resonance_rank_postprocess.py
scripts/source_quality_guard.py
config/resonance_ranking.yaml
config/source_governance.yaml
```

---

## 偏誤規則

供應商／自有訂閱、單一 GitHub 程式庫、機率／預測代理來源與社群／平台訊號**維持可見**，但在缺乏獨立佐證或明確高訊號詞彙時會被限制。

高訊號詞彙範例：

```
actively exploited
exploited in the wild
CISA KEV
zero-day
emergency patch
evacuation order
port closure
pipeline outage
central bank emergency
```

本分支新增的金融高訊號詞彙：

```
emergency rate           unscheduled meeting
liquidity facility       bank resolution
sovereign default        credit rating downgrade
circuit breaker triggered / limit down
export control           entity list
chip export restriction  fab shutdown
```

規則刻意嚴格：

> 一個來源可以提早示警。
> 但在沒有共振的情況下，它不得單獨解釋世界。

### 本分支如何在不破壞此規則的前提下提高金融權重

`config/resonance_ranking.yaml` 的 dominance penalty 觸發條件是：

```
single-source, no cross-source resonance, no high-signal term, momentum_delta <= 1
```

其中 **「no high-signal term」** 正是豁免路徑。因此本分支**不削弱 dominance guard**，而是擴充 `high_signal_terms`：實質性的金融事件因此得以脫離上限，而例行性的央行發言仍受限制。這是刻意的設計選擇。

---

## 來源治理

`config/source_governance.yaml` 定義本專案要避免的退化型態：

- 過多的一般性主流／大型媒體來源
- 單一主機或單一類別過度集中
- 過多供應商／程式庫／機率訊號而缺乏對照來源
- 來源類別不明或缺漏
- 早期訊號覆蓋不足

`scripts/source_quality_guard.py` 於每次執行後評估清單、網路與簡報，並寫出：

```
briefings/source_quality.json
briefings/source_quality.md
```

此守衛屬於早期預警層。它不會因每個警告就中斷工作流程，但會讓退化現象可見。

> **本分支的修正：** 上游 `config/macro_sources.yaml` 將三個 BIS 訂閱標為 `source_class: "central_bank_network"`，但該類別**未出現在任何類別清單中**，因此被計入 unknown-class 配額（上限 0.20）。本分支已將 `central_bank_network` 加入 `institutional`。此為上游既有問題，與金融加權無關。

---

## 主要輸出

```
briefings/latest.json          # 目前的儀表板／當日資料池
briefings/latest.md            # 人類可讀的簡短局勢
briefings/network.json         # 叢集／Network Hub／共振排序
briefings/breaking.md          # 熱門／突發訊號
briefings/source_manifest.json # 疊加合併後的啟用來源
briefings/source_manifest.md   # 可讀的來源總覽
briefings/source_quality.json  # 來源治理評估
briefings/source_quality.md    # 可讀的來源治理評估
reports/latest_atom.md         # 標準化的執行 atom
data/YYYY-MM-DD/findings.json  # 當日資料集
state/seen.json                # 去重狀態
state/velocity.json            # 動能狀態
```

---

## GitHub Actions

工作流程：`.github/workflows/monitor.yml`

節奏：`*/5 * * * *`

治理參數：

| 項目 | 值 |
|---|---|
| Job timeout | 8 分鐘 |
| Monitor timeout | 5 分鐘 |
| Hot-Lane | 每 5 分鐘 |
| Macro-Lane | 每 15 分鐘或手動 |
| `MAX_ITEMS_PER_SOURCE` | 排程執行時為 6 |
| HTTP timeout | 8 秒 |
| HTTP retry attempts | 排程執行時為 1 |

排程執行的預算刻意設得很緊。廣度**不是**靠每個訂閱抓取大量項目而來，而是靠更好的來源組合、共振、動能與基線偏離。

---

## 界限

本系統不檢查私人帳號、封閉社群、登入區、付費資料庫，也不使用未經授權的介面。

**不允許：**

- 起底（Doxxing）
- 跟蹤騷擾（Stalking）
- 竊取憑證
- 繞過存取控制
- 大規模抓取
- 第三人的私人個資
- 將未經證實的指控當作事實
- **從機率或市場資料衍生投注／投資建議**

> 最後一項在本分支中特別重要。本分支提高了金融訊號的權重，因此更容易被誤用為投資決策工具。
> **這套系統輸出的是「有東西正在發生」的訊號，不是「該怎麼做」的建議。**
> 它不產生買賣建議、不產生目標價、不產生部位建議。使用者若在金融機構工作，其所屬機構的法遵與內線交易規範一律優先於本工具的任何輸出。

---

## Senna 應如何讀取本專案

取得目前局勢時，優先讀取：

```
briefings/latest.json
briefings/network.json
briefings/source_quality.json
briefings/source_manifest.json
reports/latest_atom.md
```

**不要**從 `README.md` 推斷上一次執行實際啟用了哪些來源。該資訊由 `briefings/source_manifest.json` 提供。

---

## 發展方向

本專案向前推進的方式不是增加更多一般性訂閱，而是更好的感測能力：

- 更多小而具體、類別明確的早期指標
- 更好的跨來源佐證
- 更強的基線／動能模型
- 每次執行都有透明的來源品質
- 減少單一主機、供應商與主流媒體的支配
- 為簡短且可行動的簡報提供更好的交付

本分支另補上一項：

- **針對台灣使用情境的在地化感測** —— 半導體供應鏈、地震與颱風的實體風險傳導、出口管制與實體清單、上市櫃重大訊息揭露。

---

END OF DOCUMENT
