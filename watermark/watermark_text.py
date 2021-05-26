
# coding=utf-8

import os
import sys

import fitz

'''
pip install pymupdf
'''

dirname = os.path.dirname(__file__)
os.chdir(dirname)

if not os.path.exists("output"):
    os.makedirs('output')

doc = fitz.Document('input.pdf')

for page in doc:
    print(page)
    rects = page.searchFor("watermark.....")
    for rect in rects:
        page.addRedactAnnot(rect)
        print(rect)
    page.apply_redactions()


doc.save('output.pdf')
