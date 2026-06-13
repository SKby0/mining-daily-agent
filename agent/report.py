"""Markdown 报告后处理 — 统一格式、添加时间戳、整理链接"""

from datetime import datetime


def format_report(title: str, content: str) -> str:
    """将 LLM 输出的内容包装成最终报告格式。

    Args:
        title: 报告标题
        content: LLM 生成的 Markdown 内容

    Returns:
        完整的 Markdown 报告字符串
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data_date = datetime.now().strftime("%Y-%m-%d")

    # 确保内容包含必需的章节标记
    required_sections = ["📰", "📊", "💰", "⚠️", "📎"]
    for section_emoji in required_sections:
        if section_emoji not in content:
            if section_emoji == "📰":
                content += "\n\n### 📰 新闻摘要\n\n暂无相关新闻数据。\n"
            elif section_emoji == "📊":
                content += "\n\n### 📊 储量数据\n\n未提供 PDF 报告链接，无法提取储量数据。\n"
            elif section_emoji == "💰":
                content += "\n\n### 💰 价格走势\n\n暂无价格数据。\n"
            elif section_emoji == "⚠️":
                content += "\n\n### ⚠️ 风险提示\n\n基于当前数据，请关注以下风险：\n1. 大宗商品价格波动风险\n2. 行业政策变化风险\n3. 供需关系变化风险\n"
            elif section_emoji == "📎":
                content += "\n\n### 📎 引用源链接\n\n暂无引用源。\n"

    # 确保报告以标题开头
    if not content.strip().startswith("# "):
        content = f"# {title}\n\n{content}"

    # 添加时间戳和免责声明
    header = f"> 生成时间: {timestamp} | 数据截止: {data_date}\n\n---\n\n"
    disclaimer = "\n\n---\n\n*本报告由矿权日报 Agent 自动生成，仅供参考，不构成投资建议。*\n"

    # 如果内容中已有标题行，在其后插入 header
    lines = content.split("\n")
    if lines[0].startswith("# "):
        result = lines[0] + "\n\n" + header + "\n".join(lines[1:]) + disclaimer
    else:
        result = header + content + disclaimer

    return result
