# -*- coding: utf-8 -*-
"""Text extraction utilities"""
import re

def get_text_items(page):
    items = []
    for b in page.get_text("dict")["blocks"]:
        if b["type"] == 0:
            for line in b["lines"]:
                t = "".join(s["text"] for s in line["spans"]).strip()
                if t:
                    items.append((t, (line["bbox"][0]+line["bbox"][2])/2, line["bbox"][1]))
    return items

def in_column(xc, left, right):
    return left <= xc <= right

def unique_desc(lines):
    seen = set()
    out = []
    for d in lines:
        if d not in seen: seen.add(d); out.append(d)
    return " ".join(out).strip()

def strip_noise(desc, patterns=None):
    if not desc: return desc
    if patterns is None:
        patterns = [(r"日期\s+设计\s+审核\s+批准\s*",""),(r"江苏烽禾升智能科技有限公\s*司\s*",""),(r"项目编号:\s*[^\n]*",""),(r"项目描述:\s*[^\n]*",""),(r"页描述:\s*图纸号:\s*",""),(r"\s+"," ")]
    for p,r in patterns: desc = re.sub(p, r, desc)
    return desc.strip()

def merge_chinese_fragments(text):
    if not text: return text
    text = re.sub(r"([\u4e00-\u9fff])\s+([\u4e00-\u9fff])", r"\1\2", text)
    return text

def postprocess_desc(desc):
    if not desc or desc == "备用": return desc
    desc = strip_noise(desc)
    desc = merge_chinese_fragments(desc)
    return desc[:120]
