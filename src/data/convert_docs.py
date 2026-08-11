"""
Python 版 doc → txt 转换。比 PowerShell 更稳定。
"""

import os
import sys

# 找到所有 .doc/.docx 文件
SOURCE = r"D:\My wordl four\裁定书"
OUTPUT = r"D:\case_txt"
os.makedirs(OUTPUT, exist_ok=True)

files_to_convert = []
for root, dirs, files in os.walk(SOURCE):
    for f in files:
        if f.endswith(('.doc', '.docx')):
            files_to_convert.append(os.path.join(root, f))

print(f"找到 {len(files_to_convert)} 个文件\n")

import pythoncom
import win32com.client

pythoncom.CoInitialize()
word = win32com.client.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = 0  # wdAlertsNone

success = 0
failed = 0

for i, filepath in enumerate(files_to_convert, 1):
    filename = os.path.basename(filepath)
    txt_name = os.path.splitext(filename)[0] + ".txt"
    txt_path = os.path.join(OUTPUT, txt_name)

    if os.path.exists(txt_path) and os.path.getsize(txt_path) > 100:
        success += 1
        continue

    try:
        doc = word.Documents.Open(filepath, ReadOnly=True, Visible=False)
        doc.SaveAs(txt_path, FileFormat=4)  # wdFormatText
        doc.Close(SaveChanges=0)
        print(f"[{i}/{len(files_to_convert)}] OK: {filename[:50]}")
        success += 1
    except Exception as e:
        print(f"[{i}/{len(files_to_convert)}] FAIL: {filename[:50]} - {e}")
        failed += 1
        try:
            doc.Close(SaveChanges=0)
        except:
            pass

word.Quit()
pythoncom.CoUninitialize()

print(f"\n{'='*50}")
print(f"完成: {success} 成功, {failed} 失败")
print(f"txt 文件在: {OUTPUT}")
