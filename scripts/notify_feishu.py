#!/usr/bin/env python3
"""
飞书群机器人通知脚本 - 完整 Top 10 报告内嵌显示
无需外部网页链接，所有内容直接在飞书卡片中展示
"""

import json
import os
import re
import sys
from pathlib import Path


def format_for_feishu(md_content: str) -> str:
    """将 Markdown 内容格式化为飞书支持的格式"""
    # 移除标题中的 emoji 可能导致的问题
    content = md_content
    
    # 简化一些格式
    content = content.replace('---\n*由 Claude Agent SDK 自动生成*', '')
    content = content.replace('---', '───────')
    
    # 限制最大长度（飞书卡片限制约 30000 字符）
    max_length = 28000
    if len(content) > max_length:
        content = content[:max_length] + "\n\n...（内容已截断）"
    
    return content.strip()


def send_to_feishu(webhook_url: str, title: str, md_content: str):
    """发送完整报告到飞书，无外部链接"""
    import requests

    formatted_content = format_for_feishu(md_content)

    # 飞书卡片结构 - 纯内容展示，无按钮
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": "purple"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": formatted_content}
                }
            ]
        }
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=30)
        result = response.json()
        if result.get("code") == 0:
            print("✅ 飞书通知发送成功")
            print(f"📄 内容长度: {len(formatted_content)} 字符")
            return True
        else:
            print(f"❌ 飞书通知失败: {result}")
            print(f"响应详情: {json.dumps(result, ensure_ascii=False)}")
            return False
    except Exception as e:
        print(f"❌ 飞书通知异常: {e}")
        return False


if __name__ == "__main__":
    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        print("❌ 未设置 FEISHU_WEBHOOK_URL 环境变量")
        sys.exit(1)

    # 从命令行参数读取文件路径
    if len(sys.argv) < 3:
        print("用法: python notify_feishu.py <md_file_path> <timestamp>")
        sys.exit(1)

    md_file = sys.argv[1]
    timestamp = sys.argv[2]

    if not os.path.exists(md_file):
        print(f"❌ 文件不存在: {md_file}")
        sys.exit(1)

    # 读取完整 Markdown 内容
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    print(f"📄 原始内容长度: {len(md_content)} 字符")

    title = f"📊 微博热搜 Top 10 分析 - {timestamp.replace('-', '/')}"

    send_to_feishu(webhook_url, title, md_content)

