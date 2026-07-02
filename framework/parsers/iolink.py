# -*- coding: utf-8 -*-
"""IOLINK parser - signal and connector modes"""
import re
from utils.text import get_text_items

def parse(page,pn,config):
    items=get_text_items(page); records=[]; mode=config.get("mode","connector")
    module_name=""
    for t,x,y in items:
        if "IOLINK" in t: module_name=t.strip()
    for t,x,y in items:
        if not re.match(r"^[IQ]\d{4}\.\d$",t) or x<=100: continue
        signal_name=""; nearby_texts=[]
        for t2,x2,y2 in items:
            if re.match(r"^[IQ]\d{4}\.\d$",t2): continue
            if x2>x-50 and x2<x+450 and abs(y2-y)<120:
                nearby_texts.append(t2)
                if mode=="signal":
                    sm=re.search(r"(S\d{4}_\S+)",t2)
                    if sm: signal_name=sm.group(1)
        if mode=="signal" and signal_name: desc=signal_name
        else:
            desc=" ".join(nearby_texts).strip()[:80]
            desc=re.sub(r'M12A编码(公头|母头)\d*芯','',desc)
            desc=re.sub(r'\s+',' ',desc).strip()
            if len(desc)>60:
                cn=re.findall(r'[\u4e00-\u9fff]+',desc)
                if cn: desc=''.join(cn)[:50]
        io_type="DIO (IOLINK-I)" if t.startswith("I") else "DIO (IOLINK-Q)"
        records.append({"address":t,"device_tag":"","description":desc,"module":module_name,"io_type":io_type,"page":pn,"bit":""})
    return records
