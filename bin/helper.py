#!/usr/bin/python3

import os
import shutil

def listFolders(path):
    # Get absolute names of all files
    files = os.listdir(path)

    result = []

    # Make absolute pathes and check if directory
    for f in files:
        absf = os.path.join(path, f)
        if os.path.isdir(absf):
            result.append(f)

    return result

def isPageFile(path):
    return os.path.isfile(path) and path.endswith(".html") # TODO: move .html to config

def cleverCapitalize(text):
    if len(text) == 0:
        return ""
    elif len(text) == 1:
        return text.upper()
    else:
        return text[0].upper() + text[1:]

def copyFileToDir(src, dir):
    tmp_in = open(src, 'r')
    tmp_out = open(os.path.join(dir, os.path.basename(src)), 'w')

    for l in tmp_in:
        tmp_out.write(l)

    tmp_in.close()
    tmp_out.close()

def copyFile(src, dir):
    dest = os.path.join(dir, os.path.basename(src))

    shutil.copy(src, dest)

def listBeginsWith(lst, begin):
    if len(begin) > len(lst):
        return False

    if len(begin) == 0 and len(lst) == 0:
        return True

    if len(begin) == 0 or len(lst) == 0:
        return False

    for i,k in enumerate(begin):
        if lst[i] != begin[i]:
            return False

    return True

def listInsertUnique(lst, item):
    if not item in lst:
        lst.append(item)

def debug(text):
    print(text)
