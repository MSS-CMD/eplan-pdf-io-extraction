# -*- coding: utf-8 -*-
"""
framework/utils/text.py
文本提取工具函数
"""
import re

def get_text_items(page):
    """获取页面上所有文本元素及其坐标"""
    items = []
    for b in page.get_text("dict")["blocks"]:
        if b["type"] == 0:
            for line in b["lines"]:
                text = "".join([s["text"] for s in line["spans"]]).strip()
                if text:
                    x0, y0, x1, y1 = line["bbox"]
                    items.append((text, (x0 + x1) / 2, y0))
    return items


def in_column(x_center, col_left, col_right):
    return col_left <= x_center <= col_right


def unique_desc(lines):
    """去重描述行"""
    seen = set()
    out = []
    for d in lines:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return " ".join(out).strip()


def strip_noise(desc, noise_patterns=None):
    """去除页眉噪声"""
    if not desc:
        return desc
    if noise_patterns is None:
        noise_patterns = [
            (r"日期\s+设计\s+审核\s+批准\s*", ""),
            (r"徐工基地\s+徐工\s*", ""),
            (r"江苏烽禾升智能科技有限公\s*司\s*", ""),
            (r"项目编号:\s*[^\n]*", ""),
            (r"项目描述:\s*[^\n]*", ""),
            (r"页描述:\s*图纸号:\s*", ""),
            (r"\s+", " "),
        ]
    for pat, repl in noise_patterns:
        desc = re.sub(pat, repl, desc)
    return desc.strip()


def merge_chinese_fragments(text):
    """合并被PDF拆分的中文短语"""
    if not text:
        return text
    # 如果是"断 路器"→"断路器"、"空 开"→"空开"
    text = re.sub(r"([\u4e00-\u9fff])\s+([\u4e00-\u9fff])", r"\1\2", text)
    return text


def postprocess_desc(desc):
    """后处理管道：清洗→合并→去重→裁剪"""
    if not desc or desc == "备用":
        return desc
    desc = strip_noise(desc)
    desc = merge_chinese_fragments(desc)
    # 限制长度
    if len(desc) > 120:
        desc = desc[:117] + "..."
    return desc
