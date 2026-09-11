# PolyOCR Service

[English](README_EN.md)

基于 PaddleOCR 3.x 的多语言 OCR、可选翻译和独立 PaddleOCR-VL 服务。此仓库是社区项目，
并非 PaddleOCR 官方组件。

## 能力与边界

- 基础 OCR 使用 PaddleOCR 3.x `predict()`，兼容 3.x 映射/对象结果和旧列表结果。
- 支持 78 种语言，覆盖汉字、日文、韩文、拉丁、西里尔、阿拉伯、天城文、泰文、希腊文等
  文字系统，并接受语种码、英文名和中文名三类别名（如 `fr` / `french` / `法文`）。
- 语言在请求边界完成校验：未知语言返回 `422 unsupported_language`，不会延迟到加载模型
  时才失败。
- 图片在推理前接受字节数、解码结果、像素数和置信度阈值校验。
- 同步模型推理在线程池执行，并由信号量限制并发。
- 翻译输入限制条目数和总字符数；供应商返回数量必须与输入一致。
- HTTP、认证、请求校验和领域错误使用统一 `error` 响应。
- PaddleOCR-VL 只接受上传内容，拒绝 URL，要求独立 API Key 并限制上传大小。
- 浏览器页面使用 `textContent` 渲染服务端结果，不把返回内容解释为 HTML。

快速单元测试不下载模型，也不访问公网。真实 OCR 会下载模型，仅在显式启用的集成测试中
运行。PaddleOCR-VL 需要单独准备兼容的 GPU、驱动、CUDA 和推理依赖。

## 安装

支持并由 CI 检查 Python 3.10、3.11 和 3.12。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,ocr]"
cp .env.example .env
```

修改 `.env` 中的 API Key 后启动：

```bash
# 仅本机访问（推荐用于本地开发）
polyocr-service

# 或用 uvicorn，显式指定监听地址
uvicorn polyocr.main:create_app --factory --host 127.0.0.1 --port 8000
```

命令行入口默认监听 `127.0.0.1:8000`，也可用 `POLYOCR_HOST` / `POLYOCR_PORT` 配置。

**关于监听地址**：`--host 0.0.0.0` 会把服务暴露在所有网络接口上。容器内需要这样做
（否则映射端口无法访问，Dockerfile 已显式这样配置），但在笔记本或共享网络上直接跑时，
它会让局域网内任何人都能访问你的实例。需要对外提供服务时再显式放开：

```bash
POLYOCR_HOST=0.0.0.0 polyocr-service        # 或 polyocr-service --host 0.0.0.0
```

兼容入口 `python main.py` 同样默认只监听 `127.0.0.1`。

访问 `http://localhost:8000/` 使用 Web 页面，API 文档位于 `/docs`。

## API

健康检查不要求认证：

```bash
curl http://localhost:8000/v1/health
```

查询支持的语言（返回语种码、PaddleOCR 语言码、文字系统和可用别名）：

```bash
curl http://localhost:8000/v1/languages
```

OCR 请求支持 `X-API-Key` 或 Bearer Token：

```bash
curl -X POST http://localhost:8000/v1/ocr \
  -H "X-API-Key: $POLYOCR_API_KEY" \
  -F "file=@benchmarks/simple_dataset/en.jpg" \
  -F "language=en" \
  -F "score_threshold=0.5"
```

`language` 接受语种码、英文名或中文名，响应中的 `language` 始终回显规范语种码：

```bash
curl -X POST http://localhost:8000/v1/ocr \
  -H "X-API-Key: $POLYOCR_API_KEY" \
  -F "file=@image.jpg" \
  -F "language=法文"      # 等价于 fr / french
```

成功响应：

```json
{
  "code": 0,
  "message": "Recognition succeeded.",
  "request_id": "...",
  "cost_ms": 412.7,
  "language": "fr",
  "items": [{"text": "Bonjour", "score": 0.99, "bbox": [12, 8, 96, 34]}]
}
```

翻译：

```bash
curl -X POST http://localhost:8000/v2/translate \
  -H "X-API-Key: $POLYOCR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"texts":["Hello"],"target_language":"zh"}'
```

失败响应统一为：

```json
{
  "error": {
    "code": "invalid_image",
    "message": "Uploaded file could not be decoded as an image.",
    "request_id": "..."
  }
}
```

## 配置

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `POLYOCR_AUTH_ENABLED` | `true` | 基础业务接口是否启用认证 |
| `POLYOCR_API_KEY` | 无 | 认证启用时必填 |
| `POLYOCR_CORS_ORIGINS` | `http://localhost:8000` | 逗号分隔的允许来源 |
| `POLYOCR_MAX_UPLOAD_MB` | `10` | OCR 上传字节上限 |
| `POLYOCR_MAX_IMAGE_PIXELS` | `25000000` | 解码后像素上限 |
| `POLYOCR_MAX_CONCURRENCY` | `2` | 同时运行的 OCR 推理数 |
| `POLYOCR_OCR_WORKERS` | `2` | OCR 工作线程数 |
| `POLYOCR_MAX_TRANSLATION_ITEMS` | `50` | 单次翻译条目上限 |
| `POLYOCR_MAX_TRANSLATION_CHARS` | `20000` | 单次翻译总字符上限 |
| `TRANSLATION_API_KEY` | 无 | OpenAI 兼容翻译服务密钥 |
| `TRANSLATION_BASE_URL` | OpenAI API | 翻译服务基址 |
| `TRANSLATION_MODEL` | `gpt-4o-mini` | 翻译模型 |
| `POLYOCR_VL_API_KEY` | 无 | 独立 VL 服务必填密钥 |
| `POLYOCR_VL_MAX_UPLOAD_MB` | `20` | VL 上传上限 |

项目会自动读取当前目录的 `.env`。不要提交 `.env` 或真实密钥。认证开启而
`POLYOCR_API_KEY` 为空时，基础服务拒绝启动；VL 服务始终要求 `POLYOCR_VL_API_KEY`。
带凭据的 CORS 配置不允许通配来源。

## Docker

```bash
export POLYOCR_API_KEY='replace-with-a-secret'
docker compose up --build
```

镜像固定 Python 3.10 基线，以非 root 用户运行并提供健康检查。首次 OCR 会下载模型，
模型缓存保存在 Compose volume。

## PaddleOCR-VL

可选部署说明见
[`deployment/paddleocr-vl/README.md`](deployment/paddleocr-vl/README.md)。
VL 接口不抓取远程 URL，调用者必须上传 base64 文件并携带独立认证信息。

## 测试与验证

```bash
python -m ruff format --check .
python -m ruff check .
python -m pytest -m "not integration"
python -m build
```

固定图片真实 OCR E2E：

```bash
POLYOCR_RUN_OCR_E2E=1 python -m pytest tests/integration/test_real_ocr.py -q
```

该命令可能下载模型。容器验证命令和本次实际结果记录在
[`docs/verification.md`](docs/verification.md)。CI 只运行不下载模型的快速测试，并在
Python 3.10–3.12 上执行。

### 语言准确率基准

按语言实测识别准确率，对照 `benchmarks/accuracy_dataset` 中带标注文本的图片：

```bash
# 只测指定语言（首次运行会下载对应模型）
python benchmarks/run_accuracy_benchmark.py --languages fr,de,ru

# 全部 32 种带标注语言
python benchmarks/run_accuracy_benchmark.py

# 也可对运行中的服务发起 HTTP 实测
python benchmarks/run_accuracy_benchmark.py --mode http --server http://localhost:8000
```

同时报告 `exact`（逐行完全匹配比例）和 `cer`（字符错误率），并且不受检测顺序影响。两个指标
都保留是因为单个易混字符就能把某行的 `exact` 打到 0，而 `cer` 能反映实际差距有多小。数据集
说明见 [`benchmarks/accuracy_dataset/README.md`](benchmarks/accuracy_dataset/README.md)。

### 鲁棒性基准

在受控退化（模糊 / 压缩 / 旋转 / 缩小 / 噪点 / 明暗对比，以及运动模糊 / 透视 / 不均匀光照 /
阴影 / 纸张纹理等拍摄类退化）下实测准确率：

```bash
python benchmarks/run_robustness_benchmark.py --languages en,fr,ru,zh
python benchmarks/run_robustness_benchmark.py --severity capture
python benchmarks/run_robustness_benchmark.py --compare-preprocess
```

实测结论：旋转、透视、JPEG 压缩、明暗对比、不均匀光照、阴影、纸张纹理几乎都不影响识别——
「透视 + 光照渐变 + 纹理 + 压缩」的组合拍照场景反而是满分。真正的失效只有**细节丢失**一类：
模糊超过约 σ2、缩小到 25% 以下。

**唯一需要警惕的是运动模糊**：15px 位移下会返回**置信度正常的错误文本**（`Hello World` →
`Heelco Ncotec`），而非空结果，调用方无法区分。9px 以内完全正常。

`preprocess` 参数**未实现**：五种预处理管线在全部 17 种退化上均为净负收益，自动对比度在
17 项里害了 11 项（软阴影 −0.517、纸张纹理 −0.450）。连专门针对不均匀光照的局部
`flatten`（除以模糊背景）也是负的——因为那些场景本来就有 0.975~1.000，没有提升空间只有
损失空间。因此 `preprocess=true` 返回 `400 preprocess_unsupported`，而不是静默忽略。
完整数据见 [`docs/robustness.md`](docs/robustness.md)。

### 真实照片基准

以上都是合成图。这一项用真实手机拍摄的票据（CORD-v2，CC-BY-4.0，带人工逐词标注）实测：

```bash
python benchmarks/run_photo_benchmark.py --limit 15 --compare-preprocess
```

| 指标 | 合成图 | 真实照片 |
| --- | --- | --- |
| 平均分 | 0.975 exact | **0.841 词召回** |

**合成图的分数偏乐观约 13 个点**——这是此前只作为「局限」声明、现在被量化的差距。15 张里
4 张全对、9 张 ≥0.727，1 张（褪色热敏纸）仅 0.250。

预处理在真实照片上有三种管线均值为**正**，看似要推翻结论，因此做了 bootstrap 检验：
**五种管线的 95% 置信区间全部跨越 0，p 值最小 0.371**。表现最好的 `combined`（+0.029）
去掉那 1 张离群图后变成 **−0.018**，且害了 15 张中的 6 张。结论因此维持，但依据更准确：
真实照片上预处理**没有统计上可检测的收益**。图片在运行时下载，不入库。

许可与归属：CORD-v2 数据集为 CC-BY-4.0，归属 NAVER CLOVA IX。

## 许可证

采用 [Apache License 2.0](LICENSE)，与上游 PaddleOCR 保持一致；第三方署名记录在
[`NOTICE`](NOTICE)。

本仓库是基于 PaddleOCR 构建的独立社区服务，并非 PaddleOCR 官方组件。PaddleOCR 模型在运行
时从其原始分发方下载，并受各自许可证与使用条款约束。
