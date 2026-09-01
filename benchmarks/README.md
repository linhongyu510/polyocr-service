# 可复现的简单评测

`simple_dataset/` 包含每种示例语言一张固定图片及 manifest。先启动本地服务，再运行：

```bash
POLYOCR_API_KEY=change-me python benchmarks/run_simple_eval.py \
  --server http://localhost:8000 \
  --out /tmp/polyocr-simple-results.json
```

输出是运行时产物，不应提交。数据集可通过 `make_simple_dataset.py` 重新生成。
