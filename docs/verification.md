# 验证记录

## 环境

- 验证日期：2026-09-01
- 验证源码提交：`12b1cc8066dcd0a66dfc92ded739838fbef8b6ef`
- 主机：macOS 26.5.1（Build 25F80），arm64
- 主机 Python：3.10.20
- 容器 Python：3.12 slim，Linux arm64

最终验证后的提交还包含安装包 Web 资源修复和本记录，因此其 SHA 以 Git 历史为准。

## 自动化测试与静态检查

```text
python -m ruff format --check .
39 files already formatted

python -m ruff check .
All checks passed!

python -m pytest -q
35 passed in 0.60s

python -m pytest tests/test_repository_hygiene.py -q
2 passed in 0.13s
```

卫生测试扫描 Git 跟踪的文本文件，禁止已知泄露凭据、部署 IP、绝对 HTTP v1 请求、
`.log`、`.pyc`、`__pycache__` 和历史生成报告目录。

## TDD 证据

- Task 9：卫生测试首次运行失败，列出旧 Web 页面中的固定凭据、部署地址和绝对请求；
  迁移后卫生与 API 测试 `7 passed`。
- Task 10：扩展卫生测试后两项均失败，分别列出 45 个敏感值命中和 30 个生成产物；
  清理、迁移和参数化后 `2 passed`，VL Shell 脚本通过 `bash -n`。
- Task 11：容器契约测试因 Dockerfile 和 Compose 不存在而得到 `2 failed`；实现后
  契约测试通过，全量测试为 `32 passed`。
- Task 12：文档测试因中英文 README 不存在而得到 `2 failed, 1 passed`；文档完成后
  为 `3 passed`，全量测试为 `35 passed`。
- Task 13：已安装容器中的应用导入最初因 Web 资源未打包而失败；将页面作为
  `polyocr` 包数据后，同一容器导入命令退出码为 0。

## 容器

```text
docker build -t polyocr-service:test .
exit 0

docker build -t polyocr-service:verify .
exit 0

docker run --rm -e POLYOCR_AUTH_ENABLED=false --entrypoint python \
  polyocr-service:verify -c \
  "from polyocr.main import create_app; assert create_app().title == 'PolyOCR Service'"
container import ok
```

Docker 在本机可用，两次镜像构建均成功。构建安装 `.[ocr]`，但未启动 OCR 模型下载或
调用任何翻译/VL 服务。

## 纯净虚拟环境限制

计划中的主机命令未能形成可信的隔离环境。TRAE 运行环境预设了 `PYTHONHOME` 和
`PYTHONPATH`，创建出的 `/tmp/polyocr-verify` 会把共享工具目录注入 `sys.path`：

```text
python -m venv /tmp/polyocr-verify
/tmp/polyocr-verify/bin/pip: No such file or directory
```

使用 `uv venv --seed` 后，pip 仍把依赖解析到共享工具目录；测试可运行，但独立
`from polyocr.main import create_app` 返回 `ModuleNotFoundError`，因此不把主机 venv
记为通过。作为隔离替代证据，Docker 镜像从 Python slim 安装构建产物，随后应用导入
成功。

## 集成与性能

`python -m pytest --collect-only -m integration -q` 返回退出码 5：
`no tests collected (35 deselected)`。当前仓库没有带 `integration` 标记的固定图片测试，
因此未执行真实模型推理，也未声称 OCR 集成通过。

本次未执行性能基准。

## 发布前仍需人工处理

- 在第三方服务侧撤销并轮换历史中出现过的所有凭据。
- 决定是否用 `git filter-repo` 重写公开历史；当前树清理不等于历史清理。
- 由仓库所有者选择许可证，未确认前不得宣称具体许可证。
- 审阅历史生成报告是否需要在仓库外归档。
