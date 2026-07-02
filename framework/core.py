# -*- coding: utf-8 -*-
"""Core engine v2.4 - external config.json support"""
import json,os,re,sys
from collections import Counter

_cfg_path=os.path.join(os.path.dirname(__file__),"config.json")
if getattr(sys,'frozen',False):
    _exe_cfg=os.path.join(os.path.dirname(sys.executable),"config.json")
    if os.path.exists(_exe_cfg): _cfg_path=_exe_cfg
_config={}
if os.path.exists(_cfg_path):
    with open(_cfg_path,encoding="utf-8") as f: _config=json.load(f)

_PAGE_KW=_config.get("页面类型关键词",{"DI":["数字量输入模块 16位"],"DQ":["数字量输出模块 16位"],"SAFETY_IN":["安全输入模块"],"SAFETY_OUT":["安全输出模块"],"IOLINK":["IOLINK_数字量可分配模块"],"VALVE":["阀岛阀片总览"],"AI":["模拟量输入"]})
_COL_LAYOUTS=_config.get("列布局模板",{"EPLAN_S7_1500_标准":{"DI":{"bit_label_re":r"^(DI|FDI) Bit (\d+)$","address_re":r"^I\d{4}\.\d$","bit_label_y":571,"address_y_range":[580,605],"device_tag_y_range":[590,615],"desc_y_range":[665,715]},"DQ":{"bit_label_re":r"^DO Bit (\d+)$","address_re":r"^Q\d{4}\.\d$","bit_label_y":178,"address_y_range":[148,172],"device_tag_y_range":[140,160],"desc_y_range":[665,715]}}})
_SO_CFG=_config.get("安全输出布局",{"bit_label_re":r"^DQ-P(\d+)\.?$","address_re":r"^Q1110\.\d$","bit_label_y":178,"address_y_range":[148,172],"desc_y_range":[665,715]})
_IOL_CFG=_config.get("IOLINK模式检测",{"signal_pattern":r"S\d{4}_","search_radius_x":450,"search_radius_y":120})
_parsers={}
def register(pt,fn): _parsers[pt]=fn
def get_parser(pt): return _parsers.get(pt)

def auto_discover(doc):
    pm={k:[] for k in _PAGE_KW}
    for i in range(doc.page_count):
        text=doc[i].get_text(); pn=i+1
        if "目录 : =" in text or "HC_CONTENTS" in text: continue
        for pt,kws in _PAGE_KW.items():
            if any(kw in text for kw in kws):
                if pt in ("DI","DQ","SAFETY_IN") and " Bit " not in text: continue
                pm[pt].append(pn); break
    return pm

def _to_ranges(pages):
    if not pages: return "无"
    r=[]; s=pr=pages[0]
    for p in pages[1:]:
        if p>pr+2: r.append("{}-{}".format(s,pr)); s=p
        pr=p
    r.append("{}-{}".format(s,pr))
    return ", ".join(r)

def print_page_map(pm):
    print("="*40); print("页面类型"); print("="*40); total=0
    for pt,pages in sorted(pm.items()):
        if pages: print("  {:12s}: {}页".format(pt,len(pages))); total+=len(pages)
    print("  {:12s}: {}页".format("合计",total))

def _get_items(page):
    items=[]
    for b in page.get_text("dict")["blocks"]:
        if b["type"]==0:
            for line in b["lines"]:
                t="".join(s["text"] for s in line["spans"]).strip()
                if t: items.append((t,(line["bbox"][0]+line["bbox"][2])/2,line["bbox"][1]))
    return items

def _detect_di(items):
    bits=[y for t,x,y in items if re.match(r"^(DI|FDI) Bit \d+$",t)]
    if not bits: return None
    bit_y=round(sum(bits)/len(bits),1)
    addrs=[(t,x,y) for t,x,y in items if re.match(r"^I\d{4}\.\d$",t) and bit_y+8<y<bit_y+40]
    if not addrs: return None
    addr_y=round(sum(y for _,_,y in addrs)/len(addrs),1)
    descs=[(t,y) for t,x,y in items if re.search(r"[\u4e00-\u9fff]",t) and bit_y+95<y<bit_y+150 and "Bit" not in t and not any(k in t for k in ["版权","授权","项目","图纸","日期","设计","审核","批准","徐工","江苏"])]
    desc_y=round(min(y for _,y in descs),1) if descs else bit_y+110
    tags=[(t,y) for t,x,y in items if (t.startswith("+") or t.startswith("-")) and bit_y+15<y<bit_y+45]
    tag_y=round(sum(y for _,y in tags)/len(tags),1) if tags else None
    return {"bit_label_re":r"^(DI|FDI) Bit (\d+)$","address_re":r"^I\d{4}\.\d$","bit_label_y":bit_y,"address_y_range":[addr_y-10,addr_y+10],"device_tag_y_range":[tag_y-8,tag_y+8] if tag_y else None,"desc_y_range":[desc_y-5,desc_y+35]}

def _detect_dq(items):
    bits=[y for t,x,y in items if re.match(r"^DO Bit \d+$",t)]
    if not bits: return None
    bit_y=round(sum(bits)/len(bits),1)
    addrs=[(t,x,y) for t,x,y in items if re.match(r"^Q\d{4}\.\d$",t) and bit_y-35<y<bit_y-5]
    if not addrs: return None
    addr_y=round(sum(y for _,_,y in addrs)/len(addrs),1)
    descs=[(t,y) for t,x,y in items if re.search(r"[\u4e00-\u9fff]",t) and y>bit_y+450 and "Bit" not in t and not any(k in t for k in ["版权","授权","项目","图纸","日期","设计","审核","批准","徐工","江苏"])]
    desc_y=round(min(y for _,y in descs),1) if descs else bit_y+500
    tags=[(t,y) for t,x,y in items if (t.startswith("+") or t.startswith("-")) and bit_y-40<y<bit_y-10]
    tag_y=round(sum(y for _,y in tags)/len(tags),1) if tags else None
    return {"bit_label_re":r"^DO Bit (\d+)$","address_re":r"^Q\d{4}\.\d$","bit_label_y":bit_y,"address_y_range":[addr_y-10,addr_y+10],"device_tag_y_range":[tag_y-8,tag_y+8] if tag_y else None,"desc_y_range":[desc_y-5,desc_y+35]}

def _match_tmpl(items,io_type):
    for tname,lay in _COL_LAYOUTS.items():
        if io_type in lay:
            cfg=lay[io_type]
            bits=[y for t,x,y in items if re.match(cfg["bit_label_re"],t)]
            if bits and abs(sum(bits)/len(bits)-cfg["bit_label_y"])<15: return tname,cfg
    return None,None

def auto_config(doc,pm):
    configs={}
    for pt in ("DI","DQ"):
        if not pm.get(pt): continue
        items=_get_items(doc[pm[pt][0]-1])
        det=_detect_di(items) if pt=="DI" else _detect_dq(items)
        if det: det["io_type"]=pt; configs[pt]=det
        else:
            tn,tmpl=_match_tmpl(items,pt)
            if tmpl: configs[pt]={**tmpl,"io_type":pt}
    if pm.get("SAFETY_IN"):
        items=_get_items(doc[pm["SAFETY_IN"][0]-1])
        det=_detect_di(items)
        tn,_=_match_tmpl(items,"DI")
        if det: configs["SAFETY_IN"]={**det,"io_type":"安全输入(FDI)"}
        elif tn: configs["SAFETY_IN"]={**_COL_LAYOUTS[tn].get("DI",{}),"io_type":"安全输入(FDI)"}
    if pm.get("SAFETY_OUT"):
        real=[]
        for pn in pm["SAFETY_OUT"]:
            items=_get_items(doc[pn-1])
            if any(re.match(_SO_CFG["bit_label_re"],t) for t,x,y in items):
                real.append(pn)
                if "SAFETY_OUT" not in configs: configs["SAFETY_OUT"]={**_SO_CFG,"io_type":"安全输出(FDQ)"}
        pm["SAFETY_OUT"]=real
    if pm.get("IOLINK"):
        s=doc[pm["IOLINK"][0]-1].get_text()
        configs["IOLINK"]={"mode":"signal" if re.search(_IOL_CFG.get("signal_pattern",r"S\d{4}_"),s) else "connector"}
    if pm.get("VALVE"): configs["VALVE"]={"layout":"table","io_type":"阀岛(FDQ)","module_name":"阀岛"}
    if pm.get("AI"): configs["AI"]={"io_type":"AI"}
    return configs

def extract_all(doc,pm,configs):
    all_records=[]
    for pt,pages in pm.items():
        if not pages: continue
        p=get_parser(pt)
        if not p: print("  {}: no parser".format(pt)); continue
        cfg=configs.get(pt,{})
        for pn in pages: all_records.extend(p(doc[pn-1],pn,cfg))
    return all_records

def apply_pipeline(records,pipeline=None):
    if pipeline is None:
        from utils.text import postprocess_desc
        pipeline=[("desc_clean",lambda r:{**r,"description":postprocess_desc(r.get("description",""))})]
    for n,fn in pipeline: records=[fn(r) for r in records]
    return records

def sort_records(records):
    def key(r):
        a=r.get("address","")
        m=re.match(r"([IQ])(\d+)\.(\d)$",a)
        if m: return (0 if m.group(1)=="I" else 1, int(m.group(2)), int(m.group(3)))
        m=re.match(r"Q17(\d+)\.(\d)",a)
        if m: return (2,int(m.group(1)),int(m.group(2)))
        m=re.match(r"P[I][WQ]W?(\d+)",a)
        if m: return (3,int(m.group(1)),0)
        return (9,0,0)
    records.sort(key=key)
    return records
