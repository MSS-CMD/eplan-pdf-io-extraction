# -*- coding: utf-8 -*-
"""Launcher with file dialog and drag-drop support"""
import sys,os,subprocess,tkinter as tk
from tkinter import filedialog

def main():
    script_dir=os.path.dirname(os.path.abspath(__file__))
    extract_script=os.path.join(script_dir,"run_extract.py")
    if not os.path.exists(extract_script):
        print("Error: run_extract.py not found"); input("Enter to exit..."); return
    pdf=None
    if len(sys.argv)>1: pdf=sys.argv[1]
    else:
        root=tk.Tk(); root.withdraw(); root.attributes('-topmost',True)
        pdf=filedialog.askopenfilename(title='Select EPLAN PDF',filetypes=[('PDF','*.pdf')])
        root.destroy()
    if not pdf or not os.path.exists(pdf):
        if pdf: print("File not found:",pdf)
        return
    subprocess.call([sys.executable,extract_script,pdf])
    input("\nEnter to exit...")

if __name__=="__main__": main()
