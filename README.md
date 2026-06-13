# ⛏️ 矿权日报 Agent

基于 **MCP 协议 + LangGraph** 的矿权行业智能日报生成系统。输入自然语言查询，自动聚合新闻、提取储量数据、获取价格走势，输出结构化中文 Markdown 简报。

## ✨ 功能特性

- 🔍 **新闻聚合** — 自动抓取 mining.com / miningweekly.com 矿业新闻
- 📊 **PDF 储量提取** — 解析 NI 43-101 技术报告，提取 Indicated/Inferred 资源量
- 💰 **价格行情** — 铜/镍/铝/锌/金期货 + 锂价 + ASX 股价
- 📝 **自动生成简报** — 新闻摘要 + 储量数据 + 价格走势 + 风险提示 + 引用源
- 🌐 **Web 界面** — Streamlit 可视化操作，一键生成 + 下载报告
- 🖥️ **CLI 模式** — 命令行直接运行，适合自动化场景
- 🔌 **MCP 标准** — 3 个独立 MCP Server，可接入 Claude Desktop / Cursor

## 🏗️ 架构

```
┌─────────────────────────────────────────────────┐
│                  Agent Client                    │
│          (LangGraph ReAct + LLM)                 │
└────────┬──────────┬──────────┬──────────────────┘
         │ MCP      │ MCP      │ MCP
         │ stdio    │ stdio    │ stdio
┌────────▼───┐ ┌───▼────────┐ ┌▼──────────────┐
│ mining-news │ │ mineral-pdf │ │  lme-price    │
│   -mcp      │ │   -mcp      │ │   -mcp        │
│             │ │             │ │               │
│ search()    │ │ extract_    │ │ get_price()   │
│ fetch_      │ │ resources() │ │ get_trend()   │
│ article()   │ │             │ │               │
└─────────────┘ └─────────────┘ └───────────────┘
```

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| MCP 框架 | FastMCP 3.x |
| Agent 编排 | LangGraph ReAct |
| LLM | OpenAI 兼容 API (ChatOpenAI) |
| 新闻抓取 | requests + BeautifulSoup4 |
| PDF 解析 | pdfplumber + PyMuPDF |
| 价格数据 | yfinance + Trading Economics |
| Web 界面 | Streamlit |
| 容器化 | Docker + Docker Compose |

## 🚀 快速开始

### 前置条件

- Python 3.11+
- LLM API Key（OpenAI 兼容接口）

### 方式一：Web 界面（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/SKby0/mining-daily-agent.git
cd mining-daily-agent

# 2. 创建虚拟环境 & 安装依赖
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -e .

# 3. 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 LLM_API_KEY

# 4. 启动
streamlit run app.py
```

浏览器打开 `http://localhost:8501`，输入查询 → 点击生成 → 查看/下载报告。

### 方式二：命令行

```bash
# Windows
.venv\Scripts\python -X utf8 -m agent.run "给我生成一份关于 Pilbara 锂矿的今日简报"

# macOS/Linux
python -m agent.run "给我生成一份关于 Pilbara 锂矿的今日简报"
```

### 方式三：Docker Compose

```bash
cp .env.example .env  # 填入 API Key
docker compose up agent
```

### 方式四：Claude Desktop / Cursor

将 `mcp-config.json` 中的路径改为绝对路径，复制到：
- Claude Desktop: `%APPDATA%\Claude\claude_desktop_config.json` (Windows) 或 `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
- Cursor: `.cursor/mcp.json`

重启后即可在对话中直接调用 MCP 工具。

## 📋 查询示例

| 查询 | 说明 |
|------|------|
| `给我生成一份关于 Pilbara 锂矿的今日简报` | 完整日报 |
| `搜索最近7天的铜矿新闻` | 只搜索新闻 |
| `查看锂价近30天走势` | 只查价格 |
| `提取这个NI 43-101报告的储量数据: https://example.com/report.pdf` | PDF 解析 |

## 📁 项目结构

```
mining-daily-agent/
├── app.py                 # Streamlit Web 界面
├── servers/               # 3 个 MCP Server (FastMCP)
│   ├── mining_news.py        # 🔍 新闻聚合: search / fetch_article
│   ├── mineral_pdf.py        # 📊 PDF 解析: extract_resources
│   ├── lme_price.py          # 💰 价格行情: get_price / get_trend
│   └── _mock_data.py         # 模拟数据兜底
├── agent/                 # Agent Client (LangGraph)
│   ├── graph.py              # MCP 连接配置
│   ├── prompts.py            # 系统提示词
│   ├── report.py             # 报告格式化
│   └── run.py                # CLI 入口
├── tests/                 # 单元测试
├── output/                # 生成的报告
├── mcp-config.json        # Claude Desktop / Cursor 配置
├── docker-compose.yml     # Docker 一键启动
├── Dockerfile
└── pyproject.toml         # 依赖声明
```

## 🔌 MCP Server 详情

### mining-news-mcp

| 工具 | 参数 | 说明 |
|------|------|------|
| `search(query, days)` | query: 关键词, days: 回溯天数 | 搜索 mining.com RSS + miningweekly.com |
| `fetch_article(url)` | url: 文章链接 | 获取文章全文 |

### mineral-pdf-mcp

| 工具 | 参数 | 说明 |
|------|------|------|
| `extract_resources(pdf_url)` | pdf_url: PDF 链接或本地路径 | 两阶段提取: pymupdf 扫描 + pdfplumber 精确解析 |

### lme-price-mcp

| 工具 | 参数 | 说明 |
|------|------|------|
| `get_price(commodity, date)` | commodity: copper/nickel/.../lithium | 获取实时/历史价格 |
| `get_trend(commodity, days)` | commodity, days: 天数 | 获取价格走势摘要 |

支持的商品: `copper`, `nickel`, `aluminum`, `zinc`, `gold`, `lithium`, `pilbara_stock`

## 📄 报告示例

生成报告包含 5 个章节：

1. **📰 新闻摘要** — 3-5 条相关新闻，含来源链接
2. **📊 储量数据** — Indicated/Inferred 资源量表格（需提供 PDF 链接）
3. **💰 价格走势** — 当前价格 + 30 天趋势 + 涨跌幅
4. **⚠️ 风险提示** — 基于数据的 2-3 条风险因素
5. **📎 引用源链接** — 所有数据来源

> 模拟数据自动标注 ⚠️ 模拟数据，保证系统始终可运行

## 📜 License

MIT
