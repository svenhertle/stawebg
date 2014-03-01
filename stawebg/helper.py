#!/usr/bin/python3
# -*- coding: utf-8 -*-

import errno
import os
import re
import sys

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
    try:
        files = os.listdir(path)
    except OSError as e:
        fail("Can't open directory: " + str(e))

    result = []

    # Join paths and go into directories
    for f in files:
        absf = os.path.join(path, f)

        if os.path.isdir(absf):
            result.extend(findFiles(absf, exclude_ext))
        else:
            if not absf.endswith(tuple(exclude_ext)):
                result.append(absf)

    return result


def findDirs(path):
    dirs = listFolders(path)

    result = []

    for d in dirs:
        tmp = os.path.join(path, d)
        result.append(tmp)
        result.extend(findDirs(tmp))

    return result


def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            fail(str(e))


#
# Strings and Regex
#


def cleverCapitalize(text):
    if len(text) == 0:
        return ""
    else:
        return text[0].upper() + text[1:]


# TODO: old, needed for RSS?
def cutStr(text, length):
    if length == 0 or len(text) <= length:
        return text
    return text[0:length-4] + "..."


def matchList(string, regex_lst):
    for r in regex_lst:
        try:
            if re.match(r, string):
                return True
        except re.error as e:
            fail("Error in regular expression \"" + r + "\": " + str(e))

    return False

#
# Recognition of file types
#


def isFile(f):
    return os.path.isfile(f)


def isIndex(f, site):
    if not (isFile(f) and isCont(f, site)):
        return False

    return matchList(matchPath(f, site), site.getConfig(['files', 'index']))


def isCont(f, site):
    return matchList(matchPath(f, site), site.getConfig(['files', 'content']))


def isExcluded(f, site, c):
    return matchList(matchPath(f, site), c.get(['files', 'exclude'],
                                               False, []))


def isHidden(f, site, c):
    return matchList(matchPath(f, site), c.get(['files', 'hidden'], False, []))


def matchPath(f, c):
    return os.path.abspath(f)[len(os.path.abspath(c.getAbsSrcPath()))+1:]


#
# Debug and errors
#


def fail(text):
    sys.stderr.write(text + os.linesep)
    sys.exit(1)
