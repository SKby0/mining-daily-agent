# 矿权日报 Agent — 快速启动指南

> 5 分钟从零到运行

## 前置条件

- **Python 3.11+**
- **Docker & Docker Compose**（可选，推荐）
- **LLM API Key**（OpenAI 兼容接口）

---

## 方式一：Web 界面（推荐，有图形界面）

```bash
# 1. 进入项目目录
cd mining-daily-agent

# 2. 创建虚拟环境 & 安装依赖
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e .

# 3. 设置 API Key
cp .env.example .env
# 编辑 .env，将 LLM_API_KEY 改为你的真实密钥

# 4. 启动 Web 界面
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`，界面包含：
- 📝 查询输入框 + 预设快速查询按钮
- 🚀 一键生成简报
- 📊 Markdown 渲染的报告展示
- 📥 一键下载 `.md` 文件
- ⚙️ 侧边栏可修改 LLM 配置

---

## 方式二：命令行

```bash
# 激活虚拟环境后
# Windows
.venv\Scripts\python -X utf8 -m agent.run "给我生成一份关于 Pilbara 锂矿的今日简报"

# macOS/Linux
python -m agent.run "给我生成一份关于 Pilbara 锂矿的今日简报"

# 查看报告
cat output/report_*.md
```

---

## 方式三：Docker Compose

```bash
# 1. 创建环境变量文件并填入 API Key
cp .env.example .env
# 编辑 .env，将 LLM_API_KEY 改为你的真实密钥

# 2. 一键构建并运行
docker compose up agent

# 3. 查看生成的报告
ls output/
cat output/report_*.md
```

### 自定义查询

```bash
docker compose run agent python -m agent.run "搜索最近7天的铜矿新闻"
```

### 单独测试 MCP Server

```bash
docker compose run mining-news-mcp
docker compose run lme-price-mcp
```

---

## 方式四：Claude Desktop / Cursor 集成

### Claude Desktop

1. 复制 `mcp-config.json` 的内容
2. 粘贴到 Claude Desktop 配置文件：
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
3. **重要**：将 `args` 中的路径改为**绝对路径**，例如：
   ```json
   {
     "mcpServers": {
       "mining-news-mcp": {
         "command": "python",
         "args": ["D:/desktop/mining-daily-agent/servers/mining_news.py"],
         "env": {}
       }
     }
   }
   ```
4. 完全重启 Claude Desktop
5. 在对话中直接使用 MCP 工具

### Cursor

1. 在项目根目录创建 `.cursor/mcp.json`
2. 复制 `mcp-config.json` 的内容进去
3. 重启 Cursor

---

## 查询示例

| 查询 | 说明 |
|------|------|
| `给我生成一份关于 Pilbara 锂矿的今日简报` | 完整日报 |
| `搜索最近7天的铜矿新闻` | 只搜索新闻 |
| `提取这个NI 43-101报告的储量数据: https://example.com/report.pdf` | 只提取 PDF |
| `查看锂价近30天走势` | 只查价格 |
| `查看 Pilbara Minerals 股价` | 单个商品价格 |

---

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| scraping 失败 | 系统自动使用模拟数据，报告中会标注 ⚠️ 模拟数据 |
| yfinance 返回空数据 | 可能是市场休市/周末，尝试使用更早的日期 |
| LLM_API_KEY 未设置 | 在 `.env` 文件或环境变量中设置 |
| Docker 构建慢 | 首次构建需要下载依赖，约 2-3 分钟 |
| 中文乱码 | Windows 加 `-X utf8`；或设 `$env:PYTHONUTF8=1` |
| MCP Server 无法启动 | 确认 `pip install -e .` 已执行，所有依赖已安装 |

---

## 项目结构

```
mining-daily-agent/
├── app.py             # Streamlit Web 界面
├── servers/           # 3 个 MCP Server (FastMCP)
│   ├── mining_news.py    # 新闻聚合
│   ├── mineral_pdf.py    # PDF 解析
│   ├── lme_price.py      # 价格行情
│   └── _mock_data.py     # 模拟数据兜底
├── agent/             # Agent Client (LangGraph)
│   ├── graph.py          # MCP 连接配置
│   ├── prompts.py        # 系统提示词
│   ├── report.py         # 报告格式化
│   └── run.py            # CLI 入口
├── output/            # 生成的报告
├── mcp-config.json    # Claude Desktop / Cursor 配置
└── docker-compose.yml # 一键启动
```
