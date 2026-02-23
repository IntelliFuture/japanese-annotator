FROM python:3.11-slim

# 安装 MeCab 和词典
RUN apt-get update && apt-get install -y \
    mecab \
    mecab-ipadic \
    libmecab-dev \
    build-essential \
    git \
    curl \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# 安装 mecab-ipadic-neologd
WORKDIR /tmp
RUN git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git \
    && cd mecab-ipadic-neologd \
    && ./bin/install-mecab-ipadic-neologd -n -y \
    && rm -rf /tmp/mecab-ipadic-neologd

# 设置工作目录
WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8080

# 运行应用
CMD ["python", "-m", "src.main"]
