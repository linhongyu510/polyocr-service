# PaddleOCR 生产环境部署指南

## 🚀 部署概述

以下示例假设服务运行在本机：

- **Web 界面**: http://localhost:8000
- **API 接口**: http://localhost:8000

## 📋 服务功能

### Web界面功能
- 📷 **图片OCR识别** - 支持中英文等多语言
- 📄 **PDF文档解析** - 表格、公式、图片识别
- 🌐 **智能翻译** - 多语言翻译功能
- 🔍 **拖拽上传** - 便捷的文件上传

### API接口功能
- 支持多语言OCR识别
- JSON和文本格式返回
- 批量处理能力
- 置信度过滤

## 🔑 认证方式

API调用需要认证，使用以下任一方式：

```bash
# 方式1: X-API-Key头
curl -H "X-API-Key: ${POLYOCR_API_KEY}" ...

# 方式2: Bearer Token
curl -H "Authorization: Bearer ${POLYOCR_API_KEY}" ...
```

## 📝 API使用示例

### 图片OCR识别
```bash
curl -X POST \
  -H "X-API-Key: ${POLYOCR_API_KEY}" \
  -F "file=@image.jpg" \
  -F "language=en" \
  http://localhost:8000/v1/ocr
```

### 支持的语言代码
- `zh`: 中文 (Chinese)
- `en`: 英文 (English)
- `ja`: 日文 (Japanese)
- `ko`: 韩文 (Korean)
- 更多语言请参考API文档

### 返回格式
```json
{
  "code": 0,
  "msg": "识别成功",
  "cost": 0.189,
  "tid": "task_id",
  "data": [
    {
      "text": "识别的文字",
      "bbox": [x1, y1, x2, y2]
    }
  ]
}
```

## 🛠️ 管理工具

### 部署脚本
```bash
# 部署/重启服务
./deploy_production.sh

# 检查服务状态
./check_status.sh
```

### 手动管理
```bash
# 查看服务状态
ps aux | grep -E "(frontend_server|start_backend)"

# 查看端口监听
netstat -tlnp | grep -E ":8000|:16110"

# 查看日志
tail -f logs/backend.log
tail -f logs/frontend.log

# 停止服务
pkill -f "python3.*start_backend.py"
pkill -f "python3.*frontend_server.py"
```

## 📊 性能参数

- **并发处理**: 支持多用户同时访问
- **响应时间**: 图片识别 < 0.5秒
- **支持格式**: JPG, PNG, BMP, PDF
- **文件大小限制**: 10MB (图片), 100MB (PDF)

## 🔧 故障排除

### 服务无法访问
1. 检查服务器网络连接
2. 确认端口8000和16110未被防火墙阻止
3. 查看服务日志确认服务正在运行

### API调用失败
1. 确认API密钥正确
2. 检查文件格式和大小
3. 查看返回的错误信息

### 识别效果不佳
1. 确保图片清晰度足够
2. 选择正确的语言模型
3. 尝试调整图像预处理选项

## 📞 技术支持

如遇到问题，请：
1. 查看日志文件获取详细错误信息
2. 使用 `./check_status.sh` 检查服务状态
3. 重新运行部署脚本 `./deploy_production.sh`

## 🔄 更新部署

当代码更新时，运行：
```bash
./deploy_production.sh
```

脚本会自动停止旧服务并启动新版本。

---

**部署时间**: $(date)  
**服务器地址**: 由部署者配置
**维护人员**: System Administrator
