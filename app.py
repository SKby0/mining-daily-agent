"""矿权日报 Agent — Streamlit Web UI

启动方式:
  streamlit run app.py
"""

import os
import sys
from datetime import datetime

import streamlit as st

# Windows 编码修复
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv()

from agent.graph import create_mcp_client
from agent.prompts import SYSTEM_PROMPT
from agent.report import format_report

# ── Streamlit 页面配置 ──────────────────────────────────────────
st.set_page_config(
    page_title="矿权日报 Agent",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 侧边栏 ──────────────────────────────────────────────────────
with st.sidebar:
    st.title("⛏️ 矿权日报 Agent")
    st.markdown("---")

    # LLM 配置
    st.subheader("⚙️ LLM 配置")
    llm_base_url = st.text_input("API Base URL", value=os.getenv("LLM_BASE_URL", "https://mydamoxing.cn"))
    llm_model = st.text_input("Model", value=os.getenv("LLM_MODEL", "glm-5.1"))
    llm_api_key = st.text_input("API Key", value=os.getenv("LLM_API_KEY", ""), type="password")

    st.markdown("---")

    # 预设查询模板
    st.subheader("📋 快速查询")
    presets = [
        "给我生成一份关于 Pilbara 锂矿的今日简报",
        "搜索最近7天的铜矿新闻",
        "查看锂价近30天走势",
        "查看 Pilbara Minerals 股价",
        "查看铜和镍的价格走势对比",
    ]
    for preset in presets:
        if st.button(preset, key=preset, use_container_width=True):
            st.session_state.query = preset

    st.markdown("---")
    st.markdown(
        "<small>Powered by FastMCP + LangGraph</small>",
        unsafe_allow_html=True,
    )

# ── 主界面 ──────────────────────────────────────────────────────
st.title("⛏️ 矿权日报 — Mining Daily Report")

# 查询输入
query = st.text_area(
    "输入查询指令",
    value=st.session_state.get("query", "给我生成一份关于 Pilbara 锂矿的今日简报"),
    height=100,
    help="支持自然语言查询，如：'给我生成一份关于 Pilbara 锂矿的今日简报'",
)

# 生成按钮
col1, col2 = st.columns([1, 5])
with col1:
    generate_btn = st.button("🚀 生成简报", type="primary", use_container_width=True)


# ── 同步运行 Agent（兼容 Streamlit 事件循环）──────────────────────
def run_agent_sync(query: str, api_key: str, base_url: str, model: str) -> str:
    """在新线程的事件循环中运行 Agent，避免与 Streamlit 事件循环冲突。"""
    import asyncio
    from threading import Thread

    result_holder = {"result": None, "error": None}

    def _worker():
        async def _run():
            from langchain_openai import ChatOpenAI
            from langgraph.prebuilt import create_react_agent

            llm = ChatOpenAI(
                base_url=base_url + "/v1",
                model=model,
                api_key=api_key,
                temperature=0.3,
                max_tokens=4096,
            )

            client = create_mcp_client()
            tools = await client.get_tools()

            agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)
            result = await agent.ainvoke({"messages": [("user", query)]})

            final_message = result["messages"][-1].content

            # 提取标题
            title = "矿权日报"
            if "关于" in query and "的" in query:
                start = query.index("关于") + 2
                end = query.index("的", start)
                title = f"矿权日报 - {query[start:end]}"

            return format_report(title, final_message)

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result_holder["result"] = loop.run_until_complete(_run())
        except Exception as e:
            result_holder["error"] = e
        finally:
            loop.close()

    t = Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout=300)  # 最多等 5 分钟

    if result_holder["error"]:
        raise result_holder["error"]
    if result_holder["result"] is None:
        raise TimeoutError("Agent 运行超时（5分钟），请重试")
    return result_holder["result"]


# ── 报告生成逻辑 ────────────────────────────────────────────────
if generate_btn and query:
    if not llm_api_key:
        st.error("请先在侧边栏填写 API Key")
        st.stop()

    # 进度提示
    with st.spinner("⏳ 正在连接 MCP Servers 并调用 LLM 生成简报，预计 1-2 分钟..."):
        try:
            report = run_agent_sync(query, llm_api_key, llm_base_url, llm_model)

            # 保存报告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(os.path.dirname(__file__), "output")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"report_{timestamp}.md")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)

            st.success("✅ 报告生成完成！")

            # 显示报告
            st.markdown("---")
            st.markdown(report)

            # 下载按钮
            st.download_button(
                label="📥 下载 Markdown 报告",
                data=report,
                file_name=f"mining_report_{timestamp}.md",
                mime="text/markdown",
            )

        except Exception as e:
            st.error(f"❌ 生成失败: {e}")
            with st.expander("查看详细错误"):
                import traceback
                st.code(traceback.format_exc())

elif generate_btn and not query:
    st.warning("请输入查询指令")

# ── 底部信息 ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #888; font-size: 0.85em;">
        矿权日报 Agent | FastMCP + LangGraph + Streamlit<br>
        本报告仅供参考，不构成投资建议
    </div>
    """,
    unsafe_allow_html=True,
)
