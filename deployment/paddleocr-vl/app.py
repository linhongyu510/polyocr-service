#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PaddleOCR-VL 服务化部署应用
支持图像和PDF文档的版面解析
"""

import os
import json
import base64
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from io import BytesIO

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image

try:
    from paddleocr import PaddleOCRVL
except ImportError:
    print("警告: 未安装PaddleOCR，请先安装依赖")
    PaddleOCRVL = None

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载配置
config_path = Path(__file__).parent / "config.yaml"
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(os.path.expandvars(f.read()))

# 创建FastAPI应用
app = FastAPI(
    title="PaddleOCR-VL API",
    description="PaddleOCR-VL 版面解析服务",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加静态文件服务
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# 全局变量
pipeline = None

class LayoutParsingRequest(BaseModel):
    file: str  # Base64编码的文件内容或URL
    fileType: Optional[int] = None  # 0=PDF, 1=图像
    useDocUnwarping: Optional[bool] = None
    useLayoutDetection: Optional[bool] = None
    useChartRecognition: Optional[bool] = None
    visualize: Optional[bool] = None
    prettifyMarkdown: Optional[bool] = None
    showFormulaNumber: Optional[bool] = None

class LayoutParsingResponse(BaseModel):
    logId: str
    errorCode: int
    errorMsg: str
    result: Dict[str, Any]

def init_pipeline():
    """初始化PaddleOCR-VL管道"""
    global pipeline
    if PaddleOCRVL is None:
        raise RuntimeError("PaddleOCR未正确安装")
    
    try:
        # 使用配置文件中的参数初始化
        pipeline = PaddleOCRVL(
            use_doc_orientation_classify=config['model']['use_doc_orientation_classify'],
            use_doc_unwarping=config['model']['use_doc_unwarping'],
            use_layout_detection=config['model']['use_layout_detection'],
            use_chart_recognition=config['model']['use_chart_recognition'],
            vl_rec_backend=config['inference']['backend'],
            vl_rec_server_url=config['inference']['server_url']
        )
        logger.info("PaddleOCR-VL管道初始化成功")
    except Exception as e:
        logger.error(f"PaddleOCR-VL管道初始化失败: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    try:
        init_pipeline()
        logger.info("服务启动成功")
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        raise

@app.get("/")
async def root():
    """根路径 - 返回前端页面"""
    return FileResponse(Path(__file__).parent / "static" / "index.html")

@app.get("/api/info")
async def api_info():
    """API信息"""
    return {"message": "PaddleOCR-VL API 服务运行中"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "pipeline_ready": pipeline is not None}

@app.post("/layout-parsing", response_model=LayoutParsingResponse)
async def layout_parsing(request: LayoutParsingRequest):
    """
    版面解析接口
    """
    try:
        if pipeline is None:
            raise HTTPException(status_code=500, detail="PaddleOCR-VL管道未初始化")
        
        # 处理文件输入
        if request.file.startswith('http'):
            # URL输入
            input_path = request.file
        else:
            # Base64输入
            try:
                file_data = base64.b64decode(request.file)
                # 保存临时文件
                temp_path = f"/tmp/temp_input_{hash(request.file) % 10000}"
                with open(temp_path, 'wb') as f:
                    f.write(file_data)
                input_path = temp_path
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"文件解码失败: {e}")
        
        # 执行推理
        output = pipeline.predict(input_path)
        
        # 处理结果
        layout_parsing_results = []
        for i, res in enumerate(output):
            # 构建响应
            result_item = {
                "prunedResult": {
                    "layout": res.layout if hasattr(res, 'layout') else [],
                    "text": res.text if hasattr(res, 'text') else "",
                    "markdown": res.markdown if hasattr(res, 'markdown') else {}
                },
                "markdown": {
                    "text": res.markdown.get('text', '') if hasattr(res, 'markdown') else '',
                    "images": res.markdown.get('images', {}) if hasattr(res, 'markdown') else {},
                    "isStart": i == 0,
                    "isEnd": i == len(output) - 1
                },
                "outputImages": {},
                "inputImage": None
            }
            
            # 处理输出图像
            if hasattr(res, 'img') and res.img:
                try:
                    img_buffer = BytesIO()
                    res.img.save(img_buffer, format='JPEG')
                    img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                    result_item["outputImages"]["result"] = img_base64
                except Exception as e:
                    logger.warning(f"处理输出图像失败: {e}")
            
            # 处理输入图像
            if request.fileType == 1:  # 图像文件
                try:
                    with open(input_path, 'rb') as f:
                        input_img_data = f.read()
                    input_img_base64 = base64.b64encode(input_img_data).decode('utf-8')
                    result_item["inputImage"] = input_img_base64
                except Exception as e:
                    logger.warning(f"处理输入图像失败: {e}")
            
            layout_parsing_results.append(result_item)
        
        # 清理临时文件
        if not request.file.startswith('http') and os.path.exists(input_path):
            os.remove(input_path)
        
        # 构建响应
        response_data = {
            "logId": f"req_{hash(str(request)) % 100000}",
            "errorCode": 0,
            "errorMsg": "Success",
            "result": {
                "layoutParsingResults": layout_parsing_results,
                "dataInfo": {
                    "inputType": "image" if request.fileType == 1 else "pdf",
                    "totalPages": len(layout_parsing_results)
                }
            }
        }
        
        return response_data
            
    except Exception as e:
        logger.error(f"版面解析失败: {e}")
        return {
            "logId": f"req_{hash(str(request)) % 100000}",
            "errorCode": 500,
            "errorMsg": f"处理失败: {str(e)}",
            "result": {}
        }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    文件上传接口
    """
    try:
        # 读取文件内容
        content = await file.read()
        
        # 转换为Base64
        file_base64 = base64.b64encode(content).decode('utf-8')
        
        # 判断文件类型
        file_type = 0 if file.filename.lower().endswith('.pdf') else 1
        
        return {
            "success": True,
            "file_base64": file_base64,
            "file_type": file_type,
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {e}")

if __name__ == "__main__":
    # 启动服务
    uvicorn.run(
        "app:app",
        host=config['server']['host'],
        port=config['server']['port'],
        reload=False,
        log_level="info"
    )
