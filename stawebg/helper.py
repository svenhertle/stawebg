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
            if not absf.endswith(tuple(exclude_ext)):
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

#
# Configuration
#
def getConfigFromKey(config, key, fail, filename):
        for k in key:
            if not config:
                if fail:
                    fail("Can't find " + str(key) + " in " + filename)
                else:
                    break

            config = config.get(k)

        return config

#
# Debug and errors
#


def fail(text):
    sys.stderr.write(text + "\n")
    sys.exit(1)
