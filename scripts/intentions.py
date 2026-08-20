#!/usr/bin/env python3
"""
采购意向公开列表（原始顺序，不含已过期）
用法: python3 intentions.py [--top N] [--page-size N] [--region CODE]
输出: JSON
"""

import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _core import crawl_intentions, filter_active_intentions


def main():
    parser = argparse.ArgumentParser(description="乌海市采购意向列表（原始顺序）")
    parser.add_argument("--top", type=int, default=0, help="只取前N条，0=全部")
    parser.add_argument("--page-size", type=int, default=20, help="每页采集条数")
    parser.add_argument("--region", default="150301", help="地区编码，乌海=150301")
    args = parser.parse_args()

    items, total = crawl_intentions(page_size=args.page_size, region=args.region, top=args.top)
    items = filter_active_intentions(items)

    output = {
        "类型": "采购意向",
        "地区编码": args.region,
        "官网总数": total,
        "返回条数": len(items),
        "项目": [
            {
                "序号": x["index"],
                "标题": x["title"],
                "地区": x["region"],
                "采购单位": x.get("purchaser", ""),
                "发布日期": x["pubDate"],
                "预计采购时间": x.get("expectTime", ""),
                "预算万元": x.get("budget"),
                "项目描述": x.get("description", ""),
                "链接": x["url"],
            }
            for x in items
        ],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
