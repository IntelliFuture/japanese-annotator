VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: run dev test install venv docker-build docker-run clean

# 创建虚拟环境
venv:
	python3 -m venv $(VENV)

# 安装依赖
install: venv
	$(PIP) install -r requirements.txt

# 启动服务（生产模式）
run:
	$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 启动服务（开发模式，自动重载）
dev:
	@echo "Swagger UI: http://127.0.0.1:8000/docs"
	$(PYTHON) -m uvicorn app.main:app --reload

# 运行测试
test:
	$(PYTHON) -m pytest

# Docker 构建
docker-build:
	docker compose build

# Docker 启动
docker-run:
	docker compose up

# 清理缓存
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
