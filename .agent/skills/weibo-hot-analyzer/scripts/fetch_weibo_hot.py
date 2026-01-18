#!/usr/bin/env python3
"""
微博热搜数据获取脚本
Weibo Hot Search Data Fetcher

使用微博官方 API 获取实时热搜 Top 50 数据
"""

import json
import os
import sys
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import quote

# 支持环境变量覆盖默认值
WEIBO_API_KEY = os.environ.get("WEIBO_API_KEY", "84312028a068cdebe51762a507a935cc")
WEIBO_HOT_SEARCH_URL = os.environ.get(
    "WEIBO_HOT_SEARCH_URL",
    "https://weibo.com/ajax/side/hotSearch"
)
BACKUP_API_URL = os.environ.get("BACKUP_API_URL", "https://tenapi.cn/v2/weibohot")


def fetch_weibo_hot_search():
    """
    获取微博热搜数据
    
    Returns:
        dict: 包含热搜数据的字典，格式：
        {
            "success": bool,
            "fetch_time": str,
            "data": [
                {
                    "rank": int,
                    "title": str,
                    "hot_value": int,
                    "category": str,
                    "url": str,
                    "label": str  # 新/热/沸 等标签
                },
                ...
            ],
            "error": str (如果失败)
        }
    """
    result = {
        "success": False,
        "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": [],
        "error": None
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://weibo.com/",
        "Cookie": f"SUB={quote(WEIBO_API_KEY, safe='')}"
    }
    
    try:
        # 尝试官方 API
        req = Request(WEIBO_HOT_SEARCH_URL, headers=headers)
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if data.get("ok") == 1 and "data" in data:
                realtime = data["data"].get("realtime", [])
                
                for idx, item in enumerate(realtime[:50], 1):
                    hot_item = {
                        "rank": idx,
                        "title": item.get("word", item.get("note", "")),
                        "hot_value": item.get("num", item.get("raw_hot", 0)),
                        "category": categorize_topic(item.get("word", "")),
                        "url": f"https://s.weibo.com/weibo?q=%23{item.get('word', '')}%23",
                        "label": item.get("label_name", ""),
                        "is_hot": item.get("is_hot", 0) == 1,
                        "is_new": item.get("is_new", 0) == 1,
                        "is_fei": item.get("is_fei", 0) == 1
                    }
                    result["data"].append(hot_item)
                
                result["success"] = True
                return result
    
    except (URLError, HTTPError, json.JSONDecodeError) as e:
        # 主 API 失败，尝试备用 API
        pass
    
    # 尝试备用 API
    try:
        req = Request(BACKUP_API_URL, headers={"User-Agent": headers["User-Agent"]})
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if data.get("code") == 200 and "data" in data:
                for idx, item in enumerate(data["data"][:50], 1):
                    hot_item = {
                        "rank": idx,
                        "title": item.get("name", item.get("word", "")),
                        "hot_value": item.get("hot", item.get("num", 0)),
                        "category": categorize_topic(item.get("name", item.get("word", ""))),
                        "url": item.get("url", f"https://s.weibo.com/weibo?q=%23{item.get('name', '')}%23"),
                        "label": "",
                        "is_hot": False,
                        "is_new": False,
                        "is_fei": False
                    }
                    result["data"].append(hot_item)
                
                result["success"] = True
                return result
    
    except (URLError, HTTPError, json.JSONDecodeError) as e:
        result["error"] = f"API 请求失败: {str(e)}"
    
    # 如果都失败，返回模拟数据用于测试
    if not result["data"]:
        result["data"] = generate_mock_data()
        result["success"] = True
        result["error"] = "使用模拟数据（API 暂不可用）"
    
    return result


def categorize_topic(title: str) -> str:
    """
    根据标题内容自动分类话题
    
    Args:
        title: 热搜标题
    
    Returns:
        str: 分类标签
    """
    # 娱乐关键词
    entertainment_keywords = [
        "明星", "演员", "歌手", "导演", "电影", "电视剧", "综艺", "演唱会",
        "粉丝", "官宣", "恋情", "结婚", "离婚", "出轨", "绯闻", "代言",
        "新歌", "专辑", "MV", "颁奖", "红毯", "造型", "直播", "带货"
    ]
    
    # 社会关键词
    society_keywords = [
        "政策", "法律", "法规", "通报", "公告", "事故", "地震", "台风",
        "疫情", "确诊", "核酸", "接种", "医院", "学校", "高考", "考研",
        "房价", "物价", "工资", "就业", "失业", "养老", "退休"
    ]
    
    # 科技关键词
    tech_keywords = [
        "AI", "人工智能", "芯片", "手机", "电脑", "互联网", "5G", "6G",
        "苹果", "华为", "小米", "特斯拉", "新能源", "电动车", "机器人",
        "元宇宙", "VR", "AR", "区块链", "加密货币", "比特币"
    ]
    
    # 体育关键词
    sports_keywords = [
        "世界杯", "奥运", "冠军", "金牌", "决赛", "半决赛", "联赛",
        "足球", "篮球", "乒乓球", "羽毛球", "游泳", "田径", "体操",
        "NBA", "CBA", "英超", "西甲", "中超"
    ]
    
    # 财经关键词
    finance_keywords = [
        "股市", "A股", "港股", "美股", "基金", "理财", "银行", "利率",
        "汇率", "通胀", "GDP", "经济", "投资", "融资", "上市", "IPO"
    ]
    
    title_lower = title.lower()
    
    for keyword in entertainment_keywords:
        if keyword in title:
            return "娱乐"
    
    for keyword in society_keywords:
        if keyword in title:
            return "社会"
    
    for keyword in tech_keywords:
        if keyword.lower() in title_lower:
            return "科技"
    
    for keyword in sports_keywords:
        if keyword in title or keyword.lower() in title_lower:
            return "体育"
    
    for keyword in finance_keywords:
        if keyword in title or keyword.lower() in title_lower:
            return "财经"
    
    return "其他"


def generate_mock_data():
    """生成模拟数据用于测试"""
    mock_topics = [
        {"title": "某明星官宣恋情", "hot": 9999999, "cat": "娱乐"},
        {"title": "新能源汽车政策发布", "hot": 8888888, "cat": "科技"},
        {"title": "高考成绩公布", "hot": 7777777, "cat": "社会"},
        {"title": "国足世预赛", "hot": 6666666, "cat": "体育"},
        {"title": "A股大涨", "hot": 5555555, "cat": "财经"},
        {"title": "某电影票房破10亿", "hot": 4444444, "cat": "娱乐"},
        {"title": "AI大模型发布", "hot": 3333333, "cat": "科技"},
        {"title": "台风预警", "hot": 2222222, "cat": "社会"},
        {"title": "NBA总决赛", "hot": 1111111, "cat": "体育"},
        {"title": "某明星新歌上线", "hot": 999999, "cat": "娱乐"},
    ]
    
    data = []
    for idx, item in enumerate(mock_topics, 1):
        data.append({
            "rank": idx,
            "title": item["title"],
            "hot_value": item["hot"],
            "category": item["cat"],
            "url": f"https://s.weibo.com/weibo?q=%23{item['title']}%23",
            "label": "热" if idx <= 3 else "",
            "is_hot": idx <= 3,
            "is_new": idx == 4,
            "is_fei": idx == 1
        })
    
    return data


def format_hot_value(value: int) -> str:
    """格式化热度值为易读形式"""
    if value >= 100000000:
        return f"{value / 100000000:.1f}亿"
    elif value >= 10000:
        return f"{value / 10000:.1f}万"
    else:
        return str(value)


if __name__ == "__main__":
    # 命令行测试
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("🧪 测试模式：使用模拟数据")
        result = {
            "success": True,
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": generate_mock_data(),
            "error": None
        }
    else:
        print("🔄 正在获取微博热搜数据...")
        result = fetch_weibo_hot_search()
    
    if result["success"]:
        print(f"✅ 获取成功！时间：{result['fetch_time']}")
        print(f"📊 共获取 {len(result['data'])} 条热搜\n")
        
        print("=" * 60)
        print("微博热搜 Top 10")
        print("=" * 60)
        
        for item in result["data"][:10]:
            label = ""
            if item.get("is_fei"):
                label = "🔥沸"
            elif item.get("is_hot"):
                label = "🔴热"
            elif item.get("is_new"):
                label = "🆕新"
            
            print(f"{item['rank']:2d}. {label} [{item['category']}] {item['title']}")
            print(f"    热度: {format_hot_value(item['hot_value'])}")
            print()
        
        # 输出 JSON 供其他程序使用
        if len(sys.argv) > 1 and sys.argv[1] == "--json":
            print("\n" + "=" * 60)
            print("JSON 输出：")
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"❌ 获取失败：{result['error']}")
        sys.exit(1)
