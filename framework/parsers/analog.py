# -*- coding: utf-8 -*-
"""Analog input parser"""
import re
from utils.text import get_text_items

def parse(page,pn,config):
    items=get_text_items(page); records=[]; module_name=""; seen=set()
    for t,x,y in items:
        if "模拟量输入" in t: module_name=t.strip()
    for t,x,y in items:
        if not re.match(r"^PIW\d{4}$",t) or x<=100 or t in seen: continue
        seen.add(t)
        nearby=[]
        for t2,x2,y2 in items:
            if x2>x and x2<x+300 and abs(y2-y)<60 and not re.match(r"^PIW\d{4}$",t2): nearby.append(t2)
        desc=" ".join(nearby).strip()[:80]
        records.append({"address":t,"device_tag":"","description":desc,"module":module_name,"io_type":"AI","page":pn,"bit":""})
    return records
