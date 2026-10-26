from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Any, Callable

import websocket
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants

from .config import Config

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PositionSnapshot:
    signed_size: Decimal
    unrealized_pnl: Decimal


def _max_leverage(meta: dict[str, Any], coin: str) -> int:
    for asset in meta["universe"]:
        if asset["name"] == coin:
            return int(asset["maxLeverage"])
    raise ValueError(f"unknown perpetual coin: {coin}")


def _matches(subscription: dict[str, Any], message: dict[str, Any]) -> bool:
    channel = message.get("channel")
    data = message.get("data", {})
    if subscription["type"] == "l2Book":
        return channel == "l2Book" and data.get("coin") == subscription["coin"]
    if subscription["type"] == "candle":
        return (
            channel == "candle"
            and data.get("s") == subscription["coin"]
            and data.get("i") == subscription["interval"]
        )
    return False


class MarketStream:
    """Small reconnecting stream for the market-data channels used by the bot."""

    def __init__(self, base_url: str) -> None:
        self.url = "ws" + base_url[len("http") :] + "/ws"
        self.subscriptions: list[tuple[dict[str, Any], Callable[[dict[str, Any]], None]]] = []
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.ready = False
        self.ws: websocket.WebSocketApp | None = None
        self.thread = threading.Thread(target=self._run, name="hyperliquid-ws", daemon=True)
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name="hyperliquid-ws-heartbeat",
            daemon=True,
        )
        self.thread.start()
        self.heartbeat_thread.start()

    def subscribe(
        self, subscription: dict[str, Any], callback: Callable[[dict[str, Any]], None]
    ) -> None:
        with self.lock:
            already_subscribed = any(item[0] == subscription for item in self.subscriptions)
            self.subscriptions.append((subscription, callback))
            ws = self.ws if self.ready and not already_subscribed else None
        if ws is not None:
            ws.send(json.dumps({"method": "subscribe", "subscription": subscription}))

    def _run(self) -> None:
        backoff = 1
        while not self.stop_event.is_set():
            opened = threading.Event()
            self.ws = websocket.WebSocketApp(
                self.url,
                on_open=lambda ws: (opened.set(), self._on_open(ws)),
                on_message=self._on_message,
                on_error=lambda _ws, error: LOGGER.warning("WebSocket error: %s", error),
                on_close=lambda _ws, code, reason: LOGGER.warning(
                    "WebSocket closed code=%s reason=%s", code, reason
                ),
            )
            self.ws.run_forever()
            self.ready = False
            if opened.is_set():
                backoff = 1
            if self.stop_event.is_set():
                break
            LOGGER.warning("WebSocket reconnecting in %ss", backoff)
            if self.stop_event.wait(backoff):
                break
            backoff = min(backoff * 2, 30)

    def _heartbeat_loop(self) -> None:
        while not self.stop_event.wait(50):
            self._send_heartbeat()

    def _send_heartbeat(self) -> None:
        with self.lock:
            ws = self.ws if self.ready else None
        if ws is None:
            return
        try:
            ws.send(json.dumps({"method": "ping"}))
        except Exception:
            LOGGER.exception("WebSocket heartbeat failed")

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        LOGGER.info("WebSocket connected")
        self.ready = True
        with self.lock:
            subscriptions: list[dict[str, Any]] = []
            for subscription, _callback in self.subscriptions:
                if subscription not in subscriptions:
                    subscriptions.append(subscription)
        for subscription in subscriptions:
            ws.send(json.dumps({"method": "subscribe", "subscription": subscription}))

    def _on_message(self, _ws: websocket.WebSocketApp, raw: str) -> None:
        if raw == "Websocket connection established.":
            return
        message = json.loads(raw)
        if message.get("channel") in {"pong", "subscriptionResponse"}:
            return
        with self.lock:
            subscriptions = list(self.subscriptions)
        for subscription, callback in subscriptions:
            if _matches(subscription, message):
                try:
                    callback(message)
                except Exception:
                    LOGGER.exception("WebSocket callback failed for %s", subscription)

    def close(self) -> None:
        self.stop_event.set()
        if self.ws is not None:
            self.ws.close()
        self.thread.join(timeout=5)
        self.heartbeat_thread.join(timeout=5)


class HyperliquidGateway:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.base_url = (
            constants.TESTNET_API_URL if config.network == "testnet" else constants.MAINNET_API_URL
        )
        self.info = Info(self.base_url, skip_ws=True, timeout=30)
        self.max_leverage = _max_leverage(self.info.meta(), config.coin)
        if config.leverage > self.max_leverage:
            raise ValueError(
                f"HL_LEVERAGE={config.leverage} exceeds {config.coin} max leverage "
                f"{self.max_leverage}"
            )
        self.exchange: Exchange | None = None
        if not config.dry_run:
            import eth_account

            wallet = eth_account.Account.from_key(config.secret_key)
            self.exchange = Exchange(
                wallet,
                self.base_url,
                account_address=config.account_address,
                timeout=30,
            )
            self._ensure_leverage()

        asset = self.info.name_to_asset(config.coin)
        self.size_decimals = self.info.asset_to_sz_decimals[asset]
        self.stream = MarketStream(self.base_url)

    def leverage_setting(self) -> dict[str, Any] | None:
        if not self.config.account_address:
            return None
        data = self.info.post(
            "/info",
            {
                "type": "activeAssetData",
                "user": self.config.account_address,
                "coin": self.config.coin,
            },
        )
        return data["leverage"]

    def _ensure_leverage(self) -> None:
        current = self.leverage_setting()
        if current is not None and (
            current["type"] == self.config.margin_mode
            and int(current["value"]) == self.config.leverage
        ):
            LOGGER.info(
                "leverage already configured coin=%s mode=%s leverage=%sx",
                self.config.coin,
                self.config.margin_mode,
                self.config.leverage,
            )
            return
        assert self.exchange is not None
        result = self.exchange.update_leverage(
            self.config.leverage,
            self.config.coin,
            is_cross=self.config.margin_mode == "cross",
        )
        if result.get("status") != "ok":
            raise RuntimeError(f"failed to update leverage: {result}")
        LOGGER.info(
            "updated leverage coin=%s mode=%s leverage=%sx",
            self.config.coin,
            self.config.margin_mode,
            self.config.leverage,
        )

    def position(self) -> PositionSnapshot:
        if not self.config.account_address:
            return PositionSnapshot(Decimal("0"), Decimal("0"))
        state = self.info.user_state(self.config.account_address)
        for wrapped in state["assetPositions"]:
            position = wrapped["position"]
            if position["coin"] == self.config.coin:
                return PositionSnapshot(
                    Decimal(position["szi"]),
                    Decimal(position["unrealizedPnl"]),
                )
        return PositionSnapshot(Decimal("0"), Decimal("0"))

    def candles(self, interval: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
        return self.info.candles_snapshot(self.config.coin, interval, start_ms, end_ms)

    def book(self) -> dict[str, Any]:
        return self.info.l2_snapshot(self.config.coin)

    def fills(self, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
        if not self.config.account_address:
            return []
        return self.info.user_fills_by_time(self.config.account_address, start_ms, end_ms, True)

    def open_orders(self) -> list[dict[str, Any]]:
        if not self.config.account_address:
            return []
        return [
            order
            for order in self.info.open_orders(self.config.account_address)
            if order["coin"] == self.config.coin
        ]

    def cancel_orders(self, orders: list[dict[str, Any]]) -> Any:
        requests = [{"coin": self.config.coin, "oid": int(order["oid"])} for order in orders]
        if not requests:
            return None
        if self.config.dry_run:
            LOGGER.warning(
                "DRY RUN cancel orders coin=%s oids=%s",
                self.config.coin,
                [request["oid"] for request in requests],
            )
            return {"status": "dry-run"}
        assert self.exchange is not None
        return self.exchange.bulk_cancel(requests)

    def subscribe(self, subscription: dict[str, Any], callback: Callable[[dict[str, Any]], None]) -> None:
        self.stream.subscribe(subscription, callback)

    def normalize_size(self, size: Decimal) -> Decimal:
        quantum = Decimal(1).scaleb(-self.size_decimals)
        return size.quantize(quantum, rounding=ROUND_DOWN)

    def submit_gtc(self, is_buy: bool, size: Decimal, reduce_only: bool, reference_px: Decimal) -> Any:
        normalized = self.normalize_size(size)
        if normalized <= 0:
            raise ValueError("order size rounds to zero at the market's size precision")
        if self.config.dry_run:
            LOGGER.warning(
                "DRY RUN GTC order coin=%s is_buy=%s size=%s reduce_only=%s reference_px=%s",
                self.config.coin,
                is_buy,
                normalized,
                reduce_only,
                reference_px,
            )
            return {"status": "dry-run"}
        assert self.exchange is not None
        return self.exchange.order(
            self.config.coin,
            is_buy,
            float(normalized),
            float(reference_px),
            {"limit": {"tif": "Gtc"}},
            reduce_only=reduce_only,
        )

    def close(self) -> None:
        self.stream.close()
