# japanese-annotator (Python / sudachipy)

日语分词注音微服务 — 基于 **sudachipy**（Rust 引擎）+ **FastAPI**。

## 特性

- 使用 [sudachipy](https://github.com/WorksApplications/sudachi.rs)（Rust 实现，性能好）
- SudachiDict-full 词典，覆盖人名/地名/新词
- 支持 A/B/C 三种分词粒度
- 片假名读音自动转平假名输出
- 汉字级别精确 `<ruby>` 注音（送假名不包裹，如 `食べる` → `<ruby>食<rt>た</rt></ruby>べる`）
- 文本正规化（全角→半角、半角片假名→全角等）
- 支持自定义词典热重载（`user_dict/*.dic`）
- 提供适合 staging/production 的多阶段 Docker 镜像构建
- 提供 Aliyun ACR 镜像发布 GitHub Actions workflow

## 快速开始

### Docker（开发）

```bash
docker compose up --build
```

### 本地运行

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API

### POST /annotate

```json
// Request
{ "text": "東京都に住んでいます", "mode": "C", "pre_normalize": false }

// Response
{
  "tokens": [
    { "surface": "東京都", "reading": "とうきょうと", "lemma": "東京都", "pos": "名詞" },
    ...
  ],
  "ruby_html": "<ruby>東京都<rt>とうきょうと</rt></ruby>に<ruby>住<rt>す</rt></ruby>んでいます"
}
```

- **mode**: `A`（最小粒度）/ `B`（中间）/ `C`（最大，默认）
- **pre_normalize**: 分词前是否先正规化文本（默认 `false`）

### POST /annotate/batch

```json
{ "texts": ["東京都に住んでいます", "日本語を勉強しています"], "mode": "C", "pre_normalize": false }
```

### POST /normalize

文本正规化（全角数字/字母→半角、半角片假名→全角、CJK 间全角空格移除等）。

```json
// Request
{ "text": "０１２ＡＢＣ" }

// Response
{ "original": "０１２ＡＢＣ", "normalized": "012ABC" }
```

### POST /dict/reload

热重载 `user_dict/` 目录下的自定义词典（`.dic` 文件）。

### GET /health

```json
{ "status": "ok" }
```

## 自定义词典

将编译好的 `.dic` 文件放入 `user_dict/` 目录，然后调用 `/dict/reload` 生效。

在容器部署场景中，建议通过 volume 挂载到 `/app/user_dict`，而不是打包进镜像。

## Docker 镜像

当前 Dockerfile 使用多阶段构建：

- `builder` 阶段安装 Python 依赖（包括 `sudachidict_full`）
- `runtime` 阶段仅复制运行所需依赖和 `app/` 代码
- `user_dict` 目录在运行时创建，供 volume 挂载
- 默认以非 root 用户运行

本地构建：

```bash
docker build -t japanese-annotator:local .
```

本地运行镜像：

```bash
docker run --rm -p 8000:8000 \
  -e USER_DICT_DIR=/app/user_dict \
  -v $(pwd)/user_dict:/app/user_dict \
  japanese-annotator:local
```

## Staging 部署

仓库内提供了 staging compose 模板：

- `deploy/staging/docker-compose.yml`

推荐同步到 `IntelliFutureDeploy/japanese-annotator/staging/docker-compose.yml`。

默认约定：

- 外部暴露端口：`8100`
- 容器内部端口：`8000`
- 用户词典挂载目录：`/etc/japanese-annotator/user_dict`
- 镜像地址：`crpi-5s2sj3q8pm2yq2k6.cn-hongkong.personal.cr.aliyuncs.com/yomiya/japanese-annotator:staging`

## CI/CD

GitHub Actions workflow 位于：

- `.github/workflows/docker-build-push.yml`

默认行为：

- push 到 `main` 时发布 `staging`、`latest`、`sha-*` 标签
- push 到 `feat/sudachi-annotator` 时发布 `staging`、`sha-*` 标签
- 推送 `v*` tag 时发布版本标签
- 支持手动触发 `workflow_dispatch`

需要在 GitHub 仓库 Secrets 中配置：

- `ACR_USERNAME`
- `ACR_PASSWORD`

同时需要提前在阿里云 ACR 中创建仓库：

- `yomiya/japanese-annotator`
