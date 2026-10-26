import json
import threading
from decimal import Decimal

import pytest

from hyperliquid_bot.config import Config
from hyperliquid_bot.gateway import (
    HyperliquidGateway,
    MarketStream,
    PositionSnapshot,
    _matches,
    _max_leverage,
)


class FakeExchange:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def order(self, *args: object, **kwargs: object) -> dict[str, str]:
        self.calls.append(("order", args, kwargs))
        return {"status": "ok"}

    def bulk_cancel(self, requests: object) -> dict[str, str]:
        self.calls.append(("cancel", (requests,), {}))
        return {"status": "ok"}

    def update_leverage(self, *args: object, **kwargs: object) -> dict[str, str]:
        self.calls.append(("leverage", args, kwargs))
        return {"status": "ok"}


class FakeWebSocket:
    def __init__(self) -> None:
        self.messages: list[dict[str, object]] = []

    def send(self, raw: str) -> None:
        self.messages.append(json.loads(raw))

def test_l2_subscription_routing() -> None:
    subscription = {"type": "l2Book", "coin": "BTC"}
    assert _matches(subscription, {"channel": "l2Book", "data": {"coin": "BTC"}})
    assert not _matches(subscription, {"channel": "l2Book", "data": {"coin": "ETH"}})


def test_candle_subscription_routing_includes_interval() -> None:
    subscription = {"type": "candle", "coin": "BTC", "interval": "1m"}
    assert _matches(
        subscription,
        {"channel": "candle", "data": {"s": "BTC", "i": "1m"}},
    )
    assert not _matches(
        subscription,
        {"channel": "candle", "data": {"s": "BTC", "i": "5m"}},
    )


def test_identical_wire_subscription_is_multiplexed_locally() -> None:
    stream = object.__new__(MarketStream)
    stream.subscriptions = []
    stream.lock = threading.Lock()
    stream.ready = True
    stream.ws = FakeWebSocket()  # type: ignore[assignment]
    calls: list[str] = []
    subscription = {"type": "candle", "coin": "BTC", "interval": "1m"}

    stream.subscribe(subscription, lambda _message: calls.append("analysis"))
    stream.subscribe(subscription, lambda _message: calls.append("clock"))

    assert len(stream.ws.messages) == 1  # type: ignore[union-attr]
    stream._on_message(
        stream.ws,  # type: ignore[arg-type]
        json.dumps({"channel": "candle", "data": {"s": "BTC", "i": "1m"}}),
    )
    assert calls == ["analysis", "clock"]


def test_official_application_heartbeat_payload() -> None:
    stream = object.__new__(MarketStream)
    stream.lock = threading.Lock()
    stream.ready = True
    stream.ws = FakeWebSocket()  # type: ignore[assignment]
    stream._send_heartbeat()
    assert stream.ws.messages == [{"method": "ping"}]  # type: ignore[union-attr]


def test_position_reads_signed_size_and_unrealized_pnl() -> None:
    gateway = object.__new__(HyperliquidGateway)
    gateway.config = Config(account_address="0x1")

    class FakeInfo:
        @staticmethod
        def user_state(_address: str) -> dict[str, object]:
            return {
                "assetPositions": [
                    {"position": {"coin": "BTC", "szi": "-0.25", "unrealizedPnl": "1.5"}}
                ]
            }

    gateway.info = FakeInfo()  # type: ignore[assignment]
    assert gateway.position() == PositionSnapshot(Decimal("-0.25"), Decimal("1.5"))


def test_market_max_leverage_comes_from_perpetual_metadata() -> None:
    meta = {"universe": [{"name": "BTC", "maxLeverage": 40}]}
    assert _max_leverage(meta, "BTC") == 40

    with pytest.raises(ValueError, match="unknown perpetual"):
        _max_leverage(meta, "ETH")


def test_matching_leverage_setting_does_not_submit_update() -> None:
    gateway, exchange = live_gateway()
    gateway.config = Config(
        dry_run=False,
        account_address="0x1",
        secret_key="0x2",
        leverage=20,
        margin_mode="cross",
    )
    gateway.leverage_setting = lambda: {"type": "cross", "value": 20}  # type: ignore[method-assign]
    gateway._ensure_leverage()
    assert exchange.calls == []


def test_different_leverage_setting_is_updated() -> None:
    gateway, exchange = live_gateway()
    gateway.config = Config(
        dry_run=False,
        account_address="0x1",
        secret_key="0x2",
        leverage=3,
        margin_mode="isolated",
    )
    gateway.leverage_setting = lambda: {"type": "cross", "value": 20}  # type: ignore[method-assign]
    gateway._ensure_leverage()
    assert exchange.calls == [("leverage", (3, "BTC"), {"is_cross": False})]


def test_open_orders_are_scoped_to_configured_coin() -> None:
    gateway = object.__new__(HyperliquidGateway)
    gateway.config = Config(account_address="0x1")

    class FakeInfo:
        @staticmethod
        def open_orders(_address: str) -> list[dict[str, object]]:
            return [{"coin": "BTC", "oid": 1}, {"coin": "ETH", "oid": 2}]

    gateway.info = FakeInfo()  # type: ignore[assignment]
    assert gateway.open_orders() == [{"coin": "BTC", "oid": 1}]


def live_gateway() -> tuple[HyperliquidGateway, FakeExchange]:
    gateway = object.__new__(HyperliquidGateway)
    gateway.config = Config(dry_run=False, account_address="0x1", secret_key="0x2")
    gateway.size_decimals = 3
    exchange = FakeExchange()
    gateway.exchange = exchange  # type: ignore[assignment]
    return gateway, exchange


def test_increase_submits_gtc_order() -> None:
    gateway, exchange = live_gateway()
    gateway.submit_gtc(True, Decimal("0.0129"), False, Decimal("100"))
    assert exchange.calls == [
        (
            "order",
            ("BTC", True, 0.012, 100.0, {"limit": {"tif": "Gtc"}}),
            {"reduce_only": False},
        )
    ]


def test_reduction_submits_reduce_only_gtc_order() -> None:
    gateway, exchange = live_gateway()
    gateway.submit_gtc(False, Decimal("0.0129"), True, Decimal("100"))
    assert exchange.calls == [
        (
            "order",
            ("BTC", False, 0.012, 100.0, {"limit": {"tif": "Gtc"}}),
            {"reduce_only": True},
        )
    ]


def test_cancel_orders_uses_one_bulk_request() -> None:
    gateway, exchange = live_gateway()
    gateway.cancel_orders([{"coin": "BTC", "oid": 11}, {"coin": "BTC", "oid": 12}])
    assert exchange.calls == [
        ("cancel", ([{"coin": "BTC", "oid": 11}, {"coin": "BTC", "oid": 12}],), {})
    ]
