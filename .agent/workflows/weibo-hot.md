---
description: 分析微博热搜 Top 10，生成深度分析报告
---

# 微博热搜分析工作流

// turbo-all

## 步骤

1. 运行 Python 脚本获取微博热搜数据
```bash
python /Users/wyw/Project/微博热搜分析/.agent/skills/weibo-hot-analyzer/scripts/fetch_weibo_hot.py --json
```

2. 读取 skill 文档获取分析指令
```
查看 /Users/wyw/Project/微博热搜分析/.agent/skills/weibo-hot-analyzer/SKILL.md
```

3. 按照 SKILL.md 中的分析维度，对 Top 10 热搜进行深度分析

4. 创建输出目录
```bash
mkdir -p weibo-hot-reports
```

5. 生成 HTML 和 Markdown 双格式报告，保存到 `weibo-hot-reports/` 目录

6. 输出报告摘要和文件链接
