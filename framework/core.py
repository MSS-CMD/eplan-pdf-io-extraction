# -*- coding: utf-8 -*-
"""
framework/core.py - 主引擎
"""
import json, os, re
from collections import Counter

_parsers = {}

def register(page_type, parser_fn):
    _parsers[page_type] = parser_fn

def get_parser(page_type):
    return _parsers.get(page_type)

# ===== 自动页面发现 =====

def auto_discover(doc):
    page_map = {"DI": [], "DQ": [], "IOLINK": [], "VALVE": [],
                 "AI": [], "SAFETY_IN": [], "SAFETY_OUT": []}
    for i in range(doc.page_count):
        text = doc[i].get_text()
        pn = i + 1
        is_toc = "目录 : =" in text or "HC_CONTENTS" in text or "页计数器" in text
        if is_toc:
            continue
        if "安全输出模块" in text:
            page_map["SAFETY_OUT"].append(pn)
        elif "安全输入模块" in text and "DI Bit" in text:
            page_map["SAFETY_IN"].append(pn)
        elif "数字量输入模块 16位" in text and "DI Bit" in text:
            page_map["DI"].append(pn)
        elif "数字量输出模块 16位" in text and "DO Bit" in text:
            page_map["DQ"].append(pn)
        elif "IOLINK_数字量可分配模块" in text:
            page_map["IOLINK"].append(pn)
        elif "模拟量输入" in text and "PIW" in text:
            page_map["AI"].append(pn)
        elif "阀岛阀片总览" in text or ("亚德客阀岛" in text and "Q17" in text):
            page_map["VALVE"].append(pn)
    return page_map

def _to_ranges(pages):
    if not pages: return "无"
    ranges = []
    start = prev = pages[0]
    for p in pages[1:]:
        if p > prev + 2:
            ranges.append("{}-{}".format(start, prev))
            start = p
        prev = p
    ranges.append("{}-{}".format(start, prev))
    return ", ".join(ranges)

def print_page_map(page_map):
    print("=" * 40)
    print("自动页面发现结果")
    print("=" * 40)
    total = 0
    for ptype, pages in sorted(page_map.items()):
        if pages:
            print("  {:12s}: {} 页 → {}".format(ptype, len(pages), _to_ranges(pages)))
            total += len(pages)
    print("  {:12s}: {} 页".format("合计", total))

# ===== 调度提取 =====

def extract_all(doc, page_map, configs):
    all_records = []
    for page_type, pages in page_map.items():
        if not pages: continue
        parser = get_parser(page_type)
        if not parser:
            print("  ⚠ {}: 无解析器".format(page_type))
            continue
        cfg = configs.get(page_type, {})
        for pn in pages:
            all_records.extend(parser(doc[pn-1], pn, cfg))
    return all_records

# ===== 后处理 =====

def apply_pipeline(records, pipeline=None):
    if pipeline is None:
        from utils.text import postprocess_desc
        pipeline = [("desc_clean", lambda r: {**r, "description": postprocess_desc(r.get("description", ""))})]
    for name, fn in pipeline:
        records = [fn(r) for r in records]
    return records

# ===== 地址排序 =====

def sort_records(records):
    def key(r):
        a = r.get("address", "")
        m = re.match(r"I(\d{4})\.(\d)", a)
        if m: return (0, int(m.group(1)), int(m.group(2)))
        m = re.match(r"Q(\d{4})\.(\d)", a)
        if m: return (1, int(m.group(1)), int(m.group(2)))
        m = re.match(r"Q17(\d{3})\.(\d)", a)
        if m: return (2, int(m.group(1)), int(m.group(2)))
        m = re.match(r"PIW(\d{4})", a)
        if m: return (3, int(m.group(1)), 0)
        return (9, 0, 0)
    records.sort(key=key)
    return records
