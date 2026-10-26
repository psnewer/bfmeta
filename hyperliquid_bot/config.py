from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal

TIMEFRAMES = {"1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "8h", "12h", "1d", "3d", "1w", "1M"}


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    if raw.lower() in {"1", "true", "yes", "on"}:
        return True
    if raw.lower() in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true or false")


@dataclass(frozen=True)
class Config:
    network: str = "testnet"
    dry_run: bool = True
    coin: str = "BTC"
    side: str = "forward"
    account_address: str = ""
    secret_key: str = ""
    leverage: int = 1
    margin_mode: str = "cross"
    tap: Decimal = Decimal("0.02")
    limit_size: Decimal = Decimal("0.08")
    t_guide: Decimal = Decimal("0")
    limit_spread: Decimal = Decimal("0.0005")
    timeframe: str = "5m"
    all_in: bool = False

    @classmethod
    def from_env(cls) -> "Config":
        config = cls(
            network=os.getenv("HL_NETWORK", "testnet").lower(),
            dry_run=_bool("HL_DRY_RUN", True),
            coin=os.getenv("HL_COIN", "BTC").upper(),
            side=os.getenv("HL_SIDE", "forward").lower(),
            account_address=os.getenv("HL_ACCOUNT_ADDRESS", ""),
            secret_key=os.getenv("HL_SECRET_KEY", ""),
            leverage=int(os.getenv("HL_LEVERAGE", "1")),
            margin_mode=os.getenv("HL_MARGIN_MODE", "cross").lower(),
            tap=Decimal(os.getenv("HL_TAP", "0.02")),
            limit_size=Decimal(os.getenv("HL_LIMIT_SIZE", "0.08")),
            t_guide=Decimal(os.getenv("HL_T_GUIDE", "0")),
            limit_spread=Decimal(os.getenv("HL_LIMIT_SPREAD", "0.0005")),
            timeframe=os.getenv("HL_TIMEFRAME", "5m"),
            all_in=_bool("HL_ALL_IN", False),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.network not in {"testnet", "mainnet"}:
            raise ValueError("HL_NETWORK must be testnet or mainnet")
        if self.side not in {"forward", "backward"}:
            raise ValueError("HL_SIDE must be forward or backward")
        if self.leverage <= 0:
            raise ValueError("HL_LEVERAGE must be a positive integer")
        if self.margin_mode not in {"cross", "isolated"}:
            raise ValueError("HL_MARGIN_MODE must be cross or isolated")
        if self.tap <= 0 or self.limit_size <= 0:
            raise ValueError("HL_TAP and HL_LIMIT_SIZE must be positive")
        if self.tap > self.limit_size:
            raise ValueError("HL_TAP cannot exceed HL_LIMIT_SIZE")
        if self.limit_spread <= 0:
            raise ValueError("HL_LIMIT_SPREAD must be positive")
        if self.timeframe not in TIMEFRAMES:
            raise ValueError(f"HL_TIMEFRAME must be one of: {', '.join(sorted(TIMEFRAMES))}")
        if not self.dry_run and (not self.account_address or not self.secret_key):
            raise ValueError("live mode requires HL_ACCOUNT_ADDRESS and HL_SECRET_KEY")
