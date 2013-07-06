#!/usr/bin/python3

import os
import sys
import shutil
import errno

#
# File IO
#

def listFolders(path):
    # Get absolute names of all files
    files = os.listdir(path)

    result = []

    # Join paths and check if directory
    for f in files:
        absf = os.path.join(path, f)
        if os.path.isdir(absf):
            result.append(f)

    return result

def findFiles(path, exclude_ext=[]):
    # Get absolute names of all files
    files = os.listdir(path)

    result = []

    # Join paths and go into directories
    for f in files:
        absf = os.path.join(path, f)

        if os.path.isdir(absf):
            result.extend(findFiles(absf))
        else:
            if not stringEndsWith(absf, exclude_ext):
                result.append(absf)


    return result

def copyFile(src, dir):
    dest = os.path.join(dir, os.path.basename(src))

    shutil.copy(src, dest)

def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def isMarkdown(path):
    return os.path.splitext(path)[0] == ".md"

def listToPath(lst, prefix=""):
    tmp = prefix

    for l in lst:
        tmp = os.path.join(tmp, l)

    return tmp

#
# Lists
#

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

#
# Strings
#

def cleverCapitalize(text):
    if len(text) == 0:
        return ""
    elif len(text) == 1:
        return text.upper()
    else:
        return text[0].upper() + text[1:]

def stringEndsWith(string, extensions):
    for e in extensions:
        if string.endswith(e):
            return True

    return False

#
# Debug and errors
#

def debug(text):
    print(text)

def fail(text):
    print(text, file=sys.stderr)
    sys.exit(1)
