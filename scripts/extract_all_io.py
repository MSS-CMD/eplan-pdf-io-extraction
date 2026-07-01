# -*- coding: utf-8 -*-
"""
EPLAN PDF I/O 提取核心函数
用法: 修改 pdf_path 后直接运行
"""
import pymupdf, re, json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

pdf_path = r"path\to\your\drawing.pdf"
doc = pymupdf.open(pdf_path)

all_records = []
new_q_records = []

# ============================================================
# 工具函数
# ============================================================
def get_text_items(page):
    """获取页面上所有文本元素及其坐标"""
    items = []
    blocks = page.get_text("dict")["blocks"]
    for b in blocks:
        if b["type"] == 0:
            for line in b["lines"]:
                text = "".join([s["text"] for s in line["spans"]]).strip()
                if text:
                    x0, y0, x1, y1 = line["bbox"]
                    items.append((text, x0, y0, x1, y1))
    return items

# ============================================================
# DI/DQ 解析（主控柜 + 远程IO）
# ============================================================
def parse_di_dq(page, page_num, is_di):
    items = get_text_items(page)
    io_type = "DI" if is_di else "DQ"
    label = "DI Bit" if is_di else "DO Bit"
    
    module_name = ""
    cabinet = ""
    for text, x0, y0, x1, y1 in items:
        if ("数字量输入模块" in text or "数字量输出模块" in text):
            module_name = text
        if "=010" in text and "+MCP01" in text:
            cabinet = "MCP01"
        if "+安全区" in text:
            m = re.search(r"\+安全区(\d+)", text)
            if m: cabinet = "安全区" + m.group(1)
    
    anchors = []
    for text, x0, y0, x1, y1 in items:
        m = re.match(r"^(DI|DO)\s+Bit\s+(\d+)$", text)
        if m:
            anchors.append(((x0+x1)/2, (y0+y1)/2, int(m.group(2))))
    if not anchors:
        return False
    anchors.sort(key=lambda a: a[0])
    
    cols = []
    for idx, (cx, cy, bit) in enumerate(anchors):
        left = (anchors[idx-1][0] + cx)/2 if idx > 0 else cx - 55
        right = (anchors[idx+1][0] + cx)/2 if idx < len(anchors)-1 else cx + 55
        cols.append((left, right, cx, cy, bit))
    
    for left, right, cx, cy, bit in cols:
        col_items = [(t, x0, y0) for t, x0, y0, x1, y1 in items
                     if left <= (x0+x1)/2 <= right]
        address = ""
        desc_parts = []
        device_tag = ""
        for text, x0, y0 in col_items:
            if re.match(r"^[IQ]\d+\.\d+$", text): address = text
            elif text.startswith("+") or text.startswith("-"): device_tag = text
            elif re.search(r"[\u4e00-\u9fff]", text) and "Bit" not in text: desc_parts.append(text)
        if address:
            desc = " ".join(desc_parts).strip()
            all_records.append({
                "address": address, "signal_name": "", "description": desc or device_tag,
                "module": module_name, "io_type": io_type, "cabinet": cabinet, "page": page_num
            })

# ============================================================
# IOLINK DI 解析
# ============================================================
def parse_iolink(page, page_num):
    items = get_text_items(page)
    module_name = ""
    cabinet = ""
    for text, x0, y0, x1, y1 in items:
        if "IOLINK_数字量可分配模块" in text: module_name = text
        if "+安全区" in text:
            m = re.search(r"\+安全区(\d+)", text)
            if m: cabinet = "安全区" + m.group(1)
    
    addr_items = [(t, x0, y0) for t, x0, y0, x1, y1 in items
                  if re.match(r"^I\d{4}\.\d$", t) and x0 > 100]
    for addr_text, ax, ay in addr_items:
        signal_name = ""
        desc_text = ""
        nearby = [(t, x0) for t, x0, y0, x1, y1 in items
                  if ax < (x0+x1)/2 < ax + 250 and abs(y0 - ay) < 60]
        for text, x0 in nearby:
            sig_m = re.search(r"(S\d{4})_(.+)", text)
            if sig_m and not signal_name: signal_name = sig_m.group(1) + "_" + sig_m.group(2)
            if "预留" in text and not desc_text: desc_text = "预留"
            cn = re.findall(r"[\u4e00-\u9fff]{2,}", text)
            for c in cn:
                if not any(w in c for w in ["版权","保护","编码","M12","SAF"]) and not desc_text:
                    desc_text = c
        all_records.append({
            "address": addr_text, "signal_name": signal_name, "description": desc_text,
            "module": module_name, "io_type": "DIO (IOLINK)", "cabinet": cabinet, "page": page_num
        })

# ============================================================
# IOLINK Q 提取
# ============================================================
def extract_iolink_q(page, page_num):
    lines = page.get_text("text", sort=True).split("\n")
    module_name = ""
    for line in lines:
        if "IOLINK_数字量可分配模块" in line: module_name = line.strip()
    q_addrs = set()
    for line in lines:
        for m in re.finditer(r"\bQ\d{4}\.\d\b", line): q_addrs.add(m.group())
    for qa in sorted(q_addrs):
        new_q_records.append({
            "address": qa, "signal_name": "", "description": "",
            "module": module_name, "io_type": "DQ (IOLINK)", "cabinet": "", "page": page_num
        })

# ============================================================
# 阀岛 Q 提取
# ============================================================
def extract_valve_q(page, page_num):
    lines = page.get_text("text", sort=True).split("\n")
    module_name = "亚德客阀岛"
    for line in lines:
        q_addrs = list(re.finditer(r"\bQ17\d{3}\.\d\b", line))
        sigs = list(re.finditer(r"\b(C\d{4})_(\S+)", line))
        if not q_addrs: continue
        for qm in q_addrs:
            q_full = qm.group()
            sig_name = ""
            desc = ""
            for sm in sigs:
                sig_name = sm.group(1) + "_" + sm.group(2)
                desc = sm.group(2)
            new_q_records.append({
                "address": q_full, "signal_name": sig_name, "description": desc,
                "module": module_name, "io_type": "DQ (阀岛)", "cabinet": "", "page": page_num
            })

# ============================================================
# AI 解析
# ============================================================
def parse_ai(page, page_num):
    items = get_text_items(page)
    module_name = ""
    for text, x0, y0, x1, y1 in items:
        if "模拟量输入" in text or ("IOLINK_" in text and "模拟量" in text):
            module_name = text
    piws = [(t, x0, y0) for t, x0, y0, x1, y1 in items if re.match(r"^PIW\d{4}$", t) and x0 > 100]
    for addr_text, ax, ay in piws:
        signal_name = ""
        desc_text = ""
        nearby = [(t, x0) for t, x0, y0, x1, y1 in items if abs(y0 - ay) < 60 and ax < (x0+x1)/2 < ax + 250]
        for text, x0 in nearby:
            sig_m = re.search(r"(S\d{4})_(.+)", text)
            if sig_m: signal_name = sig_m.group(1) + "_" + sig_m.group(2)
            cn = re.findall(r"[\u4e00-\u9fff]{3,}", text)
            for c in cn:
                if not any(w in c for w in ["编码","公头","母头","M12","版权"]) and not desc_text:
                    desc_text = c
        all_records.append({
            "address": addr_text, "signal_name": signal_name, "description": desc_text,
            "module": module_name, "io_type": "AI", "cabinet": "", "page": page_num
        })

# ============================================================
# 主处理循环
# ============================================================
for i in range(doc.page_count):
    page = doc[i]
    text = page.get_text()
    page_num = i + 1
    if "数字量输入模块 16位" in text: parse_di_dq(page, page_num, True)
    elif "数字量输出模块 16位" in text: parse_di_dq(page, page_num, False)
    elif "IOLINK_数字量可分配模块" in text:
        parse_iolink(page, page_num)
        extract_iolink_q(page, page_num)
    elif "亚德客阀岛" in text or "阀岛" in text: extract_valve_q(page, page_num)
    elif "模拟量输入" in text and "PIW" in text: parse_ai(page, page_num)

# ============================================================
# 合并、去重、排序
# ============================================================
merged = all_records + new_q_records
seen = set()
unique = []
for r in merged:
    if r["address"] not in seen:
        seen.add(r["address"])
        unique.append(r)

def addr_key(r):
    a = r["address"]
    m = re.match(r"I(\d{4})\.(\d)", a)
    if m: return (0, int(m.group(1)), int(m.group(2)))
    m = re.match(r"Q(\d{4})\.(\d)", a)
    if m: return (1, int(m.group(1)), int(m.group(2)))
    m = re.match(r"PIW(\d{4})", a)
    if m: return (3, int(m.group(1)), 0)
    return (9, 0, 0)
unique.sort(key=addr_key)

# ============================================================
# 生成 Excel
# ============================================================
wb = Workbook()
ws = wb.active
ws.title = "PLC IO 总表"

# ... (Excel 格式化代码，见主技能文档)
print(f"总点数: {len(unique)}")

output_path = pdf_path.replace(".pdf", "_IO_Table.xlsx")
# wb.save(output_path)
# print(f"已保存: {output_path}")

doc.close()
