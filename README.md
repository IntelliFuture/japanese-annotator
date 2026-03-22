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

## 快速开始

### Docker（推荐）

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
