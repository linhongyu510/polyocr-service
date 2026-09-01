# 架构说明

PolyOCR Service 将稳定的 HTTP 边界、基础 OCR 推理和可选外部能力分开。主应用可以在
未配置翻译和 VL 服务时独立启动，健康检查也不会触发模型下载。

## 主 API

`src/polyocr/main.py` 创建 FastAPI 应用，注册请求 ID、中间件、错误处理器和版本化路由。
认证边界接受 `X-API-Key` 或 Bearer Token，并使用常量时间比较。OCR 路由负责验证上传，
`OCRService` 规范化后端结果，`ModelManager` 按语言缓存模型实例。

## 翻译边界

翻译是可选的 OpenAI 兼容适配器。服务只发送文本、目标语言和固定系统提示；缺少配置时
明确返回 `translation_not_configured`。上游错误被映射为稳定的服务错误，不透传响应正文。
测试使用 `httpx.MockTransport`，不会访问真实供应商。

## VL 边界

`deployment/paddleocr-vl/` 是独立部署单元，不参与主应用启动。它通过环境变量获取监听
地址和 VLM 端点，适合需要版面解析或视觉语言模型的 GPU 环境。主 API 不代理 VL 请求，
两个服务可分别扩缩容和保护。

## 数据流

1. 客户端向主 API 提交认证头和图片。
2. API 验证大小、格式、语言和请求参数。
3. 模型管理器复用对应语言的 OCR 后端。
4. 服务返回规范化文本、置信度、边界框、耗时和请求 ID。
5. 翻译或 VL 请求只在调用各自入口并完成独立配置时离开主进程。

架构图见 [architecture.svg](assets/architecture.svg)。
