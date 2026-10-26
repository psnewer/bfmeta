from decimal import Decimal

import pytest

from hyperliquid_bot.strategy import (
    Candle,
    PositionStrategy,
    Side,
    cutoff,
    mt5_round,
    truncate_size,
)

D = Decimal


def candles() -> list[Candle]:
    return [Candle(D("101"), D("99")) for _ in range(10)]


def strategy(side: Side = Side.FORWARD) -> PositionStrategy:
    return PositionStrategy(side, D("0.02"), D("0.08"), D("0.04"), D("0.03"))


@pytest.mark.parametrize(
    ("value", "expected"),
    [("1.239", "1.23"), ("-1.239", "-1.23"), ("0", "0")],
)
def test_mt5_round(value: str, expected: str) -> None:
    assert mt5_round(D(value)) == D(expected)


def test_cutoff_increase_and_reduce() -> None:
    assert cutoff(D("0.02"), D("0.02"), D("0.06"), "inc") == D("0.04")
    assert cutoff(D("0.02"), D("0.06"), D("0.02"), "red") == D("0.04")


def test_cutoff_negative_target_matches_mql5_truncation() -> None:
    assert cutoff(D("0.02"), D("0.08"), D("-0.03"), "red") == D("0.10")


def test_size_truncation_uses_asset_precision() -> None:
    assert truncate_size(D("0.0049"), 3) == D("0.004")
    assert truncate_size(D("-0.0049"), 3) == D("-0.004")


def test_forward_increases_long_position() -> None:
    bot = strategy()
    bot.state.first_price = D("100")
    decision = bot.decide(D("0"), D("99.99"), D("100.01"), candles())
    assert decision is not None
    assert decision.is_buy is True
    assert decision.reduce_only is False
    assert decision.size == D("0.04")


def test_forward_increases_existing_long_position() -> None:
    bot = PositionStrategy(Side.FORWARD, D("0.02"), D("0.08"), D("0.06"), D("0.03"))
    bot.state.first_price = D("100")
    decision = bot.decide(D("0.02"), D("99.99"), D("100.01"), candles())
    assert decision is not None
    assert decision.is_buy is True
    assert decision.reduce_only is False
    assert decision.current_size == D("0.02")
    assert decision.target_size == D("0.06")
    assert decision.size == D("0.04")


def test_forward_reduction_is_reduce_only() -> None:
    bot = strategy()
    bot.state.first_price = D("100")
    decision = bot.decide(D("0.08"), D("99.99"), D("100.01"), candles())
    assert decision is not None
    assert decision.is_buy is False
    assert decision.reduce_only is True
    assert decision.size == D("0.04")


def test_backward_rejects_external_long_position() -> None:
    bot = strategy(Side.BACKWARD)
    with pytest.raises(RuntimeError, match="existing long"):
        bot.decide(D("0.01"), D("99.99"), D("100.01"), candles())


def test_backward_increases_short_position() -> None:
    bot = strategy(Side.BACKWARD)
    bot.state.first_price = D("100")
    decision = bot.decide(D("-0.02"), D("99.99"), D("100.01"), candles())
    assert decision is not None
    assert decision.is_buy is False
    assert decision.reduce_only is False
    assert decision.size == D("0.02")


def test_backward_reduction_is_reduce_only_buy() -> None:
    bot = strategy(Side.BACKWARD)
    bot.state.first_price = D("100")
    decision = bot.decide(D("-0.08"), D("99.99"), D("100.01"), candles())
    assert decision is not None
    assert decision.is_buy is True
    assert decision.reduce_only is True
    assert decision.size == D("0.04")


@pytest.mark.parametrize(("side", "position"), [(Side.FORWARD, "0.02"), (Side.BACKWARD, "-0.02")])
def test_zero_target_reduces_position_to_zero(side: Side, position: str) -> None:
    bot = PositionStrategy(side, D("0.02"), D("0.08"), D("0"), D("0.03"))
    bot.state.first_price = D("100")
    decision = bot.decide(D(position), D("99.99"), D("100.01"), candles())
    assert decision is not None
    assert decision.reduce_only is True
    assert decision.size == D("0.02")


def test_increase_is_capped_at_position_limit() -> None:
    bot = PositionStrategy(Side.FORWARD, D("0.01"), D("0.08"), D("0.10"), D("0.03"))
    bot.state.first_price = D("100")
    decision = bot.decide(D("0.07"), D("99.99"), D("100.01"), candles())
    assert decision is not None
    assert decision.size == D("0.01")


def test_all_in_blocks_positive_target_but_allows_full_reduction() -> None:
    bot = PositionStrategy(
        Side.FORWARD,
        D("0.02"),
        D("0.08"),
        D("0.04"),
        D("0.03"),
        all_in=True,
    )
    bot.state.first_price = D("100")
    assert bot.decide(D("0"), D("99.99"), D("100.01"), candles()) is None

    bot.t_guide = D("0")
    decision = bot.decide(D("0.08"), D("101.99"), D("102.01"), candles())
    assert decision is not None
    assert decision.reduce_only is True
    assert decision.size == D("0.08")


def test_fewer_than_ten_candles_blocks_decision() -> None:
    bot = strategy()
    assert bot.decide(D("0"), D("99.99"), D("100.01"), candles()[:9]) is None


def test_wide_spread_blocks_order() -> None:
    bot = strategy()
    bot.state.first_price = D("100")
    assert bot.decide(D("0"), D("99"), D("101"), candles()) is None


def test_spread_must_be_strictly_less_than_absolute_limit() -> None:
    bot = PositionStrategy(Side.FORWARD, D("0.02"), D("0.08"), D("0.04"), D("0.02"))
    bot.state.first_price = D("100")
    assert bot.decide(D("0"), D("99.99"), D("100.01"), candles()) is None


def test_realized_loss_blocks_reentry_while_flat() -> None:
    bot = strategy()
    bot.state.margin = D("-1")
    assert bot.decide(D("0"), D("99.99"), D("100.01"), candles()) is None


def test_unrealized_pnl_is_carried_into_next_cycle_margin_check() -> None:
    bot = strategy()
    bot.state.first_price = D("100")
    bot.decide(
        D("0.02"),
        D("99.99"),
        D("100.01"),
        candles(),
        unrealized_pnl=D("-1"),
    )
    assert bot.state.margin == D("-1")
    assert bot.decide(D("0"), D("99.99"), D("100.01"), candles()) is None


def test_profitable_flat_balance_resets_guide_without_reopening() -> None:
    bot = strategy()
    bot.state.first_price = D("90")
    bot.state.realized_pnl = D("1")
    assert bot.decide(D("0"), D("99.99"), D("100.01"), candles()) is None
    assert bot.t_guide == D("0")
    assert bot.state.first_price == D("100")
    assert bot.state.realized_pnl == D("0")


def test_sub_cent_base_size_uses_market_precision() -> None:
    bot = PositionStrategy(
        Side.FORWARD,
        D("0.002"),
        D("0.008"),
        D("0.004"),
        D("0.03"),
        size_decimals=3,
    )
    bot.state.first_price = D("100")
    decision = bot.decide(D("0"), D("99.99"), D("100.01"), candles())
    assert decision is not None
    assert decision.size == D("0.004")
