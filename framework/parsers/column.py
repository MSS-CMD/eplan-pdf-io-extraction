# -*- coding: utf-8 -*-
"""framework/parsers/column.py - DI/DQ统一列布局解析器"""
import re
from utils.text import get_text_items, in_column, unique_desc

def parse(page, pn, config):
    records = []
    items = get_text_items(page)
    module_name = ""
    for t, x, y in items:
        if "数字量输入模块" in t or "数字量输出模块" in t or "安全输入模块" in t:
            module_name = t.strip()

    # 找到Bit标签作为列锚点（数字总是在最后一个捕获组）
    anchors = []
    for t, x, y in items:
        m = re.match(config["bit_label_re"], t)
        if m and abs(y - config.get("bit_label_y", 571)) < 15:
            anchors.append((x, int(m.group(m.lastindex))))

    if not anchors:
        return records
    anchors.sort(key=lambda a: a[0])

    for idx, (cx, bit) in enumerate(anchors):
        left = (anchors[idx - 1][0] + cx) / 2 if idx > 0 else cx - 60
        right = (anchors[idx + 1][0] + cx) / 2 if idx < len(anchors) - 1 else cx + 60
        addr, tag, desc_lines = "", "", []

        for t, x, y in items:
            if not in_column(x, left, right):
                continue
            if re.match(config["address_re"], t):
                y_l, y_h = config.get("address_y_range", [0, 999])
                if y_l < y < y_h:
                    addr = t
            if (t.startswith("+") or t.startswith("-")) and config.get("device_tag_y_range"):
                y_l, y_h = config["device_tag_y_range"]
                if y_l < y < y_h:
                    tag = t
            y_l, y_h = config.get("desc_y_range", [0, 999])
            if re.search(r'[\u4e00-\u9fff]', t) and y_l < y < y_h and "Bit" not in t:
                desc_lines.append(t)
            if t == "备用" and y_l < y < y_h:
                desc_lines.append("备用")

        if addr:
            records.append({
                "address": addr, "device_tag": tag,
                "description": unique_desc(desc_lines),
                "module": module_name, "io_type": config.get("io_type", "DI"),
                "page": pn, "bit": bit,
            })
    return records
