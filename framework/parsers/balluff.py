# -*- coding: utf-8 -*-
"""BALLUFF IO-Link PORT布局解析器"""
import re
from utils.text import get_text_items

def parse(page, pn, config):
    items = get_text_items(page)
    records = []
    module_name = ""
    for t,x,y in items:
        if "BALLUFF IO-Link" in t: module_name = t.strip()

    # 找PORT行（y坐标）
    port_rows = {}
    for t,x,y in items:
        m = re.match(r"PORT (\d+)", t)
        if m:
            port_rows[int(m.group(1))] = round(y)

    if not port_rows:
        # 某些BALLUFF页没有PORT标签，直接扫I/Q地址
        for t,x,y in items:
            m = re.match(r"^([IQ]\d{3,4})\.(\d)$", t)
            if m:
                base = m.group(1); bit = int(m.group(2))
                addr = t
                descs = []
                for t2,x2,y2 in items:
                    if abs(y2-y) < 15 and x2 > x and x2 < x+200 and not re.match(r"^[IQ]\d{3,4}\.\d$", t2):
                        descs.append(t2)
                desc = " ".join(descs)[:80]
                io_type = "BALLUFF DI" if t.startswith("I") else "BALLUFF DQ"
                records.append({"address":addr,"device_tag":"","description":desc,
                                "module":module_name,"io_type":io_type,"page":pn,"bit":bit})
        return records

    # 按PORT分组提取
    for port, py in sorted(port_rows.items()):
        for t,x,y in items:
            m = re.match(r"^([IQ]\d{3,4})\.(\d)$", t)
            if not m: continue
            if abs(y - py) > 50: continue  # 同一PORT区域
            addr = t; base = m.group(1); bit = int(m.group(2))
            descs = []; tags = []
            for t2,x2,y2 in items:
                if x2 < 200: continue
                if abs(y2 - y) < 12 and x2 > x and x2 < x + 150 and not re.match(r"^[IQ]\d{3,4}\.\d$", t2):
                    descs.append(t2)
                if abs(y2 - y) < 12 and x2 < x - 10 and x2 > x - 80:
                    tags.append(t2)
            desc = " ".join(descs)[:80]
            tag = " ".join(tags)[:40]
            if not addr: continue
            io_type = "BALLUFF DI" if t.startswith("I") else "BALLUFF DQ"
            records.append({"address":addr,"device_tag":tag,"description":desc or "PORT{}".format(port),
                            "module":module_name,"io_type":io_type,"page":pn,"bit":bit})
    return records
