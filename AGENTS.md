# Repository Guidelines

## Project Structure & Module Organization

The original MetaTrader 5 Expert Advisor lives under `metatrader5/`. Its entry point is `metatrader5/Experts/bfmeta/bfmeta.mq5`; shared configuration and handlers are in `metatrader5/Include/`. The Hyperliquid port lives in `hyperliquid_bot/`, with tests in `tests/` and migration design notes in `docs/`. Keep platform-specific code inside its platform directory.

## Build, Test, and Development Commands

No command-line build scripts or dependency manager are checked in. Develop and compile with MetaEditor/MetaTrader 5:

- Open `metatrader5/Experts/bfmeta/bfmeta.mq5` in MetaEditor.
- Press **F7** to compile and inspect all compiler warnings and errors.
- Run the compiled Expert Advisor in MT5 Strategy Tester, selecting a symbol, timeframe, date range, and suitable input parameters.

Copy `metatrader5/Experts/` and `metatrader5/Include/` into the corresponding `MQL5` data-directory paths so angle-bracket includes resolve correctly.

## Coding Style & Naming Conventions

Match the surrounding MQL5 style and avoid unrelated formatting changes. Use platform-standard PascalCase names for event APIs (`OnTimer`, `HistorySelect`), descriptive `snake_case` for local and global variables, and the established `Handler_T1`/`Handler_T2` pattern for strategy classes and files. Keep braces and indentation consistent with the file being edited. Several existing MQL5 files use UTF-16 encoding; preserve each file's encoding and line endings when editing it.

## Testing Guidelines

There is currently no automated test directory or coverage target. Every change must compile cleanly and be exercised in Strategy Tester. Test both `current_side` modes, boundary values for `_tap`, `limit_size`, and `limit_spread`, and scenarios with no positions, open positions, and completed deals. Review the Strategy Tester journal for the specific branch or handler changed; a successful run alone does not prove that path executed. Use a demo account before any live-account validation.

## Commit & Pull Request Guidelines

Existing history uses short free-form subjects and establishes no reliable convention. Prefer concise, imperative messages such as `Fix T2 cutoff calculation`. Keep commits focused. Pull requests should explain the trading behavior changed, affected inputs and side, compile/test results, and tester settings. Link relevant issues and attach journal excerpts or screenshots when behavior is visible only in MT5.
