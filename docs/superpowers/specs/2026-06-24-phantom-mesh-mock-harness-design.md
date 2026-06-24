# phantom-mesh Mock + Integration-Test Harness — Design

> Date: 2026-06-24 · Branch: `feat/phantom-mesh-mock-harness` · Status: design (approved, pending spec review)
> Approach: **A — Dev-crew** (the three agents are a build/review crew; the mock router is deterministic).

## 1. Purpose & scope

phantom-finance is the "financial brick" of the **phantom-mesh** ecosystem (the *main project*). The real
phantom-mesh is not connected yet, so two of phantom-finance's integration seams cannot be exercised end-to-end
(this gap was confirmed in the project analysis: the LLM categorization path and event consumption are never
integration-tested).

This project builds an importable **`phantom_mesh` stand-in package** that implements exactly those two seams,
plus a `tests/integration/` suite that drives phantom-finance against it end-to-end. The three "AIs"
(claude / codex / hermes) are realized as **Claude subagents on different model tiers**, acting as a
**build/review/gate crew** (write = codex, review = hermes, gate = claude), mirroring the phantom-mesh
collaboration model described in `docs/phantom-finance.md`.

**This is purely additive.** No phantom-finance production code is modified. When the real phantom-mesh is
available, it replaces the mock and the same contract-level tests run against it.

### Non-goals (YAGNI)
- No real LLM calls and no network access of any kind.
- No live agent bridge / file-based RPC between the Python runtime and the agent layer (that is Approach B/C, deferred).
- The mock is **not** published to PyPI; it is a local development stand-in only.
- **No fixes to phantom-finance production code.** If an integration test reveals a real defect (e.g. one of the
  bugs found in the prior analysis), it is *flagged and reported*, not silently fixed. Fixing is a separate,
  user-approved track.

## 2. The two integration seams (exact contracts, verified against source)

### Seam ① — Model router (inbound to phantom-finance)
From `phantom_finance/llm.py`:
- `from phantom_mesh import router as mesh_router` — so `phantom_mesh` must be importable and expose a `router`
  attribute (a submodule is fine).
- `complete = getattr(mesh_router, "complete", None)`; used only if `callable(complete)`.
- Called as `router.complete(prompt: str) -> str`.
- The prompt has a fixed shape:
  `"Reply with EXACTLY ONE category from this list (or the literal word none): {categories}. Transaction: {description}."`
- phantom-finance post-processes the answer: take the first non-empty line, `strip().lower()`, and **accept it only
  if it is in `known_categories()`** = `set(categorize.DEFAULT_RULES.values()) | {"income", "transfer"}`.
- The whole path is gated by env `PHANTOM_FINANCE_LLM`: if unset or in `{off, 0, false, none, ""}` → router is
  never located (returns `None`), categorization stays pure-rules.

### Seam ② — Event sink (outbound from phantom-finance)
From `phantom_finance/events.py` + `paths.py`:
- Events are written under `events_dir()` = `$PHANTOM_MESH_HOME/events` (default `~/.phantom-mesh/events`).
- One directory per event: `<event_id>/meta.json`, where
  `event_id = "<UTC %Y%m%dT%H%M%S>-phantom-finance-<kind>"`.
- `meta.json` schema: `{"source": "phantom-finance", "kind": <str>, "ts": <ISO-8601 UTC>, "payload": <dict>}`.
- The only `kind` currently emitted is `"monthly-report"` (from `reporter.write_report`).

> Test isolation already exists: `tests/conftest.py` redirects `PHANTOM_MESH_HOME` and `PHANTOM_FINANCE_HOME`
> into `tmp_path` via an autouse fixture, so the mock and the events dir are naturally sandboxed per test.

## 3. Mock package API (`mock_mesh/phantom_mesh/`)

### `phantom_mesh/router.py`
```python
def complete(prompt: str) -> str: ...
```
- Parses the `description` out of the fixed-format prompt
  (`prompt.split("Transaction: ", 1)[1].rsplit(".", 1)[0].strip()`), and optionally the allowed `categories`.
- Routes the description to a **deterministic "3-AI panel"**: three independent `dict[str, str]`
  keyword→category maps named `CLAUDE_RULES`, `CODEX_RULES`, `HERMES_RULES`, each covering merchants **not** in
  phantom-finance's `DEFAULT_RULES` (so the LLM tier demonstrably adds value over the rule tier). Each panelist
  returns its first substring match or abstains; the result is the **majority vote**. Tie or no quorum (< 2
  agreeing) → return the literal `"none"`.
- This deterministically embodies the docs' "≥2 distinct-AI consensus" while staying fully repeatable.

**Fault-injection for fail-closed testing** (no production-code change needed):
- Env `PHANTOM_MESH_MOCK_MODE`:
  - unset / `vote` (default) → normal panel vote.
  - `invalid` → always return a category guaranteed **not** in `known_categories()` (e.g. `"definitely-not-a-real-category"`).
  - `raise` → raise `RuntimeError("mock router forced failure")`.
  - `empty` → return `""`.

### `phantom_mesh/companion.py`
```python
class Event(TypedDict): source: str; kind: str; ts: str; payload: dict

@dataclass
class ConsumeResult:
    events: list[Event]      # only schema-valid events
    errors: list[str]        # one human-readable message per malformed/invalid meta.json

def is_valid(meta: object) -> bool: ...                       # schema predicate
def consume(events_dir: str | os.PathLike) -> ConsumeResult: ...
def correlate(events: list[Event]) -> dict: ...
```
- `is_valid(meta)` is the single schema predicate: `meta` is a dict with exactly the keys
  `{source, kind, ts, payload}`, `source == "phantom-finance"`, `kind` and `ts` are non-empty strings, and
  `payload` is a dict.
- `consume()` scans `events_dir` for `*/meta.json`, parses each, and partitions them: valid ones go into
  `result.events`, anything malformed (bad JSON or failing `is_valid`) goes into `result.errors` as a message.
  It **never raises** on a malformed file — that resilience is the contract test #6 pins.
- `correlate()` is a minimal stand-in for companion's spend×behavior correlation: e.g. sum `payload` expense/income
  fields across `monthly-report` events. Just enough to prove the payload is consumable downstream.

### `phantom_mesh/__init__.py`
- Re-exports `router` and `companion` so `from phantom_mesh import router` resolves.

### `mock_mesh/README.md`
- States this is a **mock**, documents the two seams it satisfies, and explains the swap-to-real procedure
  (see §6).

## 4. Integration tests (`tests/integration/`)

`tests/integration/conftest.py`:
- Prepends `mock_mesh/` to `sys.path` so `import phantom_mesh` resolves to the mock (no install step).
- Helper fixtures to set `PHANTOM_FINANCE_LLM` and `PHANTOM_MESH_MOCK_MODE` per test (monkeypatch).
- Inherits the repo-root autouse `isolated_home` fixture (tmp `PHANTOM_MESH_HOME` / `PHANTOM_FINANCE_HOME`).

`tests/integration/test_mesh_integration.py`:

| # | Test | Asserts |
|---|------|---------|
| 1 | `test_router_categorizes_unseen_merchant` | LLM on + import CSV with a merchant absent from `DEFAULT_RULES` but known to the panel → that txn gets the panel's category. |
| 2 | `test_llm_disabled_by_default` | `PHANTOM_FINANCE_LLM` unset → router never consulted; unseen merchant stays `uncategorized` (or income by sign). |
| 3 | `test_invalid_category_is_clamped` | `PHANTOM_MESH_MOCK_MODE=invalid` → phantom-finance rejects it → txn stays `uncategorized`. |
| 4 | `test_router_exception_is_swallowed` | `PHANTOM_MESH_MOCK_MODE=raise` → no crash; pure-rules result. |
| 5 | `test_event_emitted_and_consumed` | Run `reporter.write_report` → event dir written → `consume()` returns `ConsumeResult` with `len(events) == 1`, valid schema, expected `kind`/payload keys, and `errors == []`. |
| 6 | `test_companion_survives_malformed_event` | Hand-write a broken `meta.json` alongside a good one → `consume()` returns the good one in `events` and one message in `errors`, without raising. |

These six map 1:1 onto the integration gaps identified in the prior analysis (LLM inbound path untested; event
consumption untested; fail-closed behaviors asserted only at the unit level, never end-to-end through ingest/report).

## 5. Dev-crew orchestration (how claude / codex / hermes manifest)

Execution uses one `Workflow` with three phases. Model tiers give genuine behavioral diversity; the names are
stand-ins for the future real agents.

| Role | Model (default) | Responsibility |
|------|-----------------|----------------|
| **codex** | `sonnet` | Phase *Write* — implement `mock_mesh/phantom_mesh/*` and `tests/integration/*` per this spec. |
| **hermes** | `haiku` | Phase *Review* — **independent** adversarial check: does the mock match the seam contracts *verbatim*? do the tests actually exercise the seam (not tautologies)? missing edge cases? Returns structured findings. |
| **claude** | `opus` (main loop, the orchestrator) | Phase *Gate* — apply review fixes, run `pytest tests/integration -q` and `pytest tests/ -q` for real, gate on green. |

- The reviewer (hermes) does **not** write the code it reviews — independence is the point.
- The gate is evidence-based: the orchestrator only declares success after showing real `pytest` output.

## 6. File layout & swap-to-real

```
phantom-finance/
  mock_mesh/
    README.md
    phantom_mesh/
      __init__.py
      router.py        # complete(prompt) -> category  (deterministic 3-AI panel + fault injection)
      companion.py     # consume(events_dir) / correlate(events)  + schema validation
  tests/
    integration/
      conftest.py      # mock_mesh on sys.path; LLM/mode fixtures
      test_mesh_integration.py
  docs/superpowers/specs/2026-06-24-phantom-mesh-mock-harness-design.md   # this file
```

**Swap to the real phantom-mesh later:** the mock only occupies the `phantom_mesh` import name via
`mock_mesh/` on the *test* sys.path; production imports are untouched. To use the real project, install the real
`phantom_mesh` package and stop adding `mock_mesh/` to the path. Contract-level assertions (schema valid, fail-closed
behavior, event consumed) carry over unchanged; only the mock-specific category expectations in test #1 are
mock-bound and are kept isolated/parametrized so they are easy to retarget.

## 7. Success criteria
- `pytest tests/integration -q` is green.
- `pytest tests/ -q` shows **no regression** (the existing suite still passes; the mock and integration tests are
  additive and sandboxed).
- The LLM inbound path runs end-to-end with `PHANTOM_FINANCE_LLM=on` for the first time.
- An emitted event is consumed and schema-validated by the mock companion.
- All three fail-closed behaviors (invalid category clamped, exception swallowed, disabled→not called) are asserted
  end-to-end.
- Any real phantom-finance defect surfaced by a test is reported in the final summary, not silently patched.

## 8. Open items / future work
- Approach B/C (live multi-agent router via a bridge) when the real agents are wired.
- Additional event `kind`s as phantom-finance emits more (only `monthly-report` exists today).
- Sharing the contract-level tests as a reusable conformance suite the real phantom-mesh must also pass.
