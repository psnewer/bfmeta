# Decision Log

## 2026-09-24 — Event-driven Python port

Status: the event-driven decision remains active; the basis-point spread decision below was superseded later on 2026-09-24.

Use the official Python SDK instead of embedding exchange calls in MQL5. Trigger decisions from WebSocket one-minute candle bucket changes, while using REST only for startup and authoritative reconciliation. This preserves the EA's approximate cadence without an `OnTimer` trading loop and avoids firing on every book update. See `hyperliquid-design.md` for the current design.

Use basis points for spread gating because the original absolute threshold is not portable across Hyperliquid markets. Default to testnet and dry-run to prevent accidental trading during migration.

## 2026-09-24 — Restore configurable timeframe and absolute spread

The initial port incorrectly treated the MQL5 variable name `M5` as a fixed interval and changed `limit_spread` to basis points. Reading the authoritative consumers showed that `M5` is an `ENUM_TIMEFRAMES` input passed to `CopyRates`, while spread is checked as `ask_1 - bid_1 < limit_spread`. Restore those semantics as `HL_TIMEFRAME` and absolute `HL_LIMIT_SPREAD`. See `hyperliquid-design.md` for the current design.

## 2026-09-27 — Adopt native position, precision, PnL, and heartbeat semantics

Use Hyperliquid's signed net position directly; virtual MT5-style tickets add state without preserving an exchange capability and were explicitly rejected. Derive order-size precision from each asset's `szDecimals`. Include `unrealizedPnl` with reconciled closed PnL so the strategy preserves the EA's margin signal and evaluation order. Use Hyperliquid's official JSON application heartbeat and retain only the latest pending minute event. See `hyperliquid-design.md` for the authoritative mechanism details.

## 2026-09-27 — Cancel existing orders and defer replacement

Do not combine cancellation and replacement within one evaluation. When a strategy decision encounters existing orders for its asset, cancel them and wait for the next minute event so the replacement uses fresh position and market state. This also keeps the lifecycle valid for future maker execution. See the Order Lifecycle section of `hyperliquid-design.md`.

## 2026-09-27 — Replace IOC execution with GTC

Use GTC limit orders so an unfilled strategy order may rest instead of being canceled immediately. Keep the cancel-and-defer rule to prevent an old resting order and its replacement from being active together. This supersedes the earlier IOC execution choice; see the Order Lifecycle section of `hyperliquid-design.md`.

## 2026-09-27 — Make leverage and margin mode explicit

Do not inherit asset leverage from an earlier web session. Configure the desired leverage and margin mode, validate the asset limit, and synchronize differing account state before signed trading starts. See the Leverage and Margin Mode section of `hyperliquid-design.md`.
