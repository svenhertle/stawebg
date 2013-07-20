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


def fail(text):
    sys.stderr.write(text + "\n")
    sys.exit(1)
