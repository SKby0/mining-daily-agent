"""MCP Server 3: lme-price-mcp — 金属/商品价格行情

工具:
  get_price(commodity, date) — 获取某商品某日价格
  get_trend(commodity, days) — 获取某商品近 N 天走势

数据源:
  - yfinance: 铜/镍/铝/锌/金 COMEX/LME 期货
  - yfinance: PLS.AX (Pilbara Minerals 股价)
  - Trading Economics: 锂价 (网页抓取)
"""

import json
from datetime import datetime, timedelta
from typing import Optional

import requests
import yfinance as yf
from bs4 import BeautifulSoup
from fastmcp import FastMCP

from servers._mock_data import MOCK_PRICES, MOCK_TRENDS

mcp = FastMCP("lme-price-mcp")

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
_TIMEOUT = 10

# yfinance Ticker 映射
YFINANCE_TICKERS = {
    "copper": "HG=F",
    "nickel": "NI=F",
    "aluminum": "ALI=F",
    "zinc": "ZNC=F",
    "gold": "GC=F",
    "pilbara_stock": "PLS.AX",
}

VALID_COMMODITIES = list(YFINANCE_TICKERS.keys()) + ["lithium"]

UNITS = {
    "copper": "USD/lb",
    "nickel": "USD/tonne",
    "aluminum": "USD/tonne",
    "zinc": "USD/tonne",
    "gold": "USD/oz",
    "lithium": "CNY/tonne",
    "pilbara_stock": "AUD",
}

# ── 内存缓存（避免同一 session 重复下载）────────────────────────
_price_cache: dict = {}
_trend_cache: dict = {}


def _validate_commodity(commodity: str) -> str:
    """验证并归一化 commodity 名称"""
    commodity = commodity.lower().strip()
    aliases = {
        "li": "lithium", "cu": "copper", "al": "aluminum",
        "aluminium": "aluminum", "zn": "zinc", "au": "gold",
        "ni": "nickel", "pls": "pilbara_stock", "pilbara": "pilbara_stock",
    }
    commodity = aliases.get(commodity, commodity)
    if commodity not in VALID_COMMODITIES:
        raise ValueError(
            f"Unknown commodity '{commodity}'. Valid: {', '.join(VALID_COMMODITIES)}"
        )
    return commodity


# ── yfinance 价格获取 ────────────────────────────────────────────
def _get_yfinance_price(ticker: str, date_str: str = "") -> dict:
    """通过 yfinance 获取单个商品价格（带缓存）"""
    cache_key = f"{ticker}:{date_str}"
    if cache_key in _price_cache:
        return _price_cache[cache_key]

    try:
        t = yf.Ticker(ticker)
        if date_str:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            end_date = target_date + timedelta(days=5)  # 多取几天覆盖非交易日
            hist = t.history(
                start=target_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
            )
        else:
            hist = t.history(period="5d")

        if hist.empty:
            result = {"error": f"No price data for {ticker}"}
        else:
            last_row = hist.iloc[-1]
            result = {
                "price": round(float(last_row["Close"]), 4),
                "date": hist.index[-1].strftime("%Y-%m-%d"),
            }
    except Exception as e:
        result = {"error": f"yfinance error: {e}"}

    _price_cache[cache_key] = result
    return result


# ── Trading Economics 锂价抓取 ───────────────────────────────────
def _get_lithium_price() -> dict:
    """从 Trading Economics 抓取锂价（带缓存）"""
    if "lithium" in _price_cache:
        return _price_cache["lithium"]

    try:
        url = "https://tradingeconomics.com/commodity/lithium"
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        price = None

        # 尝试多种提取方式
        for el in soup.find_all(attrs={"data-value": True}):
            try:
                price = float(el["data-value"])
                if 10000 < price < 500000:
                    break
                price = None
            except (ValueError, TypeError):
                continue

        if price is None:
            import re
            text = soup.get_text()
            matches = re.findall(r"([\d,]+(?:\.\d+)?)\s*(?:CNY|Yuan)", text)
            if matches:
                try:
                    price = float(matches[0].replace(",", ""))
                except ValueError:
                    pass

        if price is not None:
            result = {"price": price, "unit": "CNY/tonne", "date": datetime.now().strftime("%Y-%m-%d"), "source": "Trading Economics"}
        else:
            result = {"error": "Could not extract lithium price"}
    except Exception as e:
        result = {"error": f"Scrape error: {e}"}

    _price_cache["lithium"] = result
    return result


# ── yfinance 趋势数据 ────────────────────────────────────────────
def _get_yfinance_trend(ticker: str, commodity: str, days: int) -> dict:
    """通过 yfinance 获取趋势数据（带缓存）"""
    cache_key = f"{ticker}:{days}"
    if cache_key in _trend_cache:
        return _trend_cache[cache_key]

    try:
        hist = yf.download(ticker, period=f"{days}d", progress=False)

        if hist.empty:
            result = {"error": f"No trend data for {ticker}"}
        else:
            prices = [round(float(c), 4) for c in hist["Close"]]
            dates = [d.strftime("%Y-%m-%d") for d in hist.index]

            start_price = prices[0]
            end_price = prices[-1]
            change_pct = round(((end_price - start_price) / start_price) * 100, 2) if start_price else 0
            trend_direction = "flat" if abs(change_pct) < 1 else ("up" if change_pct > 0 else "down")

            # 只返回摘要，不返回全量数据点（减少 token）
            result = {
                "commodity": commodity,
                "unit": UNITS[commodity],
                "trend_direction": trend_direction,
                "change_pct": change_pct,
                "start_price": start_price,
                "end_price": end_price,
                "start_date": dates[0],
                "end_date": dates[-1],
                "min_price": round(min(prices), 4),
                "max_price": round(max(prices), 4),
                "avg_price": round(sum(prices) / len(prices), 4),
                "data_points_count": len(prices),
                "source": "Yahoo Finance",
            }
    except Exception as e:
        result = {"error": f"yfinance trend error: {e}"}

    _trend_cache[cache_key] = result
    return result


# ── MCP 工具 ─────────────────────────────────────────────────────
@mcp.tool
def get_price(commodity: str, date: str = "") -> str:
    """Get the price of a commodity on a specific date.

    Args:
        commodity: One of: copper, nickel, aluminum, zinc, gold, lithium, pilbara_stock
        date: Date in YYYY-MM-DD format (default: latest available)

    Returns:
        JSON string of dict with keys: commodity, price, unit, date, source
    """
    try:
        commodity = _validate_commodity(commodity)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    result = {"commodity": commodity, "unit": UNITS[commodity]}

    if commodity == "lithium":
        price_data = _get_lithium_price()
        if "error" in price_data:
            mock = MOCK_PRICES["lithium"]
            result.update(mock)
            result["mock"] = True
            result["source"] = "mock data"
        else:
            result.update(price_data)
    else:
        ticker = YFINANCE_TICKERS[commodity]
        price_data = _get_yfinance_price(ticker, date)
        if "error" in price_data:
            mock = MOCK_PRICES.get(commodity, {})
            result.update(mock)
            result["mock"] = True
            result["source"] = "mock data"
        else:
            result["price"] = price_data["price"]
            result["date"] = price_data["date"]
            result["source"] = "Yahoo Finance"

    return json.dumps(result, ensure_ascii=False)


@mcp.tool
def get_trend(commodity: str, days: int = 30) -> str:
    """Get price trend summary for a commodity over the past N days.

    Args:
        commodity: One of: copper, nickel, aluminum, zinc, gold, lithium, pilbara_stock
        days: Number of days (default 30, max 365)

    Returns:
        JSON string of dict with keys: commodity, unit, trend_direction,
        change_pct, start_price, end_price, min_price, max_price, avg_price, source
    """
    days = max(1, min(days, 365))

    try:
        commodity = _validate_commodity(commodity)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    if commodity == "lithium":
        result = MOCK_TRENDS.get("lithium", {}).copy()
        if not result:
            result = {"commodity": "lithium", "unit": "CNY/tonne"}
        result["mock"] = True
        result["source"] = "mock data"
    else:
        ticker = YFINANCE_TICKERS[commodity]
        result = _get_yfinance_trend(ticker, commodity, days)
        if "error" in result:
            mock = MOCK_TRENDS.get(commodity, {})
            result = mock.copy() if mock else {"commodity": commodity}
            result["mock"] = True
            result["source"] = "mock data"

    return json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
   mcp.run()
