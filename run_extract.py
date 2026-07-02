# -*- coding: utf-8 -*-
"""Run extraction from command line"""
import sys,os,time
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"framework"))
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"framework","framework"))
import pymupdf
from framework.core import auto_discover,auto_config,extract_all,sort_records,apply_pipeline,register
from framework.utils.excel import generate_excel
from framework.utils.text import postprocess_desc
from framework.parsers import column,iolink,valve,analog
for t,p in [("DI",column),("DQ",column),("SAFETY_IN",column),("SAFETY_OUT",column),("IOLINK",iolink),("VALVE",valve),("AI",analog)]: register(t,p.parse)

def run(pdf_path):
    t0=time.time()
    doc=pymupdf.open(pdf_path)
    print("\n[1] Scanning... ({} pages)".format(doc.page_count),flush=True)
    pm=auto_discover(doc)
    for pt,pages in sorted(pm.items()):
        if pages: print("    {}: {} pages".format(pt,len(pages)))
    print("[2] Detecting layout...",flush=True)
    cfgs=auto_config(doc,pm)
    total=sum(len(v) for v in pm.values())
    print("[3] Extracting ({} pages)...".format(total),flush=True)
    records=extract_all(doc,pm,cfgs)
    records=sort_records(records)
    records=apply_pipeline(records,[("clean",lambda r:{**r,"description":postprocess_desc(r.get("description",""))})])
    doc.close()
    output=pdf_path.replace(".pdf","_IO_总表.xlsx")
    generate_excel(records,output)
    from collections import Counter
    tc=Counter(r["io_type"] for r in records)
    print("\nI/O Summary:")
    for t,c in tc.most_common(): print("    {:20s}: {}".format(t,c))
    print("    {:20s}: {}".format("Total",len(records)))
    print("\nOutput: "+output+"\nTime: {:.0f}s".format(time.time()-t0))

if __name__=="__main__":
    if len(sys.argv)<2: print("Usage: python run_extract.py <pdf_path>"); sys.exit(1)
    run(sys.argv[1])
