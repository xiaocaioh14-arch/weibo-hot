# 微博 API 配置说明

## API Key 配置

当前已配置的 API Key：
```
84312028a068cdebe51762a507a935cc
```

## API 端点

### 主要端点
```
https://weibo.com/ajax/side/hotSearch
```

### 备用端点
```
https://tenapi.cn/v2/weibohot
```

## 使用方式

API Key 已直接写入 `scripts/fetch_weibo_hot.py` 脚本中。如需更新：

1. 打开 `scripts/fetch_weibo_hot.py`
2. 找到 `WEIBO_API_KEY` 变量
3. 替换为新的 API Key

## 注意事项

- 请勿将 API Key 提交到公开仓库
- API 调用有频率限制，建议间隔 1 分钟以上
- 如主 API 不可用，脚本会自动切换到备用 API
