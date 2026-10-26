from __future__ import annotations

import logging
import queue
import signal
import threading
import time
from decimal import Decimal
from typing import Any

from .config import Config
from .gateway import HyperliquidGateway
from .strategy import Candle, PositionStrategy, Side

LOGGER = logging.getLogger(__name__)
FIVE_MINUTES_MS = 5 * 60 * 1000
TIMEFRAME_MS = {
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "2h": 7_200_000,
    "4h": 14_400_000,
    "8h": 28_800_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
    "3d": 259_200_000,
    "1w": 604_800_000,
    "1M": 2_678_400_000,
}


class Bot:
    def __init__(self, config: Config, gateway: HyperliquidGateway | None = None) -> None:
        self.config = config
        self.gateway = gateway or HyperliquidGateway(config)
        self.strategy = PositionStrategy(
            Side(config.side),
            config.tap,
            config.limit_size,
            config.t_guide,
            config.limit_spread,
            config.all_in,
            size_decimals=self.gateway.size_decimals,
        )
        self.bid: Decimal | None = None
        self.ask: Decimal | None = None
        self.candles: dict[int, Candle] = {}
        self.last_minute: int | None = None
        self.last_evaluated_minute: int | None = None
        self.fill_cursor_ms = int(time.time() * 1000) - FIVE_MINUTES_MS
        self.seen_fills: set[tuple[str, int, int]] = set()
        self.market_lock = threading.Lock()
        self.events: queue.Queue[int | None] = queue.Queue(maxsize=1)
        self.stop_event = threading.Event()

    def bootstrap(self) -> None:
        self._reload_market_snapshots()
        self.gateway.subscribe({"type": "l2Book", "coin": self.config.coin}, self._on_book)
        self.gateway.subscribe(
            {"type": "candle", "coin": self.config.coin, "interval": self.config.timeframe},
            self._on_timeframe,
        )
        self.gateway.subscribe(
            {"type": "candle", "coin": self.config.coin, "interval": "1m"}, self._on_1m
        )
        LOGGER.info(
            "started network=%s coin=%s side=%s dry_run=%s",
            self.config.network,
            self.config.coin,
            self.config.side,
            self.config.dry_run,
        )

    def _reload_market_snapshots(self) -> None:
        now = int(time.time() * 1000)
        self._update_book(self.gateway.book())
        start_ms = now - TIMEFRAME_MS[self.config.timeframe] * 12
        snapshots = self.gateway.candles(self.config.timeframe, start_ms, now)
        with self.market_lock:
            self.candles.clear()
        for raw in snapshots:
            self._store_candle(raw)

    def _on_book(self, message: dict[str, Any]) -> None:
        self._update_book(message["data"])

    def _update_book(self, data: dict[str, Any]) -> None:
        levels = data["levels"]
        if levels[0] and levels[1]:
            with self.market_lock:
                self.bid = Decimal(levels[0][0]["px"])
                self.ask = Decimal(levels[1][0]["px"])

    def _on_timeframe(self, message: dict[str, Any]) -> None:
        data = message["data"]
        for candle in data if isinstance(data, list) else [data]:
            self._store_candle(candle)

    def _store_candle(self, raw: dict[str, Any]) -> None:
        with self.market_lock:
            self.candles[int(raw["t"])] = Candle(Decimal(raw["h"]), Decimal(raw["l"]))
            while len(self.candles) > 12:
                del self.candles[min(self.candles)]

    def _on_1m(self, message: dict[str, Any]) -> None:
        data = message["data"]
        if isinstance(data, list):
            if not data:
                return
            data = data[-1]
        minute = int(data["t"])
        if self.last_minute is None:
            self.last_minute = minute
        elif minute > self.last_minute:
            self.last_minute = minute
            self._replace_event(minute)

    def _replace_event(self, event: int | None) -> None:
        try:
            self.events.get_nowait()
        except queue.Empty:
            pass
        self.events.put_nowait(event)

    def _reconcile_fills(self, now_ms: int) -> None:
        for fill in self.gateway.fills(self.fill_cursor_ms, now_ms):
            if fill["coin"] != self.config.coin:
                continue
            key = (fill["hash"], int(fill["oid"]), int(fill["time"]))
            if key in self.seen_fills:
                continue
            self.seen_fills.add(key)
            self.strategy.state.realized_pnl += Decimal(fill["closedPnl"])
        # Keep a small overlap because multiple fills can share a millisecond.
        # seen_fills makes this idempotent.
        self.fill_cursor_ms = max(self.fill_cursor_ms, now_ms - 1000)

    def evaluate(self, event_ms: int) -> None:
        if (
            self.last_evaluated_minute is not None
            and event_ms - self.last_evaluated_minute > 60 * 1000
        ):
            LOGGER.warning("market-data gap detected; rebuilding REST snapshots")
            self._reload_market_snapshots()
        self.last_evaluated_minute = event_ms
        with self.market_lock:
            bid = self.bid
            ask = self.ask
            candles = [self.candles[key] for key in sorted(self.candles)][-10:]
        if bid is None or ask is None:
            LOGGER.warning("skipping decision: no order book snapshot")
            return
        now_ms = int(time.time() * 1000)
        self._reconcile_fills(now_ms)
        position = self.gateway.position()
        decision = self.strategy.decide(
            position.signed_size,
            bid,
            ask,
            candles,
            unrealized_pnl=position.unrealized_pnl,
        )
        if decision is None:
            LOGGER.info(
                "no action event_ms=%s position=%s unrealized_pnl=%s margin=%s",
                event_ms,
                position.signed_size,
                position.unrealized_pnl,
                self.strategy.state.margin,
            )
            return
        open_orders = self.gateway.open_orders()
        if open_orders:
            result = self.gateway.cancel_orders(open_orders)
            LOGGER.warning(
                "canceled existing orders; deferring new order event_ms=%s oids=%s result=%s",
                event_ms,
                [order["oid"] for order in open_orders],
                result,
            )
            return
        reference_px = ask if decision.is_buy else bid
        result = self.gateway.submit_gtc(
            decision.is_buy,
            decision.size,
            decision.reduce_only,
            reference_px,
        )
        LOGGER.info(
            "%s size=%s current=%s target=%s result=%s",
            decision.reason,
            decision.size,
            decision.current_size,
            decision.target_size,
            result,
        )

    def run(self) -> None:
        self.bootstrap()
        while not self.stop_event.is_set():
            event = self.events.get()
            if event is None:
                break
            try:
                self.evaluate(event)
            except Exception:
                LOGGER.exception("decision failed; no order was retried automatically")

    def stop(self) -> None:
        self.stop_event.set()
        self._replace_event(None)
        self.gateway.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    bot = Bot(Config.from_env())
    signal.signal(signal.SIGINT, lambda _signum, _frame: bot.stop())
    signal.signal(signal.SIGTERM, lambda _signum, _frame: bot.stop())
    bot.run()


if __name__ == "__main__":
    main()
