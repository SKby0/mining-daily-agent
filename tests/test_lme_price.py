"""Tests for lme-price-mcp"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from servers._mock_data import MOCK_PRICES, MOCK_TRENDS


def test_mock_prices_structure():
    """验证 mock 价格数据结构"""
    expected_commodities = ["copper", "nickel", "aluminum", "zinc", "gold", "lithium", "pilbara_stock"]
    for commodity in expected_commodities:
        assert commodity in MOCK_PRICES, f"Missing mock price for {commodity}"
        data = MOCK_PRICES[commodity]
        assert "price" in data
        assert "unit" in data
        assert data["price"] > 0


def test_mock_trends_structure():
    """验证 mock 趋势数据结构"""
    for commodity, data in MOCK_TRENDS.items():
        assert "trend_direction" in data
        assert data["trend_direction"] in ("up", "down", "flat")
        assert "min_price" in data
        assert "max_price" in data
        assert data["min_price"] <= data["max_price"]


def test_commodity_validation():
    """验证 commodity 验证逻辑"""
    # 直接导入验证函数
    from servers.lme_price import _validate_commodity

    assert _validate_commodity("copper") == "copper"
    assert _validate_commodity("li") == "lithium"
    assert _validate_commodity("Cu") == "copper"
    assert _validate_commodity("pilbara") == "pilbara_stock"

    try:
        _validate_commodity("unknown_metal")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


if __name__ == "__main__":
    test_mock_prices_structure()
    test_mock_trends_structure()
    test_commodity_validation()
    print("✅ lme-price-mcp tests passed")
