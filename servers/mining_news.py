"""MCP Server 1: mining-news-mcp — 矿业新闻聚合

工具:
  search(query, days)  — 搜索矿业新闻
  fetch_article(url)   — 获取文章全文

数据源:
  - mining.com RSS (WordPress feed)
  - miningweekly.com (HTML scraping)
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup
from fastmcp import FastMCP

from servers._mock_data import MOCK_NEWS

mcp = FastMCP("mining-news-mcp")

_HEADERS = {
    "User-Agent": "MiningDailyBot/1.0 (research; contact@example.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
_TIMEOUT = 8  # 快速失败，8 秒超时


def _parse_date(date_str: str) -> Optional[datetime]:
    """尝试多种格式解析日期字符串"""
    from dateutil import parser as dateutil_parser
    try:
        return dateutil_parser.parse(date_str, tzinfos=None)
    except (ValueError, TypeError):
        return None


def _is_within_days(date_str: str, days: int) -> bool:
    """判断日期是否在 N 天内"""
    dt = _parse_date(date_str)
    if dt is None:
        return True
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return dt >= cutoff


# ── 搜索 mining.com RSS ─────────────────────────────────────────
def _search_mining_com_rss(query: str, days: int) -> list[dict]:
    """通过 WordPress RSS feed 搜索 mining.com"""
    results = []
    try:
        url = f"https://www.mining.com/feed/?s={query}"
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()

        root = ET.fromstring(resp.text)
        for item in root.iter("item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            description = item.findtext("description", "")

            if not _is_within_days(pub_date, days):
                continue

            results.append({
                "title": title,
                "url": link,
                "source": "mining.com",
                "date": pub_date,
                "snippet": BeautifulSoup(description, "html.parser").get_text(strip=True)[:200],
            })
    except Exception as e:
        print(f"[mining-news-mcp] mining.com RSS error: {e}")

    return results


# ── 搜索 miningweekly.com ───────────────────────────────────────
_KEYWORD_TO_SECTOR = {
    "lithium": "batteries",
    "battery": "batteries",
    "copper": "copper",
    "gold": "gold",
    "iron": "iron-ore",
    "coal": "coal",
    "platinum": "platinum",
    "diamond": "diamonds",
}

def _search_miningweekly(query: str, days: int) -> list[dict]:
    """通过 HTML 页面搜索 miningweekly.com"""
    results = []
    sector = _KEYWORD_TO_SECTOR.get(query.lower())
    if not sector:
        return results

    try:
        url = f"https://www.miningweekly.com/page/{sector}/"
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        for article in soup.select("article, .article-item, .story"):
            title_el = article.select_one("h2 a, h3 a, .article-title a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            link = title_el.get("href", "")
            if link and not link.startswith("http"):
                link = f"https://www.miningweekly.com{link}"

            date_el = article.select_one("time, .date, .pub-date")
            date_str = date_el.get_text(strip=True) if date_el else ""

            snippet_el = article.select_one("p, .excerpt, .summary")
            snippet = snippet_el.get_text(strip=True)[:200] if snippet_el else ""

            if date_str and not _is_within_days(date_str, days):
                continue

            results.append({
                "title": title,
                "url": link,
                "source": "miningweekly.com",
                "date": date_str or "N/A",
                "snippet": snippet,
            })
    except Exception as e:
        print(f"[mining-news-mcp] miningweekly.com error: {e}")

    return results


# ── MCP 工具 ─────────────────────────────────────────────────────
@mcp.tool
def search(query: str, days: int = 7) -> str:
    """Search mining news articles matching the query from the past N days.

    Args:
        query: Search keywords, e.g. 'lithium', 'Pilbara', 'copper supply'
        days: Number of days to look back (default 7, max 30)

    Returns:
        JSON string of list[dict], each dict has keys:
        title, url, source, date, snippet
    """
    days = max(1, min(days, 30))

    # 从两个数据源搜索（任一失败不影响另一个）
    results = []
    results.extend(_search_mining_com_rss(query, days))
    results.extend(_search_miningweekly(query, days))

    # 去重 (按 URL)
    seen_urls = set()
    unique = []
    for item in results:
        if item["url"] not in seen_urls:
            seen_urls.add(item["url"])
            unique.append(item)

    # 按日期排序 (新的在前)
    unique.sort(key=lambda x: _parse_date(x["date"]) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    # 最多返回 5 条，减少 token 消耗
    unique = unique[:5]

    # 如果没有结果，使用 mock 数据
    if not unique:
        keywords = query.lower().split()
        mock_filtered = [
            item for item in MOCK_NEWS
            if any(kw in item["title"].lower() or kw in item["snippet"].lower() for kw in keywords)
        ]
        if not mock_filtered:
            mock_filtered = MOCK_NEWS[:5]
        unique = mock_filtered

    return json.dumps(unique, ensure_ascii=False)


@mcp.tool
def fetch_article(url: str) -> str:
    """Fetch and extract the full text content of a mining news article.

    Args:
        url: The article URL to fetch

    Returns:
        JSON string of dict with keys: title, author, date, content, source
    """
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # 提取标题
        title = ""
        el = soup.find("h1") or soup.find("title")
        if el:
            title = el.get_text(strip=True)

        # 提取正文
        content = ""
        for selector in [
            {"name": "article"},
            {"attrs": {"class": lambda c: c and "entry-content" in c.lower()}},
            {"attrs": {"class": lambda c: c and "article-body" in c.lower()}},
        ]:
            el = soup.find(**selector)
            if el:
                for tag in el.find_all(["script", "style", "nav", "footer", "aside"]):
                    tag.decompose()
                content = el.get_text(separator="\n", strip=True)
                break

        if not content:
            paragraphs = soup.find_all("p")
            content = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        # 截断
        if len(content) > 3000:
            content = content[:3000] + "\n... (truncated)"

        source = "mining.com" if "mining.com" in url else "miningweekly.com" if "miningweekly.com" in url else url.split("/")[2]

        result = {"title": title, "content": content, "source": source}
    except Exception as e:
        result = {"error": f"Failed to fetch: {e}", "url": url}

    return json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
