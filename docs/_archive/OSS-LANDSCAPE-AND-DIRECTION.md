> ARCHIVED 2026-06-19 — 內容已併入 docs/phantom-finance.md;此為歷史版本。

# 開源生態與建議方向 — phantom-finance

> 開源個人理財／預算編列／淨值追蹤工具的概覽，以及 **phantom-finance**
> 相對於這些工具應該定位於何處。權責說明:本文是一份**方向／參考**
> 文件,**並非**對交付狀態的承諾。實際已交付內容的唯一真實來源,
> 仍是 [`/ROADMAP.md`](../ROADMAP.md)。
>
> 星數與版本是在 **2026-06-19** 對照 GitHub 上的實際倉庫所驗證,並四捨五入
> 至當天 GitHub 顯示的數字;請將其視為一次快照,而非即時數值。
> 無法驗證的主張標記為 `[unverified]`。

---

## 1. phantom-finance 的目前狀態(有所本)

以 [`ROADMAP.md`](../ROADMAP.md) 與原始碼樹(`phantom_finance/`)為依據:

**今日已交付** — 一個單一使用者、local-first 的 Python CLI(Apache-2.0):

- JSONL ledger、全程使用 `Decimal`、sha256 `txn_id` 去重、可冪等重複匯入、
  防當機的原子寫入(lock-file + temp/replace + `.bak`)— `ledger.py`。
- CSV 匯入,具備 zh/en 表頭自動偵測、BOM、ROC(民國)日期、`NT$1,234`
  解析、透過 `--bank` 提供的台灣銀行預設組(Cathay / CTBC / E.SUN / Taishin)—
  `ingest.py`、`presets.py`。
- 規則分類器(80+ 組 zh/en 關鍵字)+ 使用者 `rules.json` 覆寫 + 一個
  **離線安全的 LLM 後援掛勾**,僅在 `PHANTOM_FINANCE_LLM` 啟用且
  `phantom_mesh.router` 可被 import 時,才接上 phantom-mesh 模型路由器;
  否則維持純規則 — `categorize.py`、`llm.py`。
- 月度預算(排除轉帳)、不帶羞辱感的月度報告、報告中呈現的循環扣款 /
  訂閱與漲價偵測 — `budget.py`、`reporter.py`、`recurring.py`。
- 多幣別 + 淨值:`rates.json`、資產帳戶 vs 現金帳戶、`net-worth`
  指令、報告中的淨值／可支配金額欄位 — `networth.py`。
- 將事件輸出至 `~/.phantom-mesh/events/`(一個目錄 + `meta.json`),供
  phantom-companion 消費 — `events.py`。

**下一步規劃中(依 ROADMAP,尚未建置):**循環扣款的持久化 + 審閱
狀態、companion 端的消費×行為×健康相關性分析(依賴 companion)、
`phantom skill` 自然語言問答、報告的手機/Telegram 推播。

**這個利基(要守住的東西):**phantom-finance *並非*一個獨立的理財
app。它是**一個私有、與 mesh 整合的 life-track 之中的「財務磚塊」**——
一條小巧的 ingest→categorize→report→**emit-event** 流水線,其差異化
產出是一個 `mesh event`,讓一個獨立的 companion 能將消費與行為／健康
／生產力相關聯,且資料**永遠不離開本機**。護城河在於整合 +
資料主權 + zh-TW/台灣銀行的契合度,**而非**功能廣度。

---

## 2. 生態概覽 — 完整的個人理財 app

| Project | URL | Stars | Lang | License | 成熟度 | 本地 / 隱私 |
| --- | --- | --- | --- | --- | --- | --- |
| **Actual Budget** | github.com/actualbudget/actual | ~27.1k | TypeScript | MIT | 成熟、非常活躍 | **Local-first**,可選用自架同步伺服器 |
| **Firefly III** | github.com/firefly-iii/firefly-iii | ~23.8k | PHP | AGPL-3.0 | 成熟、活躍(v6.6.3,2026 年 5 月) | 自架;「在你指示之前,從不聯繫外部伺服器」 |
| **Maybe Finance** | github.com/maybe-finance/maybe | ~54.2k | Ruby/Rails | AGPL-3.0 | **2025-07-27 已封存**(無人維護) | 自架;前 VC 新創,開源後遭棄置 |
| **sure**(Maybe fork) | github.com/we-promise/sure | ~8.7k | Ruby/Rails | AGPL-3.0 | Maybe 的活躍社群延續 | 與 Maybe 相同的定位 |
| **GnuCash** | github.com/Gnucash/gnucash | ~4.3k | C/C++/Scheme | GPL-2.0/3.0 | 非常成熟,桌面版(v5.x,2025 年 12 月) | 完全本地的桌面複式記帳 |

備註:
- Maybe 的 5.4 萬星是**一個歷史人氣訊號,而非健康訊號**——該倉庫
  已封存;那裡的淨值追蹤點子值得*閱讀*,而非依賴。
- Actual = **把 local-first 做好**的最強參考(同步而無強制雲端)。
  Firefly = **豐富報表 + 預算 + 匯入規則**的參考。兩者都是完整的 web app
  ——比 phantom-finance 的 CLI 利基更重。

## 2b. 生態概覽 — 純文字記帳(PTA)引擎

| Project | URL | Stars | Lang | License | 契合訊號 |
| --- | --- | --- | --- | --- | --- |
| **Beancount**(v3) | github.com/beancount/beancount | ~5.7k | Python | GPL-2.0 | 最嚴格的資料完整性;Python API ⇒ 最易於從 Python 專案*內嵌* |
| **hledger** | github.com/simonmichael/hledger | ~4.5k | Haskell | GPL-3.0 | 評價最佳的 CSV 匯入規則;整理過的 Ledger |
| **Ledger** | github.com/ledger/ledger | ~6.0k | C++ | BSD-3 | 元祖(2003);快速、精簡 |

PTA 契合度:Beancount/hledger 在*持久的複式記帳 + 報表*上,遠勝於自製
ledger。**授權注意:**Beancount/hledger/Ledger 為 GPL/BSD;一個
Apache-2.0 專案可以*以檔案格式互通*(讀寫 `.beancount`/journal 文字)
而無顧慮,但**將 Beancount 作為 Python 函式庫 import 會把你耦合到
GPL-2.0**——除非你打算重新授權,否則請保持在格式層級,而非 import 層級。

## 2c. 生態概覽 — AI / LLM 個人理財代理

| Project | URL | Stars | Lang | License | 契合訊號 |
| --- | --- | --- | --- | --- | --- |
| **personal-financial-ai-agent** | github.com/merendamattia/personal-financial-ai-agent | ~3 | Python | Apache-2.0 | 多 LLM(Ollama/Gemini/OpenAI)、隱私優先離線;**不成熟(3★)**但屬 Apache 授權的 Ollama 後端理財聊天參考 |
| **Personal-Finance-Agent** | github.com/Kirushikesh/Personal-Finance-Agent | ~15 | Python | MIT | 對話式收支登錄 + 自然語言分析;停滯(最後一次 push 為 2024-08) |
| **WiseCashAI** | (DEV.to 撰文;倉庫 `[unverified]`) | `[unverified]` | `[unverified]` | `[unverified]` | 「AI 分類 + 信封式預算,資料留在本地」 |
| **simonw/llm** | github.com/simonw/llm | ~12.1k | Python | Apache-2.0 | *並非*理財——但它是一個乾淨的 Apache-2.0 CLI/函式庫,可與本地(Ollama)+ 雲端 LLM 對話;是模型路由器接縫的參考 |

AI 代理契合度:現有的 AI 理財代理都**早期、星數低、且以聊天為先**
(對你的資料做自然語言問答)。它們沒有一個是*與 mesh 整合、能輸出
事件的 life-track 磚塊*——那個缺口正是 phantom-finance 的利基。對這一列
誠實的解讀是:**隱私優先的本地 LLM 分類如今是基本門檻,而非護城河**
(DEV.to / KDnuggets / Medium 的逐步教學顯示 Llama-3 + Ollama 分類器
是個週末專案)。phantom-finance 已經有了對的接縫(`llm.py` 離線安全
掛勾);差異化在於*它對分類後資料下游做了什麼*,而非分類器本身。

---

## 3. 建議的設計方向

每個選項的拇指法則:**直接採用**(依賴它)、**包裝**(shell out / 讀取
它的檔案)、**參考**(借鏡點子,而非程式碼)、**自建**(因為這就是
利基,所以擁有它)。

| 能力 | 裁決 | 原因 |
| --- | --- | --- |
| 核心 ingest→categorize→report→**emit-event** 流水線 | **BUILD**(已建置) | 這*就是*利基;沒有任何開源工具輸出 mesh life-track 事件。持續擁有它。 |
| zh-TW / 台灣銀行 CSV 預設組、ROC 日期、`NT$` 解析 | **BUILD**(已建置) | 沒有開源工具把台灣銀行涵蓋得好;持久的本地優勢。守住。 |
| LLM 分類器後援 | **WRAP / REFERENCE** | 保留既有的離線安全 `llm.py` 接縫;經由 phantom-mesh 自己的路由器(且/或 Ollama)轉送。**不要**採用一個笨重的 AI 代理依賴——它們不成熟,且會顛倒依賴方向。僅就 provider 抽象的形態參考 `simonw/llm` / personal-financial-ai-agent。 |
| 持久的複式記帳 ledger / 進階報表 | **REFERENCE(格式層級),不要 import** | 若/當 JSONL ledger 成長超出自身負荷,**以輸出/讀取 Beancount/hledger 的文字格式來互通**,而非 import 它們(GPL 耦合 + 範圍蔓延)。對一個單一操作者工具而言,你最可能永遠不需要這個。 |
| 淨值追蹤的使用體驗 | **REFERENCE** | 閱讀 Maybe(已封存)與 Actual 的淨值/資產建模點子;借鏡概念,而非程式碼。phantom-finance 的 `networth.py` 對此利基已經足夠。 |
| 預算信封模型 | **REFERENCE** | 若預算功能日後加深,Actual 的信封/結轉模型是黃金參考;今日的 `budget.py` 刻意維持精簡。 |
| Web UI / 行動 app / 多使用者 / 雲端同步 | **DO NOT BUILD** | 超出利基;那是 Actual/Firefly 的領域,也是一個過度建置的陷阱(見 §5)。手機觸達應該是*報告的推播*,經由 mesh,而非一個新 app。 |

**一句話方向:***維持為一個小巧、local-first、與 mesh 整合的 CLI 磚塊。
持續擁有 ingest→event 流水線與 TW/zh-TW 的邊角優勢。把 LLM 分類視為
你所包裝的一個商品化接縫,並把笨重的 PTA/理財引擎視為你永不依賴的
格式層級參考。*

---

## 4. 分階段路徑(方向,而非 ROADMAP 承諾)

這些對應到、且不凌駕於 [`ROADMAP.md`](../ROADMAP.md) 的「下一步規劃中」。
此處的開源選擇是**候選方向**,而非承諾。

- **Phase 1 — 廉價地完成這個迴圈(高價值、無新依賴)。**循環扣款的
  持久化 + 審閱狀態(已在「下一步規劃中」);既有報告事件的手機/Telegram
  推播。不需要任何外部理財開源。
- **Phase 2 — 讓資料可被問答。**`phantom skill` 對 ledger 做自然語言
  問答(「這個月外食多少?」),經由既有的 mesh 模型路由器 / Ollama 轉送。
  候選參考(非依賴):`simonw/llm` 的 provider 形態。維持 LLM 可選且
  離線安全。
- **Phase 3 — 護城河:companion 相關性分析。**在 companion 端做
  消費 × 行為 × 健康相關性分析,消費所輸出的事件。這是*沒有*任何開源
  理財工具在做的事,也是存在的理由。自建,不要採用。
- **Phase 3+(僅在真正出現需求時)— 互通,而非遷移。**選用的
  Beancount/hledger **匯出**,讓進階使用者能跑 PTA 報表,保持在格式
  層級以避免 GPL 耦合。多數單一操作者的設定永遠不會需要它。

---

## 5. 誠實的過度建置與隱私警示

- **過度建置陷阱 #1 — 變成一個理財 app。**Actual/Firefly 已經以 2 萬+
  星與多年打磨,擁有完整 web app、多使用者、同步的領域。作為單一操作者
  在那裡競爭是一筆虧本交易,且*摧毀利基*。手機故事是**一則報告的推播
  通知**,而非一個要維護的新 app。
- **過度建置陷阱 #2 — 笨重的 LLM 代理。**採用一個 AI 理財代理框架
  會顛倒依賴(phantom-finance 應該*擁有*自己的流水線並*使用*一個模型
  路由器,而非住在別人的代理裡)。本地 LLM 分類如今是商品;不要把它
  當成護城河般過度投資。
- **過度建置陷阱 #3 — 重新實作複式記帳 / PTA。**若日後真需要持久記帳,
  *以檔案格式與 Beancount/hledger 互通*;不要重建它們,也不要 import
  它們(GPL 耦合 + 範圍蔓延)。
- **授權衛生。**phantom-finance 是 **Apache-2.0**。Maybe/Firefly 為
  AGPL-3.0;Beancount/hledger/GnuCash 為 GPL。閱讀它們的使用體驗並借鏡
  *點子*沒問題;複製程式碼或作為函式庫 import 會引入 copyleft。除非
  刻意決定重新授權,否則一切重用都保持在**格式 / 概念**層級。
- **隱私是產品,而非一項功能。**差異化在於財務資料永遠不離開本機。
  任何未來的 LLM 步驟都必須預設**關閉**並保持**離線安全**(目前的
  `llm.py` 即如此)。一個雲端 LLM 分類器會悄悄違背核心承諾——本地/Ollama
  路徑必須永遠是預設,任何雲端轉送都必須是明確且選擇加入(opt-in)的。
- **`[unverified]` 項目**(上方 WiseCashAI 倉庫的身分/授權)在 2026-06-19
  未經實地確認;在以它們為關鍵依據引用前請先驗證。其他倉庫的星數/授權
  數字已於 2026-06-19 對照 GitHub API 確認。

---

## Sources

- [Firefly III](https://github.com/firefly-iii/firefly-iii)
- [Actual Budget](https://github.com/actualbudget/actual)
- [Maybe Finance](https://github.com/maybe-finance/maybe) · [sure fork](https://github.com/we-promise/sure)
- [GnuCash](https://github.com/Gnucash/gnucash)
- [Beancount](https://github.com/beancount/beancount) · [Plain Text Accounting](https://plaintextaccounting.org/)
- [Beancount/hledger/Ledger showdown 2025](https://beancount.io/forum/t/the-ultimate-plain-text-accounting-showdown-2025-beancount-v3-vs-hledger-vs-ledger/81)
- [personal-financial-ai-agent](https://github.com/merendamattia/personal-financial-ai-agent) · [Personal-Finance-Agent](https://github.com/Kirushikesh/Personal-Finance-Agent)
- [simonw/llm](https://github.com/simonw/llm)
- [WiseCashAI writeup](https://dev.to/allanninal/building-wisecashai-an-open-source-ai-powered-personal-finance-tracker-57g0) · [Local LLM finance analyzer (DZone)](https://dzone.com/articles/local-llm-finance-tracker)
