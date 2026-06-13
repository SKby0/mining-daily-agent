"""LangGraph ReAct Agent 定义 — 连接 3 个 MCP Server"""

import os
import sys
from langchain_mcp_adapters.client import MultiServerMCPClient


def _get_python_command() -> str:
    """获取当前 Python 解释器路径（确保 MCP Server 子进程使用同一个 venv）。"""
    return sys.executable


def get_mcp_client_config() -> dict:
    """返回 MCP Server 连接配置。

    支持通过环境变量覆盖服务器脚本路径（Docker 内使用绝对路径）。
    使用当前 Python 解释器启动 MCP Server，确保依赖一致。
    """
    base_dir = os.getenv("MCP_SERVERS_DIR", os.path.join(os.path.dirname(__file__), "..", "servers"))
    base_dir = os.path.abspath(base_dir)
    python = _get_python_command()

    return {
        "mining-news": {
            "command": python,
            "args": [os.path.join(base_dir, "mining_news.py")],
            "transport": "stdio",
        },
        "mineral-pdf": {
            "command": python,
            "args": [os.path.join(base_dir, "mineral_pdf.py")],
            "transport": "stdio",
        },
        "lme-price": {
            "command": python,
            "args": [os.path.join(base_dir, "lme_price.py")],
            "transport": "stdio",
        },
    }


def create_mcp_client() -> MultiServerMCPClient:
    """创建并返回 MCP 客户端实例。"""
    config = get_mcp_client_config()
    return MultiServerMCPClient(config)
