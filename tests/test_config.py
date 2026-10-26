from decimal import Decimal

import pytest

from hyperliquid_bot.config import Config


def test_live_mode_requires_credentials() -> None:
    config = Config(dry_run=False)
    with pytest.raises(ValueError, match="requires"):
        config.validate()


def test_tap_cannot_exceed_limit() -> None:
    config = Config(tap=Decimal("0.10"), limit_size=Decimal("0.08"))
    with pytest.raises(ValueError, match="cannot exceed"):
        config.validate()


def test_timeframe_must_be_supported_by_hyperliquid() -> None:
    config = Config(timeframe="1M")
    config.validate()

    with pytest.raises(ValueError, match="HL_TIMEFRAME"):
        Config(timeframe="M5").validate()


def test_leverage_and_margin_mode_are_validated() -> None:
    with pytest.raises(ValueError, match="HL_LEVERAGE"):
        Config(leverage=0).validate()

    with pytest.raises(ValueError, match="HL_MARGIN_MODE"):
        Config(margin_mode="portfolio").validate()
