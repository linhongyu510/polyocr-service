# PolyOCR 基准评测（基于 16110 API）

目录结构在 `benchmarks/`，覆盖下载数据、运行测试与评估汇总，优先东亚/东南亚语言。

运行：

```bash
python3 benchmarks/download_datasets.py
POLYOCR_API_KEY=change-me python3 benchmarks/run_simple_eval.py --server http://localhost:8000 --score 0.5
python3 benchmarks/evaluate_results.py --results benchmarks/results
```

注意：所有文件使用 UTF-8 编码，评估时按语言独立统计，避免编码问题。

