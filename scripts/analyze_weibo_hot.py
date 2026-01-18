#!/usr/bin/env python3
"""
微博热搜分析主脚本
使用 Claude Agent SDK 进行深度分析
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / ".agent" / "skills" / "weibo-hot-analyzer" / "scripts"))

from anthropic import Anthropic
from fetch_weibo_hot import fetch_weibo_hot_search, format_hot_value

# 配置
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "")  # 第三方 API 地址
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")  # 模型名称
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
OUTPUT_DIR = Path("weibo-hot-reports")


def get_claude_analysis(client, topics: list) -> str:
    """调用 Claude 进行深度分析"""
    # 构建话题列表
    topics_text = "\n".join([
        f"{t['rank']}. [{t['category']}] {t['title']} (热度: {format_hot_value(t['hot_value'])})"
        for t in topics
    ])

    prompt = f"""请对以下微博热搜 Top 10 进行深度分析，生成商业化洞察报告。

## 热搜话题
{topics_text}

## 分析要求
对每条热搜输出以下内容：
1. **核心摘要** (50-100字)
2. **关键要点** (3-5个核心信息点)
3. **商业化洞察** (品牌营销、电商选品、内容创作、广告投放、IP衍生等机会，或"无明显商业化机会")

## 整体分析
最后提供：
- 热搜趋势洞察
- 商业化机会汇总

## 输出格式
请以 JSON 格式输出，结构如下：
{{
    "analyses": [
        {{
            "rank": 1,
            "title": "话题标题",
            "category": "分类",
            "summary": "核心摘要",
            "key_points": ["要点1", "要点2", "要点3"],
            "commercial": "商业化洞察"
        }}
    ],
    "trend_insight": "趋势洞察分析",
    "commercial_summary": "商业化机会汇总"
}}

只输出 JSON，不要有其他内容。"""

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    # 兼容 MiniMax 等第三方 API 的不同返回格式
    content = response.content
    if isinstance(content, list) and len(content) > 0:
        first_item = content[0]
        # 检查是否有 text 属性（标准 Anthropic 格式）
        if hasattr(first_item, 'text'):
            return first_item.text
        # 检查是否有 thinking 属性（MiniMax ThinkingBlock）
        elif hasattr(first_item, 'thinking') and first_item.thinking:
            # 尝试从第二个 item 获取文本
            if len(content) > 1 and hasattr(content[1], 'text'):
                return content[1].text
        # 检查 type 属性
        elif hasattr(first_item, 'type'):
            if first_item.type == 'text':
                return getattr(first_item, 'text', str(first_item))
            elif first_item.type == 'thinking':
                if len(content) > 1:
                    return getattr(content[1], 'text', str(content[1]))
    # 直接尝试转字符串
    return str(content)


def generate_html_report(topics: list, analysis: dict, timestamp: str) -> str:
    """生成 HTML 报告"""
    # 模板在 .agent/skills/weibo-hot-analyzer/assets/ 目录下
    repo_root = Path(__file__).parent.parent
    template_path = repo_root / ".agent" / "skills" / "weibo-hot-analyzer" / "assets" / "report-template.html"
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # 生成表格行
    table_rows = ""
    for t in topics[:10]:
        rank_class = f"rank-{t['rank']}" if t['rank'] <= 3 else "rank-other"
        table_rows += f"""
        <tr>
            <td><span class="rank-badge {rank_class}">{t['rank']}</span></td>
            <td>
                <a href="{t['url']}" target="_blank" class="topic-title">{t['title']}</a>
                {f'<span class="topic-label label-hot">热</span>' if t.get('is_hot') else ''}
                {f'<span class="topic-label label-new">新</span>' if t.get('is_new') else ''}
                {f'<span class="topic-label label-fei">沸</span>' if t.get('is_fei') else ''}
            </td>
            <td><span class="category-tag cat-{t['category']}">{t['category']}</span></td>
            <td class="hot-value">{format_hot_value(t['hot_value'])}</td>
        </tr>
        """

    # 生成分析卡片
    analysis_cards = ""
    for item in analysis["analyses"]:
        points_html = "".join([f"<li>{p}</li>" for p in item["key_points"]])
        is_commercial_empty = item["commercial"] in ["无明显商业化机会", "暂无商业化机会", ""]
        commercial_class = "no-commercial" if is_commercial_empty else ""

        analysis_cards += f"""
        <div class="analysis-card">
            <div class="card-header">
                <div class="card-rank">
                    <span class="rank-badge rank-{item['rank']}" style="width: 40px; height: 40px; font-size: 1rem;">{item['rank']}</span>
                </div>
                <div class="card-title-area">
                    <div class="card-title">{item['title']}</div>
                    <div class="card-meta">
                        <span class="category-tag cat-{item['category']}">{item['category']}</span>
                    </div>
                </div>
            </div>
            <div class="card-section">
                <div class="card-section-title">核心摘要</div>
                <p class="summary-text">{item['summary']}</p>
            </div>
            <div class="card-section">
                <div class="card-section-title">关键要点</div>
                <ul class="key-points">{points_html}</ul>
            </div>
            <div class="card-section">
                <div class="card-section-title">💰 商业化洞察</div>
                <div class="commercial-insight {commercial_class}">{item['commercial']}</div>
            </div>
        </div>
        """

    # 生成商业化机会列表
    opportunities = []
    for item in analysis["analyses"]:
        if item["commercial"] not in ["无明显商业化机会", "暂无商业化机会", ""]:
            opportunities.append({
                "title": item["title"],
                "category": item["category"],
                "insight": item["commercial"]
            })

    opportunities_html = ""
    for i, opp in enumerate(opportunities[:5]):
        icon = {"娱乐": "🎭", "科技": "💻", "社会": "📢", "体育": "⚽", "财经": "💰", "其他": "🔍"}[opp["category"]]
        opportunities_html += f"""
        <div class="opportunity-item">
            <div class="opportunity-icon">{icon}</div>
            <div class="opportunity-content">
                <h4>{opp['title']}</h4>
                <p>{opp['insight']}</p>
            </div>
        </div>
        """

    if not opportunities_html:
        opportunities_html = "<p style='color: var(--text-secondary);'>本期热搜暂无明显商业化机会</p>"

    # 替换模板占位符
    html = template.replace("{{DATE}}", timestamp.replace("_", " "))
    html = html.replace("{{HOT_TABLE_ROWS}}", table_rows)
    html = html.replace("{{ANALYSIS_CARDS}}", analysis_cards)
    html = html.replace("{{TREND_INSIGHT}}", analysis["trend_insight"])
    html = html.replace("{{COMMERCIAL_OPPORTUNITIES}}", opportunities_html)

    return html


def generate_markdown_report(topics: list, analysis: dict, timestamp: str) -> str:
    """生成 Markdown 报告"""

    # 概览表格
    overview = "| 排名 | 热搜话题 | 热度 | 分类 |\n|------|----------|------|------|\n"
    for t in topics[:10]:
        labels = []
        if t.get('is_hot'): labels.append("热")
        if t.get('is_new'): labels.append("新")
        if t.get('is_fei'): labels.append("沸")
        label_str = f" ({','.join(labels)})" if labels else ""
        overview += f"| {t['rank']} | {t['title']}{label_str} | {format_hot_value(t['hot_value'])} | {t['category']} |\n"

    # 深度分析
    depth_analysis = ""
    for item in analysis["analyses"]:
        points = "\n".join([f"- {p}" for p in item["key_points"]])
        depth_analysis += f"""
### 🥇 第 {item['rank']} 名：{item['title']}

**分类**：{item['category']}

#### 核心摘要
{item['summary']}

#### 关键要点
{points}

#### 商业化洞察
{item['commercial']}
---
"""

    md = f"""# 微博热搜 Top 10 分析报告

> 📅 报告生成时间：{timestamp.replace("_", " ")}
> 🔗 数据来源：微博官方 API

## 📊 热搜总览

{overview}

## 🔍 深度分析

{depth_analysis}

## 📈 趋势洞察

{analysis['trend_insight']}

## 💼 商业化机会汇总

{analysis['commercial_summary']}

---
*由 Claude Agent SDK 自动生成*
"""

    return md


def main():
    print("=" * 60)
    print("微博热搜分析")
    print("=" * 60)

    if not ANTHROPIC_API_KEY:
        print("❌ 错误: 未设置 ANTHROPIC_API_KEY 环境变量")
        sys.exit(1)

    # 1. 获取热搜数据
    print("\n📡 正在获取微博热搜数据...")
    if DEBUG:
        print("🧪 调试模式：使用模拟数据")
        from fetch_weibo_hot import generate_mock_data
        result = {
            "success": True,
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": generate_mock_data()
        }
    else:
        result = fetch_weibo_hot_search()

    if not result["success"]:
        print(f"❌ 获取失败: {result.get('error', '未知错误')}")
        sys.exit(1)

    topics = result["data"]
    print(f"✅ 获取成功！共 {len(topics)} 条热搜")

    # 2. 调用 Claude 分析
    print("\n🤖 正在调用 Claude 进行深度分析...")
    client_kwargs = {"api_key": ANTHROPIC_API_KEY}
    if ANTHROPIC_BASE_URL:
        client_kwargs["base_url"] = ANTHROPIC_BASE_URL
    client = Anthropic(**client_kwargs)

    try:
        raw_analysis = get_claude_analysis(client, topics[:10])
        # 解析 JSON
        if raw_analysis.startswith("```json"):
            raw_analysis = raw_analysis[7:-3]
        elif raw_analysis.startswith("```"):
            raw_analysis = raw_analysis[3:-3]
        analysis = json.loads(raw_analysis)
        print("✅ Claude 分析完成")
    except json.JSONDecodeError as e:
        print(f"❌ Claude 返回格式错误: {e}")
        print(f"原始输出:\n{raw_analysis[:500]}")
        sys.exit(1)

    # 3. 生成报告
    print("\n📝 正在生成报告...")
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    OUTPUT_DIR.mkdir(exist_ok=True)

    # HTML 报告
    html_content = generate_html_report(topics, analysis, timestamp)
    html_path = OUTPUT_DIR / f"weibo-hot-{timestamp}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ HTML 报告: {html_path}")

    # Markdown 报告
    md_content = generate_markdown_report(topics, analysis, timestamp)
    md_path = OUTPUT_DIR / f"weibo-hot-{timestamp}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"✅ Markdown 报告: {md_path}")

    # 4. 输出摘要
    print("\n" + "=" * 60)
    print("📊 热搜 Top 3 速览")
    print("=" * 60)
    for t in topics[:3]:
        print(f"{t['rank']}. [{t['category']}] {t['title']}")
        print(f"   热度: {format_hot_value(t['hot_value'])}")

    print(f"\n✅ 分析完成！报告已保存到 {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
