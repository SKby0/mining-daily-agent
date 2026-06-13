"""Tests for Agent Client"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.prompts import SYSTEM_PROMPT, REPORT_TEMPLATE
from agent.report import format_report


def test_system_prompt_structure():
    """验证系统提示词包含必需章节"""
    assert "📰" in SYSTEM_PROMPT
    assert "📊" in SYSTEM_PROMPT
    assert "💰" in SYSTEM_PROMPT
    assert "⚠️" in SYSTEM_PROMPT
    assert "📎" in SYSTEM_PROMPT
    assert "search" in SYSTEM_PROMPT
    assert "get_price" in SYSTEM_PROMPT
    assert "get_trend" in SYSTEM_PROMPT
    assert "extract_resources" in SYSTEM_PROMPT


def test_report_formatting():
    """验证报告格式化"""
    content = "### 📰 新闻摘要\n\n测试新闻\n\n### 💰 价格走势\n\n测试价格"
    result = format_report("矿权日报 - Pilbara 锂矿", content)
    assert "生成时间" in result
    assert "不构成投资建议" in result
    assert "矿权日报" in result


def test_report_missing_sections():
    """验证缺失章节自动补充"""
    content = "只有内容没有章节标记"
    result = format_report("测试报告", content)
    assert "📰" in result
    assert "📊" in result
    assert "💰" in result
    assert "⚠️" in result
    assert "📎" in result


def test_mcp_client_config():
    """验证 MCP 客户端配置"""
    from agent.graph import get_mcp_client_config
    config = get_mcp_client_config()
    assert "mining-news" in config
    assert "mineral-pdf" in config
    assert "lme-price" in config
    for name, server in config.items():
        assert server["transport"] == "stdio"
        assert server["command"] == "python"
        assert len(server["args"]) == 1


if __name__ == "__main__":
    test_system_prompt_structure()
    test_report_formatting()
    test_report_missing_sections()
    test_mcp_client_config()
    print("✅ Agent tests passed")
