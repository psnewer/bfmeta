# Hyperliquid Port Requirements

Status: implemented and signed-testnet validated, 2026-09-27.

- Preserve the MT5 forward (long) and backward (short) target-position formulas and `_tap` step threshold.
- Use Hyperliquid perpetuals through the official Python SDK.
- Default to testnet and dry-run; live trading requires an explicit switch and credentials.
- Drive strategy decisions from a new one-minute WebSocket candle bucket. Book and configured analysis-timeframe candle updates only refresh state and must not directly submit orders.
- Expose the analysis timeframe as `HL_TIMEFRAME`, corresponding to the MQL5 `ENUM_TIMEFRAMES M5` input. Use the latest ten candles from that interval, including the current candle.
- Preserve `limit_spread` as an absolute price difference with the strict condition `ask - bid < limit_spread`.
- Treat each asset as one signed net position, matching Hyperliquid's one-way position model. Do not emulate MT5 tickets or virtual sub-positions.
- Configure leverage and `cross` or `isolated` margin mode explicitly per asset. Reject leverage above the asset's exchange-provided maximum.
- Truncate every submitted size to the asset's `szDecimals`; do not apply MT5's fixed two-decimal lot rounding.
- Preserve the MT5 margin signal as realized PnL plus current unrealized PnL, including its previous-cycle check when the position is flat.
- Use GTC limit orders at the observed best bid or ask. Every reduction must set `reduce_only`; increases must respect the configured position limit.
- Before submitting an intended order, query open orders for the configured asset. If any exist, cancel them and end the current evaluation; a new order may only be reconsidered on the next minute event.
- Recover market, position, and fill state from REST snapshots after startup or reconnect.
- Keep only the newest pending minute event and send Hyperliquid's application-level `{"method":"ping"}` heartbeat while connected.

Acceptance is defined by the tests in `tests/` plus a testnet run that logs the specific decision and resulting order status. The current evidence is recorded in `hyperliquid-testnet-validation.md`.
