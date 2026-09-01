# PaddleOCR-VL 可选部署

此目录提供独立的 PaddleOCR-VL 版面解析服务，不由 PolyOCR Service 主进程启动。

## 配置

复制示例环境变量并按部署环境填写：

```bash
cp .env.example .env
set -a
. ./.env
set +a
```

必填变量：

- `PADDLE_OCR_SERVER_HOST`：监听地址，例如 `0.0.0.0`
- `PADDLE_OCR_SERVER_PORT`：监听端口，例如 `8080`
- `VLM_SERVER_URL`：OpenAI 兼容的 VLM 推理端点

## 启动

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
./start_server.sh
```

启动脚本会在任何必填变量缺失时立即失败并打印变量名。模型服务可能需要 GPU，
请根据 PaddleOCR 与 PaddlePaddle 官方兼容矩阵选择依赖。
