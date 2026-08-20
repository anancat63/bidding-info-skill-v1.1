#!/usr/bin/env python3
"""
招标公告列表（原始顺序，不含已截止）
用法: python3 bids.py [--top N] [--page-size N] [--region CODE]
输出: JSON
"""

import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _core import crawl_bids, filter_active_bids


def main():
    parser = argparse.ArgumentParser(description="乌海市招标公告列表（原始顺序）")
    parser.add_argument("--top", type=int, default=0, help="只取前N条，0=全部")
    parser.add_argument("--page-size", type=int, default=20, help="每页采集条数")
    parser.add_argument("--region", default="150301", help="地区编码，乌海=150301")
    args = parser.parse_args()

    items, total = crawl_bids(page_size=args.page_size, region=args.region, top=args.top)
    items = filter_active_bids(items)

    output = {
        "类型": "招标公告",
        "地区编码": args.region,
        "官网总数": total,
        "返回条数": len(items),
        "项目": [
            {
                "序号": x["index"],
                "标题": x["title"],
                "地区": x["region"],
                "方式": x["type"],
                "发布日期": x["pubDate"],
                "截止时间": x["deadline"],
                "剩余天数": x["daysLeft"],
                "链接": x["url"],
            }
            for x in items
        ],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
