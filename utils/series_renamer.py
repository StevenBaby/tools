import os
import glob
import re


ext = "mkv"
pattern = r"EP(\d\d).*\.{}".format(ext)

files = glob.glob("*.{}".format(ext))

for src in files:
    match = re.search(pattern, src)
    if not match:
        continue
    num = match.group(1)
    dest = "{}.{}".format(num, ext)
    print(src, dest)
    os.rename(src, dest)
