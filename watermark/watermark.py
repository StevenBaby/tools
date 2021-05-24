
# coding=utf-8

import os
import sys

import fitz

'''
pip install pymupdf
'''

if len(sys.argv) < 2:
    print("use watermark.py filename.pdf")
    exit(0)

if not os.path.exists(sys.argv[1]):
    print("file not exists")
    exit(0)

dirname = os.path.dirname(__file__)

if not os.path.exists("output"):
    os.makedirs('output')


doc = fitz.open(sys.argv[1])

for nr in range(len(doc)):
    images = doc.getPageImageList(nr)
    if not images:
        continue

    maxsize = 0
    image = None
    for var in images:
        size = var[2] * var[3]
        if maxsize < size:
            image = var
            maxsize = size

    xref = image[0]

    pix = fitz.Pixmap(doc, xref)
    name = f"output/{nr}.png"
    if pix.n < 5:       # this is GRAY or RGB
        pix.writePNG(name)
    else:               # CMYK: convert to RGB first
        pix1 = fitz.Pixmap(fitz.csRGB, pix)
        pix1.writePNG(name)
    print(name, pix)
