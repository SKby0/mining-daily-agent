"""矿权日报 Agent — CLI 入口

用法:
  python -m agent.run "给我生成一份关于 Pilbara 锂矿的今日简报"
  python -m agent.run  # 默认查询: Pilbara 锂矿简报

环境变量:
  LLM_API_KEY   — API 密钥 (必填)
  LLM_BASE_URL  — API Base URL (默认: https://mydamoxing.cn)
  LLM_MODEL     — 模型名称 (默认: glm-5.1)
"""

import asyncio
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agent.graph import create_mcp_client
from agent.prompts import SYSTEM_PROMPT
from agent.report import format_report


async def run(query: str) -> str:
    """运行 Agent 生成报告，返回 Markdown 字符串。"""
    # 加载 .env
    load_dotenv()

    # 初始化 LLM
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise ValueError("LLM_API_KEY 环境变量未设置。请在 .env 文件或环境变量中配置。")

    model = ChatOpenAI(
        base_url=os.getenv("LLM_BASE_URL", "https://mydamoxing.cn") + "/v1",
        model=os.getenv("LLM_MODEL", "glm-5.1"),
        api_key=api_key,
        temperature=0.3,
        max_tokens=4096,
    )

    # 连接 MCP Servers 并获取工具
    # langchain-mcp-adapters 0.3.0: MultiServerMCPClient 不再使用 async with,
    # 直接创建实例后调用 get_tools()
    client = create_mcp_client()
    tools = await client.get_tools()

    print(f"[agent] 已连接 {len(tools)} 个 MCP 工具:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:80]}...")

    # 创建 ReAct Agent
    agent = create_react_agent(model, tools, prompt=SYSTEM_PROMPT)

    print(f"\n[agent] 正在生成报告: {query}\n")
    result = await agent.ainvoke({"messages": [("user", query)]})

    # 提取最终消息
    final_message = result["messages"][-1].content

    # 后处理格式化
    title = _extract_title(query)
    report = format_report(title, final_message)

    return report


def _extract_title(query: str) -> str:
    """从用户查询中提取报告标题"""
    if "关于" in query and "的" in query:
        start = query.index("关于") + 2
        end = query.index("的", start)
        return f"矿权日报 - {query[start:end]}"
    elif "简报" in query:
        return "矿权日报"
    else:
        return f"矿权日报 - {query[:20]}"


async def main():
    """CLI 主入口"""
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "给我生成一份关于 Pilbara 锂矿的今日简报"

    try:
        report = await run(query)

        # 保存到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
        output_dir = os.path.abspath(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, f"report_{timestamp}.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n[agent] 报告已保存至: {output_path}")
        print("\n" + "=" * 60)
        print(report)

    except ValueError as e:
        print(f"[error] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[error] Agent 运行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# Windows 控制台编码修复
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if __name__ == "__main__":
    asyncio.run(main())
