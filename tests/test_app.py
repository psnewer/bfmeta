from decimal import Decimal
from typing import Any, Callable

from hyperliquid_bot.app import Bot
from hyperliquid_bot.config import Config
from hyperliquid_bot.gateway import PositionSnapshot


class FakeGateway:
    def __init__(self) -> None:
        self.size_decimals = 3
        self.callbacks: dict[tuple[str, str | None], Callable[[dict[str, Any]], None]] = {}
        self.orders: list[tuple[bool, Decimal, bool, Decimal]] = []
        self.pending_orders: list[dict[str, Any]] = []
        self.canceled_orders: list[int] = []

    def book(self) -> dict[str, Any]:
        return {"levels": [[{"px": "99.99"}], [{"px": "100.01"}]]}

    def candles(self, _interval: str, _start_ms: int, _end_ms: int) -> list[dict[str, Any]]:
        return [
            {"t": index * 300_000, "h": "101", "l": "99"}
            for index in range(10)
        ]

    def subscribe(
        self, subscription: dict[str, Any], callback: Callable[[dict[str, Any]], None]
    ) -> None:
        self.callbacks[(subscription["type"], subscription.get("interval"))] = callback

    def fills(self, _start_ms: int, _end_ms: int) -> list[dict[str, Any]]:
        return []

    def position(self) -> PositionSnapshot:
        return PositionSnapshot(Decimal("0"), Decimal("0"))

    def open_orders(self) -> list[dict[str, Any]]:
        return list(self.pending_orders)

    def cancel_orders(self, orders: list[dict[str, Any]]) -> dict[str, str]:
        self.canceled_orders.extend(int(order["oid"]) for order in orders)
        self.pending_orders.clear()
        return {"status": "ok"}

    def submit_gtc(
        self, is_buy: bool, size: Decimal, reduce_only: bool, reference_px: Decimal
    ) -> dict[str, str]:
        self.orders.append((is_buy, size, reduce_only, reference_px))
        return {"status": "dry-run"}

    def close(self) -> None:
        pass


def test_new_websocket_minute_triggers_one_decision() -> None:
    gateway = FakeGateway()
    config = Config(t_guide=Decimal("0.04"), limit_spread=Decimal("0.03"), timeframe="1h")
    bot = Bot(config, gateway)  # type: ignore[arg-type]
    bot.bootstrap()

    callback = gateway.callbacks[("candle", "1m")]
    assert ("candle", "1h") in gateway.callbacks
    callback({"data": {"t": 60_000}})
    assert bot.events.empty()
    callback({"data": {"t": 120_000}})
    callback({"data": {"t": 120_000}})

    event = bot.events.get_nowait()
    assert event == 120_000
    assert bot.events.empty()
    bot.evaluate(event)
    assert gateway.orders == [(True, Decimal("0.04"), False, Decimal("100.01"))]


def test_only_latest_pending_minute_is_kept() -> None:
    gateway = FakeGateway()
    bot = Bot(Config(), gateway)  # type: ignore[arg-type]
    bot._on_1m({"data": {"t": 60_000}})
    bot._on_1m({"data": {"t": 120_000}})
    bot._on_1m({"data": {"t": 180_000}})
    assert bot.events.get_nowait() == 180_000
    assert bot.events.empty()


def test_existing_orders_are_canceled_and_new_order_waits_for_next_cycle() -> None:
    gateway = FakeGateway()
    gateway.pending_orders = [{"coin": "BTC", "oid": 101}]
    config = Config(t_guide=Decimal("0.04"), limit_spread=Decimal("0.03"))
    bot = Bot(config, gateway)  # type: ignore[arg-type]
    bot._reload_market_snapshots()

    bot.evaluate(120_000)
    assert gateway.canceled_orders == [101]
    assert gateway.orders == []

    bot.evaluate(180_000)
    assert gateway.orders == [(True, Decimal("0.04"), False, Decimal("100.01"))]
