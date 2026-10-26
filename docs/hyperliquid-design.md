# Hyperliquid Port Design

Status: implemented and signed-testnet validated, 2026-09-27.

## Components

`strategy.py` is the single source of truth for target position, step sizing, spread gating, PnL state, and direction safety. It has no network dependency. `gateway.py` owns Hyperliquid SDK calls, market metadata, position snapshots, GTC execution, and the `reduce_only` contract. `app.py` owns event ordering and reconciliation.

## Event and Recovery Protocol

The bot subscribes to `l2Book`, the configured `HL_TIMEFRAME` candle, and `1m` candle feeds. A new `1m` candle start is the only decision trigger and is deduplicated by timestamp. The queue holds only the latest pending minute so delayed processing cannot replay stale buckets. At each trigger, the worker reconciles fills and the position snapshot over REST, then evaluates against the cached book and last ten candles from the configured interval, including its current candle. This asymmetry gives the protocol a single owner (`app.py`) while market and execution components only provide data and actions.

On startup, the bot loads a book snapshot and twelve intervals of configured-timeframe candles before subscribing. Its WebSocket client sends Hyperliquid's JSON `{"method":"ping"}` application heartbeat every 50 seconds, reconnects with bounded exponential backoff, and re-subscribes after every connection. If minute events reveal a gap, the worker rebuilds the book and candle snapshots before deciding. Fill IDs are deduplicated. An opposite-side position is a fail-safe error instead of being silently reversed.

## Position, PnL, and Size Semantics

Hyperliquid exposes one signed position per asset, so the port intentionally operates on net exposure and does not reproduce MT5 ticket identity. The REST position snapshot supplies both `szi` and `unrealizedPnl`. Strategy margin is current unrealized PnL plus newly reconciled closed PnL; the flat-loss guard uses the previous evaluation's margin, matching the EA's evaluation order. A profitable flat reset clears the guide target and waits for the next minute trigger before opening again.

Order quantities are base-asset units. The gateway reads `szDecimals` from exchange metadata, and the strategy truncates increases and reductions to that precision. MT5's two-decimal helper remains relevant only to MT5-parity calculations whose inputs are not exchange order sizes.

## Leverage and Margin Mode

`HL_LEVERAGE` is a positive integer and `HL_MARGIN_MODE` is `cross` or `isolated`. During gateway initialization, exchange metadata supplies the asset's `maxLeverage`; startup fails if the configured value exceeds it. In signed mode the gateway reads `activeAssetData` for the configured account and asset. It calls `updateLeverage` only when the saved leverage or margin mode differs, and startup fails if that update is rejected. Dry-run validates the configured value against market metadata but does not change account state.

## Order Lifecycle

After the strategy produces an order decision, `app.py` asks `gateway.py` for open orders scoped to the configured account and asset. If the set is non-empty, the gateway cancels all of them in one batch and the application ends that evaluation without submitting the decision. Only a later minute event may calculate and submit a replacement. With no existing order, the gateway submits a GTC limit order at the observed best bid or ask; reductions are `reduce_only`. A marketable GTC may execute immediately, while an unfilled order remains open until the next eligible decision cancels it. Dry-run logs intended cancellations and submissions without signing them.

## Configuration and Secrets

Configuration comes from `HL_*` environment variables documented in `.env.example`. The private key is never stored in repository files. `HL_DRY_RUN=true` avoids constructing a signing client. `HL_LIMIT_SPREAD` preserves MT5's absolute-price threshold and strict comparison; users must choose a value in the configured coin's price units. Leverage is explicit rather than inherited from a previous web session.

Correction as of 2026-09-24: the earlier fixed-`5m` and basis-point assumptions are invalid. The current contract is `HL_TIMEFRAME` plus absolute `HL_LIMIT_SPREAD`; see the correction entry in `decisions.md`.

## Validation Boundary

The increase, resting GTC, cancel-then-defer, next-cycle replacement, and `reduce_only` paths were observed with signed testnet actions on 2026-09-27; see `hyperliquid-testnet-validation.md`. This validates exchange integration but does not by itself approve mainnet configuration or risk limits.
