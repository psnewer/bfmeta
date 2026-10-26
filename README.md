# bfmeta for Hyperliquid

This repository keeps the original MetaTrader 5 Expert Advisor and adds an event-driven Hyperliquid perpetuals port.

## Layout

- `metatrader5/Experts/` and `metatrader5/Include/`: original MQL5 implementation. Copy these two directories into the matching locations under the MetaTrader `MQL5` data directory.
- `hyperliquid_bot/`: Python Hyperliquid implementation.
- `tests/`: Hyperliquid unit and integration-path tests.
- `docs/`: migration requirements, design, and decisions.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
cp .env.example .env
```

Edit `.env`, then export it and start the bot:

```bash
set -a
source .env
set +a
.venv/bin/bfmeta-hl
```

The defaults connect to testnet in dry-run mode. The strategy reacts only when the Hyperliquid `1m` candle stream enters a new bucket, retaining only the newest pending bucket if processing falls behind. Order-book and configured `HL_TIMEFRAME` candle messages update cached inputs but do not directly trigger orders. `HL_LIMIT_SPREAD` is an absolute price difference, matching MT5's `ask - bid < limit_spread` check. The WebSocket stays alive with Hyperliquid's official JSON application heartbeat.

## Safety

`HL_TAP` and `HL_LIMIT_SIZE` are Hyperliquid base-asset quantities, not MT5 lots. For example, `0.02` on `BTC` means `0.02 BTC`; submitted quantities are truncated to that asset's exchange-provided `szDecimals`. Choose values from the intended notional and leverage before disabling dry-run. Use the main wallet address for `HL_ACCOUNT_ADDRESS` and an authorized API wallet key for `HL_SECRET_KEY`. Never commit `.env`.

Set `HL_LEVERAGE` to an integer supported by the asset and choose `HL_MARGIN_MODE=cross` or `isolated`. Signed startup synchronizes those settings with the account; dry-run only validates the asset's maximum leverage.

The port uses Hyperliquid's single signed net position per asset rather than emulating MT5 tickets. Each evaluation combines the position's `unrealizedPnl` with newly reconciled closed PnL for the strategy margin signal.

Keep `HL_DRY_RUN=true` until logs show the expected `increase` and `reduce` decisions. Then validate GTC placement, cancellation, and the `reduce_only` path on testnet. Mainnet should only be selected after that evidence is reviewed.

The signed testnet order lifecycle was validated on 2026-09-27; see `docs/hyperliquid-testnet-validation.md`. Testnet evidence does not determine suitable mainnet position sizes or spread limits.

GTC limit orders use the observed best bid or ask. Because this may be a marketable price, GTC does not guarantee maker execution: it can fill immediately or remain resting when the market moves.

When a decision finds existing orders for the configured asset, the bot cancels them and ends that evaluation. It waits for the next `1m` event to recalculate rather than placing a replacement immediately. In dry-run mode, cancellation is logged but not signed.

## Tests

```bash
.venv/bin/pytest -q
```

The tests cover configuration guards, exact MQL5 cutoff parity, asset-specific size precision, position/PnL handling, long/short safety, spread gating, latest-event routing, and the application heartbeat. See `docs/hyperliquid-requirements.md`, `docs/hyperliquid-design.md`, and `docs/decisions.md` for the migration contract and rationale.
