#!/bin/bash
# PaddleOCR-VL 部署安装脚本

echo "开始安装 PaddleOCR-VL 部署环境..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "Python版本: $python_version"

# 创建虚拟环境（可选）
read -p "是否创建虚拟环境? (y/n): " create_venv
if [ "$create_venv" = "y" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "虚拟环境已激活"
fi

# 安装基础依赖
echo "安装基础依赖..."
pip install --upgrade pip

# 安装PaddlePaddle GPU版本
echo "安装 PaddlePaddle GPU..."
pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

# 安装PaddleOCR
echo "安装 PaddleOCR..."
pip install -U "paddleocr[doc-parser]"

# 安装safetensors
echo "安装 safetensors..."
pip install https://paddle-whl.bj.bcebos.com/nightly/cu126/safetensors/safetensors-0.6.2.dev0-cp38-abi3-linux_x86_64.whl

# 安装其他依赖
echo "安装其他依赖..."
pip install -r requirements.txt

# 检查GPU
echo "检查GPU状态..."
python3 -c "import paddle; print('PaddlePaddle版本:', paddle.__version__); print('GPU可用:', paddle.is_compiled_with_cuda())"

echo "安装完成！"
echo "启动服务请运行: python3 app.py"
echo "或使用: uvicorn app:app --host 0.0.0.0 --port 8080"
