#!/usr/bin/env python3
"""
内蒙古政府采购网 - 核心爬虫模块（零依赖，使用urllib）
供 bids.py / bids_ranked.py / intentions.py / intentions_ranked.py 调用
"""

import json
import re
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime, date

BASE_URL = "https://www.ccgp-neimenggu.gov.cn"
LIST_API = f"{BASE_URL}/gpcms/rest/web/v2/info/selectInfoMoreChannel"

SITE_ID = "556c65d-c55d-4f92-8469-d5675c58bd04"
CHANNEL = "72289d72580838523529e2a8099cbc57"
DEFAULT_REGION = "150301"

BID_TYPE = "00101"        # 招标公告
INTENTION_TYPE = "59,5E"  # 采购意向公开

TYPE_MAP = {"001011": "公开招标", "001014": "询价", "001016": "竞争性磋商"}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Referer": f"{BASE_URL}/maincms-web/noticeInformationNm",
    "Accept": "application/json, text/plain, */*",
}


def fetch_list(notice_type, page_size=20, region=DEFAULT_REGION):
    """获取公告列表，返回 (rows, total)"""
    params = urllib.parse.urlencode({
        "siteId": SITE_ID,
        "channel": CHANNEL,
        "currPage": 1,
        "pageSize": page_size,
        "noticeType": notice_type,
        "regionCode": region,
        "cityOrArea": "7",
    })
    url = f"{LIST_API}?{params}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if str(data.get("code")) != "200":
        print(f"[错误] 接口返回异常: code={data.get('code')}, msg={data.get('message', '')}",
              file=sys.stderr)
        return [], 0
    return data.get("data", {}).get("rows", []), data.get("data", {}).get("total", 0)


def parse_date(date_str):
    """尝试解析多种日期格式，返回date对象或None"""
    if not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str[:len(fmt) + 2], fmt).date()
        except ValueError:
            continue
    # 尝试提取日期部分
    m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", date_str)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    return None


def days_left(date_str):
    """计算剩余天数，负数表示已过期"""
    d = parse_date(date_str)
    if d is None:
        return None
    return (d - date.today()).days


def clean_intention_desc(raw):
    """清理采购意向description，去掉开头套话，保留有效内容"""
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", text).strip()
    # 去掉开头套话："为便于供应商...公开如下：" 或 "，根据《财政部...公开如下："
    m = re.search(r"公开如下[：:]\s*", text)
    if m:
        text = text[m.end():]
    else:
        boilerplate = "为便于供应商及时了解政府采购信息"
        idx = text.find(boilerplate)
        if idx >= 0:
            text = text[idx + len(boilerplate):]
    # 去掉结尾套话
    for ending in ["本次公开的采购意向", "具体采购项目情况以相关采购公告和采购文件为准"]:
        idx = text.find(ending)
        if idx >= 0:
            text = text[:idx]
    return text.strip()[:200]


def extract_budget_wan(text):
    """从文本中提取预算金额（万元）"""
    m = re.search(r"预算金额[（(]万元[）)]\s*[\n:：]*\s*([\d,]+\.?\d*)", text)
    if m:
        try:
            return round(float(m.group(1).replace(",", "")), 2)
        except ValueError:
            pass
    m = re.search(r"([\d,]+\.\d+)\s*(?:20\d{2}年\d{1,2}月|无|$)", text)
    if m:
        try:
            return round(float(m.group(1).replace(",", "")), 2)
        except ValueError:
            pass
    return None


def extract_expect_month(text):
    """提取预计采购月份 YYYY-MM"""
    m = re.search(r"(20\d{2})\s*年\s*(\d{1,2})\s*月", text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    return None


def months_left(expect_str):
    """预计采购时间距今多少月"""
    if not expect_str:
        return None
    try:
        ey, em = map(int, expect_str.split("-"))
        today = date.today()
        return (ey - today.year) * 12 + (em - today.month)
    except (ValueError, IndexError):
        return None


def build_url(notice_id, plan_id=""):
    """构建公告详情链接"""
    url = f"{BASE_URL}/maincms-web/articleNm?type=notice&id={notice_id}"
    if plan_id:
        url += f"&planId={plan_id}"
    return url


def crawl_bids(page_size=20, region=DEFAULT_REGION, top=0):
    """采集招标公告，返回原始顺序列表（含已截止的，由调用方过滤）"""
    rows, total = fetch_list(BID_TYPE, page_size, region)
    if not rows:
        return [], total

    results = []
    for i, row in enumerate(rows, 1):
        notice_id = row.get("id", "")
        title = row.get("title", "")
        end_time = row.get("noticeEndTime", "")
        plan_id = row.get("openTenderCode", "")
        dleft = days_left(end_time)

        results.append({
            "index": i,
            "id": notice_id,
            "title": title,
            "description": title,
            "region": row.get("regionName", ""),
            "type": TYPE_MAP.get(row.get("noticeType", ""), "招标公告"),
            "pubDate": (row.get("noticeTime") or "")[:10],
            "deadline": end_time[:16] if end_time else "",
            "daysLeft": dleft,
            "url": build_url(notice_id, plan_id),
        })
        if top and len(results) >= top:
            break
    return results, total


def crawl_intentions(page_size=20, region=DEFAULT_REGION, top=0):
    """采集采购意向，返回原始顺序列表（含已过期的，由调用方过滤）"""
    rows, total = fetch_list(INTENTION_TYPE, page_size, region)
    if not rows:
        return [], total

    results = []
    for i, row in enumerate(rows, 1):
        notice_id = row.get("id", "")
        title = row.get("title", "")
        desc_raw = row.get("description", "") or ""
        desc_clean = clean_intention_desc(desc_raw)
        expect_time = extract_expect_month(desc_raw)
        mleft = months_left(expect_time)
        budget = extract_budget_wan(desc_raw)

        results.append({
            "index": i,
            "id": notice_id,
            "title": title,
            "description": desc_clean if desc_clean else title,
            "region": row.get("regionName", ""),
            "type": "采购意向",
            "pubDate": (row.get("noticeTime") or "")[:10],
            "expectTime": expect_time or "",
            "monthsLeft": mleft,
            "budget": budget,
            "purchaser": row.get("purchaser", "") or row.get("agency", ""),
            "url": build_url(notice_id),
        })
        if top and len(results) >= top:
            break
    return results, total


def filter_active_bids(items):
    """过滤掉已截止的招标公告"""
    return [x for x in items if x.get("daysLeft") is None or x["daysLeft"] >= 0]


def filter_active_intentions(items):
    """过滤掉已过期的采购意向"""
    return [x for x in items if x.get("monthsLeft") is None or x["monthsLeft"] >= 0]


def load_company_scope():
    """读取公司业务范围配置"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "config", "company.txt")
    path = os.path.normpath(path)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "（未配置公司业务范围，请编辑 config/company.txt）"


def format_bid_line(item):
    """格式化为单行文本（排序版用）"""
    dl = item.get("daysLeft")
    if dl is None:
        urgency = "时间未知"
    elif dl < 0:
        urgency = "已截止"
    elif dl == 0:
        urgency = "今天截止"
    else:
        urgency = f"剩{dl}天"
    budget = item.get("budget")
    budget_str = f"{budget}万" if budget else "预算未知"
    return (f"{item['index']}. [{item['type']}][{item['region']}] "
            f"{item['title']} | 截止:{item['deadline']}({urgency})")


def format_intention_line(item):
    """格式化为单行文本（排序版用）"""
    ml = item.get("monthsLeft")
    if ml is None:
        time_str = "时间未知"
    elif ml < 0:
        time_str = "已过期"
    elif ml == 0:
        time_str = "本月采购"
    else:
        time_str = f"{ml}个月后"
    budget = item.get("budget")
    budget_str = f"预算{budget}万" if budget else ""
    parts = [f"{item['index']}. [{item['region']}] {item['title']}"]
    if item.get("expectTime"):
        parts.append(f"预计采购:{item['expectTime']}({time_str})")
    if budget_str:
        parts.append(budget_str)
    if item.get("description") and item["description"] != item["title"]:
        parts.append(f"内容:{item['description'][:100]}")
    return " | ".join(parts)
