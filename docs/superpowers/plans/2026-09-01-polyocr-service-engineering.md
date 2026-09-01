# PolyOCR Service Engineering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有 PaddleOCR 单体仓库改造成安全、可测试、可容器化、具有中英双语文档的 PolyOCR Service 开源作品集。

**Architecture:** 使用 `src/polyocr` 包承载 FastAPI 应用，API 层仅处理 HTTP 契约，服务层隔离模型与翻译供应商，核心层集中配置和认证。默认测试通过依赖注入使用假 OCR 引擎，不下载模型或访问网络；真实推理和 PaddleOCR-VL 作为显式可选路径。

**Tech Stack:** Python 3.10-3.12、FastAPI、Pydantic Settings、PaddleOCR、Pillow、httpx、pytest、Ruff、Docker、GitHub Actions

---

## 文件结构

新增或迁移后的主要文件及职责：

- `src/polyocr/main.py`：应用工厂、中间件、路由注册和静态站点挂载。
- `src/polyocr/core/config.py`：环境变量解析与跨字段安全校验。
- `src/polyocr/core/security.py`：API Key 认证依赖。
- `src/polyocr/api/errors.py`：统一错误类型与响应处理器。
- `src/polyocr/api/routes/*.py`：HTTP 接口。
- `src/polyocr/services/languages.py`：语言别名与 PaddleOCR 语言代码。
- `src/polyocr/services/model_manager.py`：线程安全模型缓存。
- `src/polyocr/services/ocr.py`：图片校验、推理和结果归一化。
- `src/polyocr/services/translation.py`：OpenAI 兼容翻译供应商。
- `src/polyocr/schemas/*.py`：公开响应模型。
- `web/`：不包含密钥或固定服务器地址的静态界面。
- `tests/unit/`：纯逻辑测试。
- `tests/api/`：使用假服务的 HTTP 契约测试。
- `deployment/paddleocr-vl/`：可选 GPU/VLM 部署。
- `docs/security.md`：凭据轮换与部署安全边界。
- `README.md`、`README_EN.md`：中文主文档和英文版。

### Task 1: 建立项目与测试骨架

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/polyocr/__init__.py`
- Create: `tests/test_package.py`

- [ ] **Step 1: 写包导入失败测试**

```python
# tests/test_package.py
from polyocr import __version__


def test_package_exposes_version() -> None:
    assert __version__ == "0.1.0"
```

- [ ] **Step 2: 验证测试因包不存在而失败**

Run: `python -m pytest tests/test_package.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'polyocr'`.

- [ ] **Step 3: 添加最小包和工程配置**

```python
# src/polyocr/__init__.py
__version__ = "0.1.0"
```

`pyproject.toml` 声明 `setuptools` 的 `src` 布局；运行依赖包含 FastAPI、Uvicorn、Pydantic Settings、python-multipart、Pillow、httpx，`ocr` 可选依赖包含 PaddlePaddle、PaddleOCR、OpenCV 和 NumPy，`dev` 包含 pytest、pytest-cov、Ruff。配置 pytest 的 `pythonpath = ["src"]`，Ruff 行长 100、目标 Python 3.10。

`.gitignore` 至少覆盖 `.env`、`.venv`、`__pycache__`、`*.pyc`、`*.log`、`.pytest_cache`、`.ruff_cache`、`htmlcov`、`dist`、模型缓存和生成报告。`.env.example` 只使用 `change-me`、`http://localhost` 等示例值。

- [ ] **Step 4: 安装最小开发依赖并运行测试**

Run: `python -m pip install -e ".[dev]" --break-system-packages`

Run: `python -m pytest tests/test_package.py -q`

Expected: `1 passed`.

- [ ] **Step 5: 提交骨架**

```bash
git add pyproject.toml .gitignore .env.example src/polyocr/__init__.py tests/test_package.py
git commit -m "build: add PolyOCR package skeleton"
```

### Task 2: 配置安全边界

**Files:**
- Create: `src/polyocr/core/__init__.py`
- Create: `src/polyocr/core/config.py`
- Create: `tests/unit/test_config.py`

- [ ] **Step 1: 写配置失败测试**

```python
import pytest
from pydantic import ValidationError

from polyocr.core.config import Settings


def test_auth_requires_non_placeholder_key() -> None:
    with pytest.raises(ValidationError):
        Settings(auth_enabled=True, api_key="")


def test_credentials_reject_wildcard_cors() -> None:
    with pytest.raises(ValidationError):
        Settings(cors_origins=["*"], cors_allow_credentials=True)


def test_translation_is_optional() -> None:
    settings = Settings(auth_enabled=False, translation_api_key=None)
    assert settings.translation_enabled is False
```

- [ ] **Step 2: 验证配置测试失败**

Run: `python -m pytest tests/unit/test_config.py -q`

Expected: FAIL because `polyocr.core.config` does not exist.

- [ ] **Step 3: 实现 Settings**

实现 `Settings(BaseSettings)`，使用 `env_prefix="POLYOCR_"`，字段包含 `auth_enabled`、`api_key`、`cors_origins`、`cors_allow_credentials`、`max_upload_mb`、`default_language`、`log_level`、`translation_api_key`、`translation_base_url`、`translation_model`。增加：

```python
@property
def translation_enabled(self) -> bool:
    return bool(self.translation_api_key)
```

使用 `model_validator(mode="after")` 拒绝启用认证但密钥为空，以及凭据模式下使用 `["*"]`。提供带 `lru_cache` 的 `get_settings()` 与测试用 `clear_settings_cache()`。

- [ ] **Step 4: 运行配置测试**

Run: `python -m pytest tests/unit/test_config.py -q`

Expected: `3 passed`.

- [ ] **Step 5: 提交配置**

```bash
git add src/polyocr/core tests/unit/test_config.py
git commit -m "feat: add validated environment settings"
```

### Task 3: 认证与统一错误契约

**Files:**
- Create: `src/polyocr/api/__init__.py`
- Create: `src/polyocr/api/errors.py`
- Create: `src/polyocr/core/security.py`
- Create: `src/polyocr/schemas/__init__.py`
- Create: `src/polyocr/schemas/common.py`
- Create: `tests/unit/test_security.py`

- [ ] **Step 1: 写认证与脱敏测试**

```python
from fastapi import HTTPException
import pytest

from polyocr.core.security import verify_api_key


def test_valid_api_key_is_accepted() -> None:
    assert verify_api_key("secret", "secret") is True


def test_invalid_api_key_is_rejected() -> None:
    assert verify_api_key("wrong", "secret") is False


def test_missing_key_raises_generic_error() -> None:
    with pytest.raises(HTTPException) as exc:
        verify_api_key(None, "secret", raise_error=True)
    assert exc.value.detail == "Missing or invalid API key."
```

- [ ] **Step 2: 验证测试失败**

Run: `python -m pytest tests/unit/test_security.py -q`

Expected: FAIL because `verify_api_key` is undefined.

- [ ] **Step 3: 实现认证和错误结构**

`verify_api_key` 使用 `secrets.compare_digest`。认证依赖同时读取 `Authorization: Bearer` 与 `X-API-Key`，认证关闭时直接放行。定义 `ServiceError(code, message, status_code)`，错误处理器返回：

```python
{"error": {"code": error.code, "message": error.message, "request_id": request_id}}
```

`schemas/common.py` 定义 `ErrorDetail`、`ErrorResponse` 和 `HealthResponse`。

- [ ] **Step 4: 运行测试与静态检查**

Run: `python -m pytest tests/unit/test_security.py -q`

Run: `python -m ruff check src/polyocr/core src/polyocr/api src/polyocr/schemas`

Expected: tests PASS and Ruff exits 0.

- [ ] **Step 5: 提交安全核心**

```bash
git add src/polyocr/api src/polyocr/core/security.py src/polyocr/schemas tests/unit/test_security.py
git commit -m "feat: add API key security boundary"
```

### Task 4: 语言注册表

**Files:**
- Create: `src/polyocr/services/__init__.py`
- Create: `src/polyocr/services/languages.py`
- Create: `tests/unit/test_languages.py`

- [ ] **Step 1: 写语言规范化测试**

```python
import pytest

from polyocr.api.errors import ServiceError
from polyocr.services.languages import normalize_language, supported_languages


@pytest.mark.parametrize(
    ("alias", "expected"),
    [("zh", "ch"), ("中文", "ch"), ("ja", "japan"), ("ko", "korean"), ("FR", "fr")],
)
def test_normalize_language(alias: str, expected: str) -> None:
    assert normalize_language(alias) == expected


def test_unknown_language_is_not_silently_fallback() -> None:
    with pytest.raises(ServiceError, match="Unsupported language"):
        normalize_language("not-a-language")


def test_language_list_has_unique_codes() -> None:
    codes = [item.code for item in supported_languages()]
    assert len(codes) == len(set(codes))
```

- [ ] **Step 2: 验证测试失败**

Run: `python -m pytest tests/unit/test_languages.py -q`

Expected: FAIL because language service does not exist.

- [ ] **Step 3: 实现唯一语言注册表**

定义不可变 `Language(code, paddle_code, name, aliases)`，先覆盖现有 UI 和测试实际使用的中文、英文、日文、韩文、法文、德文、西班牙文、葡萄牙文、俄文、泰文及拉丁语系。`normalize_language` 对 `strip().casefold()` 后的别名查表，未知值抛出 `ServiceError("unsupported_language", ..., 422)`。

- [ ] **Step 4: 运行测试**

Run: `python -m pytest tests/unit/test_languages.py -q`

Expected: all tests PASS.

- [ ] **Step 5: 提交语言服务**

```bash
git add src/polyocr/services tests/unit/test_languages.py
git commit -m "feat: normalize supported OCR languages"
```

### Task 5: OCR 结果归一化与上传校验

**Files:**
- Create: `src/polyocr/schemas/ocr.py`
- Create: `src/polyocr/services/ocr.py`
- Create: `tests/unit/test_ocr_service.py`

- [ ] **Step 1: 写纯逻辑失败测试**

测试以下输入：

```python
def test_normalizes_legacy_result() -> None:
    result = [[[[[0, 0], [10, 0], [10, 10], [0, 10]], ("hello", 0.98)]]]
    assert normalize_ocr_result(result, 0.5)[0].text == "hello"


def test_normalizes_mapping_result() -> None:
    result = [{"rec_texts": ["hello"], "rec_scores": [0.98], "dt_polys": [[[0, 0]]]}]
    assert normalize_ocr_result(result, 0.5)[0].score == 0.98


def test_rejects_invalid_threshold() -> None:
    with pytest.raises(ServiceError):
        normalize_ocr_result([], 1.1)


def test_rejects_broken_image() -> None:
    with pytest.raises(ServiceError, match="decode"):
        decode_image(b"not-an-image", max_bytes=1024)
```

- [ ] **Step 2: 验证测试失败**

Run: `python -m pytest tests/unit/test_ocr_service.py -q`

Expected: FAIL because OCR functions do not exist.

- [ ] **Step 3: 实现 OCR 数据边界**

`schemas/ocr.py` 定义 `OCRItem(text, score, bbox)` 和 `OCRResponse(code, message, request_id, cost_ms, language, items)`。`decode_image` 在解码前检查字节长度，使用 Pillow `verify()` 后重新打开并转 RGB；捕获解码异常并转换为 `ServiceError("invalid_image", ..., 422)`。

`normalize_ocr_result` 支持旧列表、Mapping 和带属性对象三种结果结构，过滤低于阈值的结果，将 NumPy-like 值通过 `tolist()` 转为列表，不吞掉结构错误。

- [ ] **Step 4: 运行单测**

Run: `python -m pytest tests/unit/test_ocr_service.py -q`

Expected: all tests PASS.

- [ ] **Step 5: 提交 OCR 边界**

```bash
git add src/polyocr/schemas/ocr.py src/polyocr/services/ocr.py tests/unit/test_ocr_service.py
git commit -m "feat: validate and normalize OCR inputs"
```

### Task 6: 模型管理器

**Files:**
- Create: `src/polyocr/services/model_manager.py`
- Create: `tests/unit/test_model_manager.py`

- [ ] **Step 1: 写缓存与错误传播测试**

```python
def test_same_paddle_code_reuses_model() -> None:
    factory = Mock(return_value=object())
    manager = ModelManager(factory)
    assert manager.get("zh") is manager.get("中文")
    factory.assert_called_once_with(lang="ch")


def test_load_failure_is_not_cached() -> None:
    factory = Mock(side_effect=[RuntimeError("boom"), object()])
    manager = ModelManager(factory)
    with pytest.raises(ServiceError, match="could not be loaded"):
        manager.get("en")
    assert manager.get("en") is not None
    assert factory.call_count == 2
```

- [ ] **Step 2: 验证测试失败**

Run: `python -m pytest tests/unit/test_model_manager.py -q`

Expected: FAIL because `ModelManager` does not exist.

- [ ] **Step 3: 实现线程安全缓存**

`ModelManager` 接收 `Callable[..., OCRBackend]` 工厂，以规范化后的 PaddleOCR 语言代码为唯一键，使用 `threading.RLock` 保护首次加载。工厂异常转换为 `ServiceError("model_unavailable", ..., 503)`，失败实例不进入缓存。

- [ ] **Step 4: 运行测试**

Run: `python -m pytest tests/unit/test_model_manager.py -q`

Expected: all tests PASS.

- [ ] **Step 5: 提交模型管理**

```bash
git add src/polyocr/services/model_manager.py tests/unit/test_model_manager.py
git commit -m "feat: add consistent OCR model cache"
```

### Task 7: FastAPI 应用和 OCR 接口

**Files:**
- Create: `src/polyocr/api/dependencies.py`
- Create: `src/polyocr/api/routes/__init__.py`
- Create: `src/polyocr/api/routes/health.py`
- Create: `src/polyocr/api/routes/languages.py`
- Create: `src/polyocr/api/routes/ocr.py`
- Create: `src/polyocr/main.py`
- Create: `tests/api/conftest.py`
- Create: `tests/api/test_core_api.py`

- [ ] **Step 1: 写无模型 HTTP 契约测试**

测试 `GET /v1/health` 返回 `{"status":"ok","service":"PolyOCR Service"}`；未认证访问 `/v1/ocr` 返回 401；假 OCR 服务接收有效 PNG 后返回 `items`；损坏图片返回 `invalid_image` 且含 `request_id`。

- [ ] **Step 2: 验证 API 测试失败**

Run: `python -m pytest tests/api/test_core_api.py -q`

Expected: FAIL because `create_app` does not exist.

- [ ] **Step 3: 实现应用工厂和路由**

实现：

```python
def create_app(
    settings: Settings | None = None,
    ocr_service: OCRService | None = None,
) -> FastAPI:
    ...
```

注册请求 ID 中间件、显式 CORS、错误处理器和路由。`POST /v1/ocr` 接收 `UploadFile`、`language`、`score_threshold` 与 `preprocess`，读取时限制 `max_upload_mb + 1` 字节，认证依赖只挂载在受保护业务端点。

- [ ] **Step 4: 运行 API 与全量快速测试**

Run: `python -m pytest tests/api/test_core_api.py -q`

Run: `python -m pytest -q`

Expected: all tests PASS without model download.

- [ ] **Step 5: 提交基础 API**

```bash
git add src/polyocr/api src/polyocr/main.py tests/api
git commit -m "feat: expose tested OCR API"
```

### Task 8: 可选翻译服务

**Files:**
- Create: `src/polyocr/schemas/translation.py`
- Create: `src/polyocr/services/translation.py`
- Create: `src/polyocr/api/routes/translation.py`
- Create: `tests/unit/test_translation_service.py`
- Create: `tests/api/test_translation_api.py`

- [ ] **Step 1: 写翻译关闭与供应商错误测试**

```python
def test_missing_translation_config_is_explicit(client) -> None:
    response = client.post("/v2/translate", json={"texts": ["hello"], "target_language": "zh"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "translation_not_configured"


async def test_provider_error_is_redacted() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(401, json={"error": "secret upstream body"})
    )
    service = TranslationService(settings, transport=transport)
    with pytest.raises(ServiceError) as exc:
        await service.translate(["hello"], "zh")
    assert "secret upstream body" not in str(exc.value)
```

- [ ] **Step 2: 验证测试失败**

Run: `python -m pytest tests/unit/test_translation_service.py tests/api/test_translation_api.py -q`

Expected: FAIL because translation service and route do not exist.

- [ ] **Step 3: 实现 OpenAI 兼容翻译适配器**

请求只发送文本、目标语言和固定系统提示。设置连接、读取和总超时；上游非成功状态统一映射为 `translation_provider_error`，日志仅记录状态码和请求 ID。保留 `/v1/translation/translate` 与 `/v2/translate` 两个兼容入口，均不得返回配置或密钥。

- [ ] **Step 4: 运行翻译和全量测试**

Run: `python -m pytest tests/unit/test_translation_service.py tests/api/test_translation_api.py -q`

Run: `python -m pytest -q`

Expected: all tests PASS without network access.

- [ ] **Step 5: 提交翻译模块**

```bash
git add src/polyocr/schemas/translation.py src/polyocr/services/translation.py src/polyocr/api/routes/translation.py tests
git commit -m "feat: add optional translation provider"
```

### Task 9: 迁移和脱敏 Web 界面

**Files:**
- Create: `web/index.html`
- Create: `web/translation.html`
- Modify: `src/polyocr/main.py`
- Create: `tests/test_repository_hygiene.py`
- Remove: `index.html`
- Remove: `translation.html`
- Remove: `frontend_server.py`

- [ ] **Step 1: 写仓库卫生失败测试**

测试扫描被 Git 跟踪的文本文件，禁止出现已发现的两个真实密钥、两个公网 IP、内网 IP，以及前端中的绝对 `http://.../v1` 请求；允许 `.env.example` 的 localhost 示例。

- [ ] **Step 2: 验证测试在旧文件上失败**

Run: `python -m pytest tests/test_repository_hygiene.py -q`

Expected: FAIL and list current hard-coded files.

- [ ] **Step 3: 迁移前端并改为相对请求**

将页面品牌改为 PolyOCR Service。OCR 使用 `fetch("/v1/ocr", ...)`，翻译使用 `fetch("/v2/translate", ...)`。API Key 仅从密码输入框读取并放入当次请求 Header，不写入 localStorage、sessionStorage、Cookie 或源码。

由 `main.py` 在 `/` 返回 `web/index.html`，静态文件挂载到 `/static`。删除独立前端服务器。

- [ ] **Step 4: 运行卫生与 API 测试**

Run: `python -m pytest tests/test_repository_hygiene.py tests/api -q`

Expected: all tests PASS.

- [ ] **Step 5: 提交 Web 迁移**

```bash
git add web src/polyocr/main.py tests/test_repository_hygiene.py
git rm index.html translation.html frontend_server.py
git commit -m "refactor: serve sanitized PolyOCR web UI"
```

### Task 10: 整理测试、基准和 VL 部署

**Files:**
- Move: `paddleocr_vl_deployment/` to `deployment/paddleocr-vl/`
- Create: `deployment/paddleocr-vl/.env.example`
- Modify: `deployment/paddleocr-vl/config.yaml`
- Modify: `deployment/paddleocr-vl/README.md`
- Modify: `benchmarks/run_simple_eval.py`
- Create: `benchmarks/README.md`
- Remove: `accuracy_test/reports/`
- Remove: `accuracy_test/results/`
- Remove: tracked logs, caches, duplicate root test images and generated benchmark outputs

- [ ] **Step 1: 扩展仓库卫生测试**

增加断言：跟踪文件不以 `.log`、`.pyc` 结尾；不存在 `__pycache__`；生成报告目录不被跟踪；VL 配置不包含固定 IP。

- [ ] **Step 2: 验证新增断言失败**

Run: `python -m pytest tests/test_repository_hygiene.py -q`

Expected: FAIL and identify generated artifacts.

- [ ] **Step 3: 清理并参数化**

使用 `git mv` 迁移 VL 目录。`config.yaml` 使用 `${PADDLE_OCR_SERVER_HOST}`、`${VLM_SERVER_URL}` 等环境占位，启动脚本在缺失必要变量时失败并给出变量名。

基准脚本默认 `--server http://localhost:8000`，API Key 通过 `POLYOCR_API_KEY` 读取。只保留 `benchmarks/simple_dataset`、manifest、生成脚本和复现说明；删除无法由当前命令追溯的结果。

- [ ] **Step 4: 运行卫生测试和 Shell 语法检查**

Run: `python -m pytest tests/test_repository_hygiene.py -q`

Run: `bash -n deployment/paddleocr-vl/*.sh`

Expected: all checks PASS.

- [ ] **Step 5: 提交仓库清理**

```bash
git add -A
git commit -m "chore: clean deployment and benchmark artifacts"
```

### Task 11: Docker 与 CI

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`
- Create: `docker-compose.yml`
- Create: `.github/workflows/ci.yml`
- Create: `tests/api/test_container_contract.py`

- [ ] **Step 1: 写容器入口契约测试**

读取 Dockerfile 并断言包含非 root `USER`、`polyocr.main:create_app` 的工厂启动参数和 `/v1/health` 健康检查；读取 Compose 并断言密钥来自环境变量而非字面量。

- [ ] **Step 2: 验证测试失败**

Run: `python -m pytest tests/api/test_container_contract.py -q`

Expected: FAIL because container files do not exist.

- [ ] **Step 3: 实现 CPU 容器和 CI**

Dockerfile 使用已验证的 Python slim 版本，创建 `polyocr` 用户，安装基础包和 `.[ocr]`，执行：

```dockerfile
CMD ["uvicorn", "polyocr.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

Compose 传递 `POLYOCR_API_KEY`，持久化模型缓存，不写默认真实密钥。CI 依次运行 `ruff format --check .`、`ruff check .`、`pytest -q`、仓库卫生测试和 `docker build`。

- [ ] **Step 4: 本地验证**

Run: `python -m pytest tests/api/test_container_contract.py -q`

Run: `python -m ruff format --check . && python -m ruff check . && python -m pytest -q`

Run: `docker build -t polyocr-service:test .`

Expected: tests and Ruff PASS; Docker build exits 0. If Docker daemon unavailable, record the exact environment limitation and do not claim build success.

- [ ] **Step 5: 提交工程门禁**

```bash
git add Dockerfile .dockerignore docker-compose.yml .github tests/api/test_container_contract.py
git commit -m "ci: add container and quality gates"
```

### Task 12: 中英文 README 与安全文档

**Files:**
- Create: `README.md`
- Create: `README_EN.md`
- Create: `docs/security.md`
- Create: `docs/architecture.md`
- Create: `docs/assets/architecture.svg`
- Modify: `README_DEPLOYMENT.md` or remove it after content migration
- Modify: `README_benchmark.md` or remove it after content migration

- [ ] **Step 1: 写文档链接与命令测试**

新增测试读取两个 README，断言它们互相链接、包含非官方声明、仅引用存在文件、没有真实 IP/密钥、快速启动命令与 `pyproject.toml` 和 Docker 配置一致。

- [ ] **Step 2: 验证测试失败**

Run: `python -m pytest tests/test_documentation.py -q`

Expected: FAIL because root READMEs do not exist.

- [ ] **Step 3: 编写中文主 README**

首屏使用 **PolyOCR Service**、`Powered by PaddleOCR`、语言切换和 CI/Python/License 徽章。依次写入：效果预览、真实能力、架构图、安装矩阵、CPU Docker、本地启动、OCR 示例、翻译示例、配置、安全、测试、基准、VL 部署、路线图、贡献、许可证与致谢。

没有许可证文件时不得显示 License 徽章或擅自选择许可证；先在 README 标注“许可证待仓库所有者确认”，并把添加许可证列入发布前检查。

- [ ] **Step 4: 编写等价英文版和配套文档**

`README_EN.md` 与中文版本结构一致，不是摘要版。`docs/security.md` 明确要求立即轮换已泄露凭据，并说明当前树清理不等于历史清理。`docs/architecture.md` 解释基础 OCR、可选翻译与 VL 服务边界。

- [ ] **Step 5: 运行文档与全量验证**

Run: `python -m pytest tests/test_documentation.py -q`

Run: `python -m ruff format --check . && python -m ruff check . && python -m pytest -q`

Expected: all checks PASS.

- [ ] **Step 6: 提交文档**

```bash
git add README.md README_EN.md docs tests/test_documentation.py
git rm README_DEPLOYMENT.md README_benchmark.md
git commit -m "docs: publish PolyOCR project guides"
```

### Task 13: 最终真实验证与发布检查

**Files:**
- Modify only files required by discovered failures
- Create: `docs/verification.md`

- [ ] **Step 1: 在纯净环境验证快速路径**

Run: `python -m venv /tmp/polyocr-verify && /tmp/polyocr-verify/bin/pip install -e ".[dev]" && /tmp/polyocr-verify/bin/pytest -q`

Expected: installation succeeds and all fast tests PASS without model download.

- [ ] **Step 2: 验证应用导入和未配置翻译状态**

Run: `POLYOCR_AUTH_ENABLED=false /tmp/polyocr-verify/bin/python -c "from polyocr.main import create_app; assert create_app().title == 'PolyOCR Service'"`

Expected: exits 0.

- [ ] **Step 3: 执行静态与秘密扫描**

Run: `/tmp/polyocr-verify/bin/ruff format --check . && /tmp/polyocr-verify/bin/ruff check .`

Run: `/tmp/polyocr-verify/bin/pytest tests/test_repository_hygiene.py -q`

Expected: all checks PASS and no known credential/IP pattern is found in the current tree.

- [ ] **Step 4: 执行可用环境允许的集成验证**

Run: `docker build -t polyocr-service:verify .`

若当前架构支持 PaddlePaddle，再运行带 `integration` 标记的单张固定图片测试；若不支持，记录平台、失败命令和原因，不将其写成通过。

- [ ] **Step 5: 写验证记录**

`docs/verification.md` 记录提交 SHA、Python 版本、操作系统、每条命令及真实结果。性能数字只有实际运行固定基准后才添加；否则明确写“本次未执行性能基准”。

- [ ] **Step 6: 最终提交**

```bash
git add docs/verification.md
git commit -m "docs: record PolyOCR verification evidence"
```

## 发布前人工事项

- 在第三方服务侧撤销并轮换仓库曾暴露的 API Key 与 Secret。
- 确认是否需要使用 `git filter-repo` 重写公开历史；该操作不得在本计划中自动执行。
- 由仓库所有者选择并添加许可证，未确认前不宣称特定开源许可证。
- 审阅删除的历史报告是否需要在仓库外归档。
- 完成后先推送改造分支并创建 Draft PR，不直接强推 `main`。
