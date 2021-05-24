
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

doc = fitz.Document('1.pdf')

for nr in range(len(doc)):
    # doc._deleteObject()
    name = f'output/{nr}.svg'
    image = doc[nr].get_svg_image()
    with open(name, 'w') as file:
        file.write(image)
    print(name)
