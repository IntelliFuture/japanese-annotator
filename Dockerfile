FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install --prefix=/install -r requirements.txt


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_HOME=/app \
    APP_PORT=8000 \
    USER_DICT_DIR=/app/user_dict \
    UVICORN_WORKERS=2

WORKDIR ${APP_HOME}

RUN addgroup --system app \
    && adduser --system --ingroup app --home ${APP_HOME} app \
    && mkdir -p ${APP_HOME}/user_dict \
    && chown -R app:app ${APP_HOME}

COPY --from=builder /install /usr/local
COPY app ./app
COPY README.md ./README.md

USER app

RUN useradd -r -s /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT} --workers ${UVICORN_WORKERS}"]
