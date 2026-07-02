# -*- coding: utf-8 -*-
"""Valve island parser"""
import re
from utils.text import get_text_items

def parse(page,pn,config):
    items=get_text_items(page)
    q_items=[(t,x,y) for t,x,y in items if re.match(r"^Q17\d{3}\.\d$",t)]
    sigs=[(t,x,y) for t,x,y in items if re.match(r"^C\d{4}_",t)]
    records=[]
    for addr,ax,ay in q_items:
        best_sig=""; best_dist=999
        for st,sx,sy in sigs:
            dist=abs(sx-ax)+abs(sy-ay)*3
            if dist<best_dist: best_dist=dist; best_sig=st
        records.append({"address":addr,"device_tag":"","description":best_sig,"module":config.get("module_name","阀岛"),"io_type":config.get("io_type","阀岛(FDQ)"),"page":pn,"bit":""})
    return records
