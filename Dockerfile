FROM python:3.11-slim

# 仅需安装基础依赖，无需编译 MeCab
WORKDIR /app

# 安装 Python 依赖（fugashi 包含预编译 wheel）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8080

# 运行应用
CMD ["python", "-m", "src.main"]
