# -*- coding: utf-8 -*-
"""Launcher with file dialog and drag-drop support"""
import sys,os,subprocess,tkinter as tk
from tkinter import filedialog

def main():
    s=os.path.dirname(os.path.abspath(__file__))
    ex=os.path.join(s,"run_extract.py")
    if not os.path.exists(ex): print("Error: run_extract.py not found"); return
    pdf=None
    if len(sys.argv)>1: pdf=sys.argv[1]
    else:
        root=tk.Tk(); root.withdraw(); root.attributes('-topmost',True)
        pdf=filedialog.askopenfilename(title='Select EPLAN PDF',filetypes=[('PDF','*.pdf')])
        root.destroy()
    if not pdf or not os.path.exists(pdf): return
    # 用文件名作为项目名，传入run_extract
    pn=os.path.splitext(os.path.basename(pdf))[0][:30]
    subprocess.call([sys.executable,ex,pdf,pn])

if __name__=="__main__": main()
