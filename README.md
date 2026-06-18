# phantom-finance

[![CI](https://github.com/markl-a/phantom-finance/actions/workflows/ci.yml/badge.svg)](https://github.com/markl-a/phantom-finance/actions/workflows/ci.yml)

> **個人財務的 life-track 衛星** — 帳本 ingest(CSV / 手動)+ 規則式分類
> (LLM hook 已留好)+ 月預算 + shame-free 月報,所有資料 local-first 存在
> `~/.phantom-mesh/`,報告 emit event 給 phantom-companion 做跨域 correlation。

![license: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)
[![phantom-mesh ecosystem](https://img.shields.io/badge/ecosystem-phantom--mesh-purple)](https://github.com/markl-a/phantom-mesh)

> 📖 **Docs:** [docs/INDEX.md](docs/INDEX.md) (navigation) · **Status:** see [ROADMAP.md](ROADMAP.md) (the single source of truth for what is shipped / in progress / planned).

## 一句話 niche

記帳 app 不是雲端訂閱制(Moneybook / YNAB)就是手動到放棄(Excel)。
**phantom-finance 是 phantom-mesh 生活夥伴拼圖的財務塊** — 銀行 CSV 丟進來、
規則自動分類(中英文 merchant 都認)、錢的事實寫成 shame-free 月報,
然後變成 mesh event,讓 companion 能把「花費」跟「行為 / 健康 / 生產力」
放在同一張圖上看。資料永遠在你自己機器上。

## Status

完整的 shipped / in-progress / planned 狀態(含每項對應的 merge commit)以
[ROADMAP.md](ROADMAP.md) 為唯一來源 — see **[ROADMAP.md](ROADMAP.md)**。

> ⚠️ **Honest caveat**:分類是規則式的 — 沒見過的中文商家會留在
> `uncategorized` 等 `recat` 或 LLM hook。預算 / 報告對 `transfer` 類別自動排除,
> 但轉帳判斷也是規則式,搬大錢前先看一眼分類。

## 30-second quickstart

```bash
git clone https://github.com/markl-a/phantom-finance
cd phantom-finance
pip install -e .

# 手動記一筆(負數 = 支出,跟銀行 CSV 同號制)
phantom-finance add -- -120 "全聯 週末採買"

# 丟銀行對帳單(中英文表頭自動偵測,重複匯入自動去重)
phantom-finance import statement.csv --account cathay

# 設預算、看本月狀態
phantom-finance budget set dining 6000
phantom-finance budget show

# 月報(寫檔 + emit mesh event)
phantom-finance report --month 2026-06

pytest -v
```

報告寫到:

```
~/.phantom-mesh/logs/phantom-finance/<YYYY-MM>-report.md
```

## Architecture (within phantom-mesh ecosystem)

```
bank CSV / manual add
        |
        v
  ingest.py ──> categorize.py(rules + LLM hook)──> ledger.jsonl(JSONL, Decimal, dedupe)
                                                        |
                              +─────────────────────────+
                              v                         v
                        budget.py(月預算)          reporter.py(shame-free 月報)
                                                        |
                                  +─────────────────────+
                                  v                     v
              ~/.phantom-mesh/logs/phantom-finance/   ~/.phantom-mesh/events/
                                                        |
                                                        v
                                              phantom-companion(keystone)
                                              spend × behavior × health correlation
```

設計原則(跟全生態系一致):

- **local-first** — 沒有雲、沒有上傳,財務資料不出機器;`.gitignore` 直接擋
  `ledger.jsonl` / `*.csv` 防手滑 commit。
- **shame-free by construction** — 報告只陳述數字("over plan — worth a look"),
  羞辱句式在模板層就不存在,有測試擋。
- **Decimal end-to-end** — float 在 boundary 就 `TypeError`,金額不會有浮點誤差。

## License

Apache-2.0
