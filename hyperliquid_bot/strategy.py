from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from enum import Enum

ZERO = Decimal("0")


class Side(str, Enum):
    FORWARD = "forward"
    BACKWARD = "backward"


@dataclass(frozen=True)
class Candle:
    high: Decimal
    low: Decimal


@dataclass(frozen=True)
class Decision:
    is_buy: bool
    size: Decimal
    reduce_only: bool
    current_size: Decimal
    target_size: Decimal
    reason: str


@dataclass
class StrategyState:
    first_price: Decimal | None = None
    realized_pnl: Decimal = ZERO
    margin: Decimal = ZERO


def truncate_size(value: Decimal, decimals: int) -> Decimal:
    """Truncate like MQL5 af(), generalized to the asset's size precision."""
    scale = Decimal(10) ** decimals
    if value < ZERO:
        adjusted = value * scale - Decimal("0.001")
    elif value > ZERO:
        adjusted = value * scale + Decimal("0.001")
    else:
        return ZERO
    return adjusted.to_integral_value(rounding=ROUND_DOWN) / scale


def mt5_round(value: Decimal) -> Decimal:
    """Exact two-decimal MQL5 af() behavior, retained for parity tests."""
    return truncate_size(value, 2)


def cutoff(
    tap: Decimal,
    current: Decimal,
    target: Decimal,
    direction: str,
    size_decimals: int = 2,
) -> Decimal:
    """Port of conf.mqh cutoff() for the arguments used by this strategy."""
    steps = ZERO
    if target < ZERO:
        steps = (target / tap - Decimal("0.001")).to_integral_value(rounding=ROUND_DOWN)
    elif target > ZERO:
        steps = (target / tap + Decimal("0.001")).to_integral_value(rounding=ROUND_DOWN)
    level = steps * tap

    if direction == "inc":
        result = (
            truncate_size(target - current, size_decimals)
            if abs(target - level) < Decimal("0.0001")
            else level - current
        )
        if target <= ZERO and abs(target - level) >= Decimal("0.0001"):
            result = level - tap - current
    elif direction == "red":
        result = (
            truncate_size(current - target, size_decimals)
            if target == level
            else current - level - (tap if target > ZERO else ZERO)
        )
    else:
        raise ValueError("direction must be inc or red")
    return truncate_size(max(result, ZERO), size_decimals)


class PositionStrategy:
    def __init__(
        self,
        side: Side,
        tap: Decimal,
        limit_size: Decimal,
        t_guide: Decimal,
        limit_spread: Decimal,
        all_in: bool = False,
        size_decimals: int = 2,
    ) -> None:
        self.side = side
        self.tap = tap
        self.limit_size = limit_size
        self.t_guide = t_guide
        self.limit_spread = limit_spread
        self.all_in = all_in
        self.size_decimals = size_decimals
        self.state = StrategyState()

    def decide(
        self,
        signed_position: Decimal,
        bid: Decimal,
        ask: Decimal,
        candles: list[Candle],
        unrealized_pnl: Decimal = ZERO,
    ) -> Decision | None:
        if self.side is Side.FORWARD and signed_position < ZERO:
            raise RuntimeError("forward strategy found an existing short position")
        if self.side is Side.BACKWARD and signed_position > ZERO:
            raise RuntimeError("backward strategy found an existing long position")
        if len(candles) < 10 or bid <= ZERO or ask <= bid:
            return None

        current = abs(signed_position)
        # Handler_T1/T2 checks the margin calculated by the previous cycle.
        if current == ZERO and self.state.margin < ZERO:
            return None
        mid = (bid + ask) / Decimal("2")
        if self.state.first_price is None:
            self.state.first_price = mid

        self.state.margin = unrealized_pnl + self.state.realized_pnl

        if current == ZERO:
            if self.side is Side.FORWARD and mid > self.state.first_price:
                self.state.first_price = mid
            elif self.side is Side.BACKWARD and mid < self.state.first_price:
                self.state.first_price = mid

        # get_handler() replaces the MT5 handler with T_guide=0 after a
        # profitable balance. Hyperliquid one-way positions can only satisfy
        # the long/short equality condition while flat.
        if current == ZERO and self.state.realized_pnl > ZERO:
            self.state.first_price = mid
            self.state.realized_pnl = ZERO
            self.t_guide = ZERO
            return None

        high_low_range = max(abs(candle.high - candle.low) for candle in candles[-10:])
        if high_low_range == ZERO:
            return None
        move = mid - self.state.first_price
        if self.side is Side.BACKWARD:
            move = -move
        target = self.t_guide - move / high_low_range * self.tap

        # MQL5 uses: ask_1 - bid_1 < limit_spread.
        if ask - bid >= self.limit_spread:
            return None

        if current > target:
            size = truncate_size(
                min(cutoff(self.tap, current, target, "red", self.size_decimals), current),
                self.size_decimals,
            )
            is_buy = self.side is Side.BACKWARD
            reduce_only = True
            reason = "reduce"
        elif current < target:
            size = truncate_size(
                min(
                    cutoff(self.tap, current, target, "inc", self.size_decimals),
                    self.limit_size - current,
                ),
                self.size_decimals,
            )
            is_buy = self.side is Side.FORWARD
            reduce_only = False
            reason = "increase"
        else:
            return None

        # This preserves the original EA's outer _tap threshold and all_in branch.
        if size < self.tap or (self.all_in and target > ZERO):
            return None
        return Decision(is_buy, size, reduce_only, current, target, reason)
