#!/usr/bin/python3
# -*- coding: utf-8 -*-

import errno
import os
import re
import sys

#
# File IO
#


def listDirs(path):
    """ Get absolute names of all directories in a given directory.

    :param path: Path of the directory.
    :type path: str

    :rtype: list of str
    """
    files = os.listdir(path)

    result = []

    # Join paths and check if directory
    for f in files:
        absf = os.path.join(path, f)
        if os.path.isdir(absf):
            result.append(f)

    return result


def findFiles(path, exclude_ext=[]):
    """ Get absolute names of all files in a given directory (recursive).

    All filenames ending with a string from exclude_list are excluded.

    :param path: Path of the directory.
    :type path: str

    :param exclude_ext: file extensions that are exluded (like .php)
    :type exclude_ext: list of str

    :rtype: list of str
    """
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
    """ Get absolute names of all directories in a given directory (recursive).

    :param path: Path of the directory.
    :type path: str

    :rtype: list of str
    """
    dirs = listDirs(path)

    result = []

    for d in dirs:
        tmp = os.path.join(path, d)
        result.append(tmp)
        result.extend(findDirs(tmp))

    return result


def mkdir(path):
    """ Create directory. Prints error and exits if there was an error.

    Nothing happpens if the directory already exists.

    :param path: Path of the directory.
    :type path: str
    """
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            fail(str(e))


#
# Strings and Regex
#


def cutStr(text, length):
    """ Shorten string to max. given length.

    Adds ... to the end is string is longer.

    .. todo:: old, needed for RSS?

    :param text: String for shortening.
    :type text: str

    :param length: Maximal length
    :type length: int

    :rtype: str
    """
    if length == 0 or len(text) <= length:
        return text
    return text[0:length-4] + "..."


def matchList(string, regex_lst):
    """ Check if a string matches on of the given regexes.

    :param string: String to match
    :type string: str

    :param regex_lst: List of regular expressions.
    :type regex_lst: list of str

    :rtype: bool
    """
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

def isIndex(f, site):
    if not isCont(f, site):
        return False

    return matchList(matchPath(f, site), site.getConfig(['files', 'index']))


def isCont(f, site):
    if not os.path.isfile(f):
        return False

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
