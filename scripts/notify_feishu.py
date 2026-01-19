#!/usr/bin/env python3
"""
飞书群机器人通知脚本 - 推送微博热搜精简报告
修复：按钮前置显示 + 内容精简只保留 Top 3
"""

import json
import os
import re
import sys
from pathlib import Path


def create_short_content(full_content: str) -> str:
    """从完整 Markdown 中提取精简版内容（仅前 3 条详细分析）"""
    lines = full_content.split('\n')
    short_lines = []
    
    table_row_count = 0
    skip_until_next_section = False
    in_depth_section = False
    
    for line in lines:
        # 检测进入深度分析部分
        if line.startswith('## 🔍 深度分析'):
            in_depth_section = True
            short_lines.append(line)
            continue
        
        # 在深度分析部分，跳过第 4 条及之后
        if in_depth_section:
            # 匹配 "### 🥇 第 X 名" 格式
            match = re.match(r'^### .* 第 (\d+) 名', line)
            if match:
                rank = int(match.group(1))
                if rank >= 4:
                    skip_until_next_section = True
                else:
                    skip_until_next_section = False
        
        # 遇到趋势洞察或商业化章节，恢复输出
        if line.startswith('## 📈 趋势洞察') or line.startswith('## 💼 商业化'):
            in_depth_section = False
            skip_until_next_section = False
        
        if skip_until_next_section:
            continue
        
        # 表格只保留前 3 行数据
        if line.startswith('|'):
            if '排名' in line or '---' in line:
                short_lines.append(line)
            elif table_row_count < 3:
                short_lines.append(line)
                table_row_count += 1
            continue
        
        short_lines.append(line)
    
    result = '\n'.join(short_lines)
    return result


def send_to_feishu(webhook_url: str, title: str, md_content: str, html_url: str = None):
    """发送消息到飞书，按钮放在内容之前确保可见"""
    import requests

    # 严格限制内容长度（飞书卡片限制约 30000 字符）
    max_length = 8000  # 大幅缩短以确保按钮显示
    if len(md_content) > max_length:
        md_content = md_content[:max_length] + "\n\n...（更多内容请点击上方按钮查看完整报告）"

    # 构建按钮元素
    buttons = []
    if html_url:
        buttons.append({
            "tag": "button",
            "text": {"tag": "plain_text", "content": "📊 查看完整 HTML 报告"},
            "url": html_url,
            "type": "primary"
        })
    buttons.append({
        "tag": "button",
        "text": {"tag": "plain_text", "content": "📁 历史报告列表"},
        "url": "https://xiaocaioh14-arch.github.io/weibo-hot/",
        "type": "default"
    })

    # 卡片结构：按钮放在最前面，确保可见
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": "purple"
            },
            "elements": [
                # 1. 按钮放在最前面
                {
                    "tag": "action",
                    "actions": buttons
                },
                # 2. 分隔线
                {"tag": "hr"},
                # 3. 简要说明
                {
                    "tag": "note",
                    "elements": [
                        {"tag": "plain_text", "content": "👇 以下为 Top 3 热搜精简分析，完整报告请点击上方按钮"}
                    ]
                },
                # 4. Markdown 内容
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": md_content}
                }
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

    # 读取 Markdown 内容
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    # 生成精简版内容
    short_content = create_short_content(md_content)
    
    print(f"📄 原始内容长度: {len(md_content)} 字符")
    print(f"📄 精简后长度: {len(short_content)} 字符")

    title = f"📊 微博热搜 Top 10 分析 - {timestamp.replace('-', '/')}"
    
    # 生成 HTML 报告 URL
    html_filename = Path(md_file).stem + ".html"
    html_url = f"https://xiaocaioh14-arch.github.io/weibo-hot/{html_filename}"
    
    print(f"🔗 HTML 报告链接: {html_url}")

    send_to_feishu(webhook_url, title, short_content, html_url)

