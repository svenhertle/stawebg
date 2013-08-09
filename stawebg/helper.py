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
def getConfigFromKey(config, key, do_fail):
        for k in key:
            config = config.get(k)

            if not config:
                if do_fail:
                    fail("Can't find " + str(key))
                else:
                    return None

        return config

# Like update, but merge also dict in dict and so on
# Overrites a with b if there are e.g. two lists with different content
def mergeConfig(a, b):
    result = a.copy()

    for k in b:
        if k in result:
            if type(b[k]) == dict:
                result[k] = mergeConfig(result[k], b[k])
            else:
                result[k] = b[k]
        else:
            result[k] = b[k]

    return result

#
# Debug and errors
#


def fail(text):
    sys.stderr.write(text + "\n")
    sys.exit(1)
