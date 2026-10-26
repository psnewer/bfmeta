# Hyperliquid Testnet Validation

Status: core paths passed; partial-fill recovery gap identified, 2026-09-27.

The signed test used BTC with a `0.0002` base-asset size and an authorized API wallet. Secrets and full account addresses were not recorded.

## Verified Paths

- A GTC buy at `84660.0` entered the book as resting order `61175619782`.
- With that order open, a real `Bot.evaluate()` call canceled it successfully and submitted no replacement during the same evaluation.
- The next evaluation submitted one GTC buy at the observed ask. Order `61175622125` filled `0.0002 BTC` at an average price of `84911.0`.
- A `reduce_only` GTC sell, order `61175622862`, filled the full `0.0002 BTC` at an average price of `84912.0`.
- Final reconciliation reported zero BTC position and zero BTC open orders.

## Bidirectional Strategy Ladder

A second signed run used decisions produced by `PositionStrategy` and valid deeper book prices to isolate sizing and direction from top-of-book liquidity. Each `0.0002 BTC` step filled completely:

- Forward: `0 → 0.0002 → 0.0004 → 0.0002 → 0`.
- Backward: `0 → -0.0002 → -0.0004 → -0.0002 → 0`.
- Both reductions and both final closes were submitted with `reduce_only=true`.
- Final reconciliation again reported zero BTC position and zero BTC open orders.

## Partial-Fill Finding

At the production best ask, a forward increase from `0.0002` toward `0.0004` filled only `0.0001`, leaving a `0.0003` position. After the resting remainder was canceled, the strategy declined to submit the remaining `0.0001` because it is below `HL_TAP=0.0002`. Cleanup closed the full position and left no open orders. This is a known recovery gap, not a passing case.

The current unit suite passes all 42 tests. A preliminary deliberately off-book price was rejected for invalid tick size without creating an order or position; successful runs used prices read directly from the live testnet book.
