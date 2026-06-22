# phantom-finance — 定位重定 (B+A) 與路線圖設計

- **日期:** 2026-06-22
- **狀態:** DRAFT（待 owner review → 進 writing-plans）
- **作者:** Claude Code(brainstorming 流程;依據 6 家 AI 意見 + 市場研究 + owner 拍板）
- **關係:** 本文**修訂** `docs/phantom-finance.md` 的〈定位與護城河〉與〈刻意不做〉。實作落地後再回填主文件;在那之前,定位以本文為準。

---

## 0. 一句話定位

> **phantom-finance = 台灣接案族 / 一人公司的「本機帳務 + 報稅整理」工具。**
> 隱私(local-first)是信任底座,接案/報稅是收得到錢、會回流的核心價值,AI 與 mesh 是放大層。
> 「資料不離開你的電腦,你的 AI 夥伴還能讀它,幫你把帳記好、把稅整理好。」

## 1. 背景與決策(為什麼是 B+A)

原本主文件把 finance 定位為「A:隱私優先的個人 local-first 記帳磚塊」,且刻意不做 app/SaaS。但 owner 確立一條跨衛星原則:**每個衛星要(1)單獨佔住 + (2)接上 4 個 AI(codex/claude/openclaw/hermes)與 mesh 後更強,但沒接也能用。** 在此原則下重新評估:

- **6 家本機 AI 投票**(2026-06-22):A 主軸 3(codex/hermes/claude)、B 1(agy)、2 棄(opencode 逾時、openclaw OAuth 過期)。AI 多憑「範圍小、快出、避開 Actual/Firefly」選 A。
- **市場研究(有來源)反指 B**:
  - 隱私個人理財是 **wedge 不是 wallet**(隱私 app 爆紅卻只賺 $353;Maybe 募 145 萬仍倒、pre-OSS Actual 養不起)→ solo B2C 個人理財是墳場。
  - 接案/報稅是**政府死線逼的、用錢計價、會回流**的需求(記帳士 NT$2.5–4.5 萬/年當願付錨)。
  - **台灣是綠地**:沒有任何 app 把 載具/電子發票 + 銀行資料 + AI 分類 → 串成 執行業務/一人公司報稅輸出。
  - NL「問帳」是**獲客鉤非留存**(Cleo、OpenAI 個人理財自家 benchmark 79/100)。
  - **mesh 角度 B 更強**:乾淨、標好可扣抵的結構化資料,才是 companion 最想查、最能行動的底料。
- **後悔不對稱**:選 B 錯了 → 還有能用的個人記帳工具 + 學會稅務(下檔有限);選 A 錯了 → 沒護城河的 commodity 掉進墳場。**B 才是低後悔。**

**決策(owner 拍板):錨定 B,A 當信任底座、C(NL/CLI)當 mesh 放大層 = 「B+A」。**

## 2. 三層界線(對應「單獨佔住 + 接 AI 更強」)

| 層 | 不接任何東西(純本機離線) | 接 4 AI | 接 mesh / companion |
|---|---|---|---|
| **能力** | 規則分類 + 月/季報 + 報稅欄位 全部可跑 | 分類**補完**沒見過的商家、**自然語言問帳** | 事件 + agent **主動行動** |
| **角色** | **單獨佔住**(baseline) | 更聰明 | 更有未來 |
| **不可違反** | 沒網路/沒 AI 也要能產出正確報表 | AI 預設 **off**、離線安全 | 任何外送一律經 mesh 既有同意機制 |

**鐵則:** AI 永遠是**補完**,不是必需;稅務與金額**永遠規則式 deterministic**,不交給會幻覺的 LLM。

## 3. 架構取向

**延伸現有成熟管線,不重寫。** 現有模組(皆在 `phantom_finance/`)即骨幹:

```
bank CSV / manual add
   └─ ingest.py / presets.py ─→ categorize.py(規則 + llm.py 補完 hook)─→ ledger.py(JSONL, Decimal, dedupe, crash-safe)
                                                                              ├─ budget.py
                                                                              ├─ recurring.py(訂閱/漲價)
                                                                              ├─ networth.py(資產/淨值)
                                                                              └─ reporter.py(月報)─→ events.py ─→ ~/.phantom-mesh/events/ ─→ companion
```

B+A 不改這條骨幹,而是**在三處加值**:(i) `categorize.py` 升級成 correction→rule 學習引擎;(ii) `reporter.py` 增加接案族/報稅欄位 + 季報;(iii) 新增稅務模組(Phase 2)與 mesh 曝露層(Phase 3)。

## 4. 三階段 arc

### Phase 1 — 單獨能用(先出,純本機可跑)
把現有引擎**瞄準接案族**,不依賴 AI/mesh 也完整:
1. **報告新增台灣稅務語彙欄位**(`reporter.py`):收入分流到 **9A(執行業務)/ 9B / 薪資** 等類別、**可扣抵候選標記**、**二代健保補充保費**(單筆 ≥ NT$20,000)與 **10% 扣繳** 旗標。
2. **接案族月報 + 季報**:沿用 shame-free 措辭,新增「本季收入/可扣抵/應留意」彙整。
3. **中心功能 —「可更正、會學習的分類引擎」**(見 §5)。

### Phase 2 — 報稅 wedge(會黏、能回本)
4. **執行業務:列舉實際費用 vs 標準成本率比較**(例:程式設計 20%),輸出「哪種報法較省」的**事實比較**(非建議)。
5. **年度報稅包**:可交給記帳士或自己報的整理輸出(收入/憑證/扣抵彙整)。
6. **載具 / 電子發票 ingestion**:當作**結構化、line-level 的交易來源**(比銀行 memo 更好的分類燃料)。
7. **憑證歸檔**:把單據/發票對應到交易。

### Phase 3 — mesh / agent 層
8. **透過 MCP/事件把 ledger 曝露給 companion**:grounded NL 問帳(RAG/tool-call over deterministic 帳本,不是生成猜測)。
9. **agent 主動行動**:報稅死線提醒、≥NT$2萬扣繳旗標、年收破 ~100–120 萬「該考慮設公司」提示。

## 5. 中心功能規格 —— correction → rule 學習式分類引擎

**目標:** 規則優先、AI 補完,且**每一次人工更正都自動沉澱成一條新規則**,使分類**越用越準、可稽核、可離線**。同時這份高品質結構化資料就是餵 companion 的底料。一石三鳥(護城河 + 信任 + mesh 燃料)。

**運作:**
1. 進帳交易 → `categorize.py` 先跑**確定性規則**(現有 80+ zh/en 關鍵字 + 使用者 `rules.json`)。
2. 命中 → 直接分類(離線、零成本)。未命中 → 標 `uncategorized`(可選:若 `PHANTOM_FINANCE_LLM` 開啟且 backend 可用,呼叫 AI **建議**一個類別,標為「AI 建議、待確認」,**不自動定案**)。
3. 使用者 `recat` 更正某筆 → 引擎**提煉出一條可重用規則**(商家字串/正則 → 類別 + 是否可扣抵 + 9A/9B),寫回 `rules.json`,並回填同商家的歷史交易。
4. 下個月起,同商家自動命中該規則,**不再需要 AI、不再需要人**。

**驗收(Phase 1):** 對同一商家更正一次後,後續匯入該商家**零人工、零 AI 命中正確**;規則檔人類可讀可編輯;全程離線可跑;AI 關閉時功能不降級(只是少了「未見商家的建議」)。

## 6. 接 4 AI / mesh 的方式(已就緒的接縫)

- **分類補完**:`llm.py` 既有離線安全 hook,現已可經 `phantom exec --provider hermes|openclaw|codex|claude` 選擇 backend(本生態系 2026-06-20 完成的 `--provider` 機制 + `PHANTOM_PROVIDER` 環境變數 passthrough)。預設 off。
- **NL 問帳**:Phase 3 以 MCP 曝露唯讀 ledger 查詢工具;NL grounded 在 deterministic 帳本。
- **mesh 事件**:`events.py` 既有 emit;companion 消費。

## 7. 護城河 / 刻意不做(更新版)

**護城河:** 台灣稅務語彙(9A/9B、二代健保、扣繳、可扣抵)× 台銀/載具在地 × local-first 信任 × 餵 companion。**這是國際工具(Actual/Firefly)懶得碰、而 owner 剛好最適合做的綠地。**

**刻意不做:**
- ❌ 雲端同步 / SaaS / 爬銀行 API（違反主權核心；自動同步只當 Phase 2+ 選配,核心永不依賴上游)。
- ❌ 投資建議 / 稅務「建議」（只陳述事實 + 比較,定位「報稅前整理」「給你的記帳士」）。
- ❌ 稅務或金額邏輯交給 LLM（一律規則式;LLM 只碰分類**建議**且預設 off）。
- ❌ 跟 Actual/Firefly 拚預算 UI 廣度 / web/mobile app（手機觸達只做「報告推播」經 mesh）。

## 8. 風險與緩解(來自市場研究)

1. **載具/銀行 CSV 匯入是維護地獄 + 最不可控**(Moneybook 差點被搞死、Actual/Firefly 一直壞)。→ **先靠手動 CSV(已具備),自動 載具/Open-Banking 同步當 Phase 2+ 選配,核心永不依賴它。**
2. **稅務正確性 = 監管領域的信任地雷**(財務 LLM 約 1/5 答錯)。→ **稅務邏輯一律規則式;輸出定位「報稅前整理 / 給記帳士」非建議;保留 human-in-the-loop。**
3. **利基有界 + 台灣稅規每年變(114/115 年…)+ solo 維護**。→ **稅務規則設計成可換 config**(引擎可推廣到其他市場,但只手維護台灣);核心維持 Apache-2.0 養信任與貢獻者;若要收費,收**報稅包/年度整理/託管同步**,不走 Maybe 那種倒掉的 B2C 訂閱。

## 9. 待確認 / owner-gated

- **台銀 presets 真實對帳單驗證**:目前僅對合成 fixtures 驗過(沿用主文件既有的 owner-gated 狀態)。
- 9A/9B/二代健保/扣繳 的具體門檻與類別對應,需依**當年度(115 年)**法規定版一次(規則式、可改 config)。
- Phase 2 載具 ingestion 的取得方式(發票存摺 API / 載具歸戶 匯出格式)待 owner 提供樣本。

## 10. 與主文件的關係

本文修訂 `docs/phantom-finance.md` 的〈定位與護城河〉(A→B+A)與〈刻意不做〉(新增稅務/LLM 邊界)。**既有 Tier 1→3 功能全部保留**(JSONL 帳本 / CSV ingest / 規則+LLM hook / 預算 / 月報 / 多幣別淨值 / 訂閱漲價 / mesh event);Phase 1 是在其上**加值瞄準接案族**,非重做。主文件於 Phase 1 落地後回填。
