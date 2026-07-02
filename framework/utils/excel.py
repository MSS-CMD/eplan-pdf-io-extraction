# -*- coding: utf-8 -*-
"""Excel export utilities"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from collections import Counter

TYPE_FILLS = {
    "DI": PatternFill(start_color="D6E4F0",end_color="D6E4F0",fill_type="solid"),
    "DQ": PatternFill(start_color="E2EFDA",end_color="E2EFDA",fill_type="solid"),
    "安全输入(FDI)": PatternFill(start_color="FFF2CC",end_color="FFF2CC",fill_type="solid"),
    "安全输出(FDQ)": PatternFill(start_color="FCE4D6",end_color="FCE4D6",fill_type="solid"),
    "DIO (IOLINK-I)": PatternFill(start_color="FFF2CC",end_color="FFF2CC",fill_type="solid"),
    "DIO (IOLINK-Q)": PatternFill(start_color="FCE4D6",end_color="FCE4D6",fill_type="solid"),
    "阀岛(FDQ)": PatternFill(start_color="F2DCDB",end_color="F2DCDB",fill_type="solid"),
    "AI": PatternFill(start_color="D9E2F3",end_color="D9E2F3",fill_type="solid"),
}
HF = Font(name="微软雅黑",bold=True,size=11,color="FFFFFF")
HFill = PatternFill(start_color="2F5496",end_color="2F5496",fill_type="solid")
DF = Font(name="微软雅黑",size=10)
AF = Font(name="Consolas",size=10,bold=True)
TB = Border(left=Side(style="thin",color="D9D9D9"),right=Side(style="thin",color="D9D9D9"),top=Side(style="thin",color="D9D9D9"),bottom=Side(style="thin",color="D9D9D9"))

def generate_excel(records, output_path, title="PLC IO 总表"):
    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]
    has_bit = any(r.get("bit") is not None and r["bit"] != "" for r in records[:10])
    has_tag = any(r.get("device_tag") for r in records[:10])
    if has_bit and has_tag:
        headers = ["序号","I/O类型","地址","Bit","描述","设备标签","模块/机架","页码"]
        cw = [6,16,12,8,40,40,55,8]
    elif has_bit:
        headers = ["序号","I/O类型","地址","Bit","描述","模块/机架","页码"]
        cw = [6,16,12,8,50,55,8]
    else:
        headers = ["序号","I/O类型","地址","描述","模块/机架","页码"]
        cw = [6,16,12,50,55,8]
    for ci,h in enumerate(headers,1):
        c = ws.cell(row=1,column=ci,value=h)
        c.font=HF; c.fill=HFill; c.alignment=Alignment(horizontal="center",vertical="center",wrap_text=True)
    for idx,rec in enumerate(records,1):
        row = idx+1
        fill = TYPE_FILLS.get(rec.get("io_type",""), PatternFill())
        vals = [idx, rec.get("io_type",""), rec.get("address","")]
        if has_bit: vals.append(rec.get("bit",""))
        vals.append(rec.get("description",""))
        if has_tag: vals.append(rec.get("device_tag",""))
        vals.append(str(rec.get("module","")).strip())
        vals.append(rec.get("page",""))
        for ci,v in enumerate(vals,1):
            c = ws.cell(row=row,column=ci,value=v)
            c.font = AF if ci==3 else DF
            c.fill = fill if ci==2 else PatternFill()
            hl = "center" if ci in (1,2,3,4,8) else "general"
            c.alignment = Alignment(horizontal=hl, vertical="center", wrap_text=(ci>=5))
            c.border = TB
    for i,w in enumerate(cw,1): ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = "A1:"+get_column_letter(len(headers))+str(len(records)+1)

    ws2 = wb.create_sheet(title="汇总统计")
    tc = Counter(r.get("io_type","") for r in records)
    ws2.cell(row=1,column=1,value="I/O类型").font=Font(name="微软雅黑",bold=True,size=11)
    ws2.cell(row=1,column=2,value="点数").font=Font(name="微软雅黑",bold=True,size=11)
    ws2.cell(row=1,column=3,value="地址范围").font=Font(name="微软雅黑",bold=True,size=11)
    cr,total=2,0
    for t,c in tc.most_common():
        if c==0: continue
        total+=c
        rs=[r for r in records if r.get("io_type")==t]
        ar="{}~{}".format(rs[0]["address"],rs[-1]["address"]) if rs else ""
        ws2.cell(row=cr,column=1,value=t).font=DF
        ws2.cell(row=cr,column=2,value=c).font=DF
        ws2.cell(row=cr,column=3,value=ar).font=DF
        cr+=1
    ws2.cell(row=cr,column=1,value="合计").font=Font(name="微软雅黑",bold=True,size=11)
    ws2.cell(row=cr,column=2,value=total).font=Font(name="微软雅黑",bold=True,size=11)
    ws2.column_dimensions['A'].width=20
    ws2.column_dimensions['B'].width=10
    ws2.column_dimensions['C'].width=35
    wb.save(output_path)
