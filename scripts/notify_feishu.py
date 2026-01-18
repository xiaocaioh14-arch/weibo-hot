#!/usr/bin/env python3
"""
飞书群机器人通知脚本 - 推送 Markdown 报告
"""

import json
import os
import sys
from pathlib import Path


def send_to_feishu(webhook_url: str, title: str, md_content: str, html_url: str = None):
    """发送 Markdown 内容到飞书"""
    import requests

    # 飞书 Markdown 最大长度约 40000 字符，截取部分内容
    max_length = 38000
    if len(md_content) > max_length:
        md_content = md_content[:max_length] + "\n\n...（内容过长，请查看完整报告）"

    # 构建按钮
    buttons = []
    if html_url:
        buttons.append({
            "tag": "button",
            "text": {"tag": "plain_text", "text": "📊 查看 HTML 报告"},
            "url": html_url,
            "type": "primary"
        })
    buttons.append({
        "tag": "button",
        "text": {"tag": "plain_text", "text": "📁 查看全部报告"},
        "url": "https://xiaocaioh14-arch.github.io/weibo-hot/"
    })

    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": "purple"
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": md_content}},
                {"tag": "action", "elements": buttons}
            ]
        }
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=30)
        result = response.json()
        if result.get("code") == 0:
            print("✅ 飞书通知发送成功")
            return True
        else:
            print(f"❌ 飞书通知失败: {result}")
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

    # 读取 Markdown 内容
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    title = f"📊 微博热搜分析报告 - {timestamp.replace('-', '/').replace('_', ' ')}"
    
    # 生成 HTML 报告 URL
    html_filename = Path(md_file).stem + ".html"
    html_url = f"https://xiaocaioh14-arch.github.io/weibo-hot/{html_filename}"

    send_to_feishu(webhook_url, title, md_content, html_url)

