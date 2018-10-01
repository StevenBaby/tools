#!/usr/bin/python3
# coding=utf-8

import os
import shutil
import dandan

logger = dandan.logger.getLogger()

dirname = os.path.dirname(os.path.abspath(__file__))
github = os.path.dirname(dirname)

logger.info("github location %s", github)

words = os.path.join(github, 'words')

logger.info("words location %s", words)

local_before = os.path.join(words, 'words', 'local')
tmp_dir = 'tmp'
local_after = os.path.join(tmp_dir, 'local')

if os.path.exists(local_before):
    logger.info("move local location to home")
    shutil.move(local_before, local_after)

if not os.path.exists(local_after):
    logger.warning("home local not exists, exiting...")
    exit(0)

# if os.path.exists(words):
#     logger.info("remove words %s", words)
#     shutil.rmtree(words)

# url = 'https://github.com/StevenKangWei/words.git'
# command = 'git clone {} {}'.format(url, words)
# logger.info(command)
# os.system(command)

logger.info("restore local")
shutil.move(local_after, local_before)

logger.info("remove redundance dir")
if os.path.exists(tmp_dir):
    shutil.rmtree(tmp_dir)

local_local = os.path.join(local_before, 'local')
if os.path.exists(local_local):
    shutil.rmtree(local_local)
