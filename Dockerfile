FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制后端代码和依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有文件
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=backend/app.py

# 设置时区环境变量
ENV TZ=Asia/Shanghai

# 创建数据目录
RUN mkdir -p /app/data

WORKDIR /app/backend

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "app.py"]