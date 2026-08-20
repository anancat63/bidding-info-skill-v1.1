#!/usr/bin/env python3
"""
招标公告列表（AI打分排序版）
输出评分提示+编号列表，由AI根据公司业务范围打分排序
用法: python3 bids_ranked.py [--top N] [--page-size N] [--region CODE]
"""

import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _core import crawl_bids, filter_active_bids, load_company_scope, format_bid_line


def main():
    parser = argparse.ArgumentParser(description="乌海市招标公告（AI评分排序）")
    parser.add_argument("--top", type=int, default=0, help="只取前N条，0=全部")
    parser.add_argument("--page-size", type=int, default=20, help="每页采集条数")
    parser.add_argument("--region", default="150301", help="地区编码，乌海=150301")
    args = parser.parse_args()

    items, total = crawl_bids(page_size=args.page_size, region=args.region, top=args.top)
    items = filter_active_bids(items)
    scope = load_company_scope()

    print("=" * 60)
    print("任务：根据公司业务范围，对以下招标公告进行匹配度评分并排序")
    print("=" * 60)
    print()
    print("【公司业务范围】")
    print(scope)
    print()
    print("【评分规则】")
    print("- 满分100分，分数越高越值得跟进")
    print("- 80-100：高度匹配，核心业务，建议立即跟进")
    print("- 60-79：比较匹配，公司有能力承接")
    print("- 40-59：部分相关，可作为储备")
    print("- 0-39：关联度低，不建议投入精力")
    print("- 主要依据项目名称判断匹配度，截止时间近的适当关注")
    print("- 评分后按分数从高到低排序，以表格形式输出")
    print("- 表格列：评分 | 标题 | 地区 | 方式 | 截止时间 | 剩余天数 | 链接")
    print("- 3天内截止的标注【紧急】，7天内标注【关注】")
    print()
    print(f"【招标公告列表】（官网共{total}条，以下{len(items)}条未截止）")
    print("-" * 60)

    # 输出编号列表和链接映射
    links = {}
    for x in items:
        print(format_bid_line(x))
        links[x["index"]] = x["url"]

    print()
    print("【链接】")
    for idx, url in links.items():
        print(f"{idx}. {url}")
    print()
    print("请对以上每个项目打分（0-100），按分数从高到低排序后输出Markdown表格。")


if __name__ == "__main__":
    main()
