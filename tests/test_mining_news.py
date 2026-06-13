"""Tests for mining-news-mcp"""

import json
import sys
import os

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from servers._mock_data import MOCK_NEWS


def test_mock_news_structure():
    """验证 mock 新闻数据结构"""
    assert len(MOCK_NEWS) > 0, "MOCK_NEWS should not be empty"
    for item in MOCK_NEWS:
        assert "title" in item
        assert "url" in item
        assert "source" in item
        assert "date" in item
        assert "snippet" in item
        assert "mock" in item
        assert item["mock"] is True


def test_mock_news_json_serializable():
    """验证 mock 新闻数据可序列化为 JSON"""
    result = json.dumps(MOCK_NEWS, ensure_ascii=False)
    parsed = json.loads(result)
    assert len(parsed) == len(MOCK_NEWS)


if __name__ == "__main__":
    test_mock_news_structure()
    test_mock_news_json_serializable()
    print("✅ mining-news-mcp tests passed")
