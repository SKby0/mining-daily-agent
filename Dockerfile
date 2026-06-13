FROM python:3.11-slim

WORKDIR /app

# 系统依赖 (pymupdf 编译需要)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用 Docker 层缓存
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# 复制源码
COPY servers/ servers/
COPY agent/ agent/

# 确保输出目录存在
RUN mkdir -p /app/output

ENV PYTHONIOENCODING=utf-8
ENV PYTHONUNBUFFERED=1

# 默认运行 Agent
CMD ["python", "-m", "agent.run"]
