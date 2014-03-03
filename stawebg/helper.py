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

def isIndex(filename, site):
    """ Checks if file is an index file.

    :param filename: Filename to check
    :type filename: str

    :param site: Relevant site (for configuration)
    :type site: :class:`stawebg.site.Site`

    :rtype: bool
    """
    if not isCont(filename, site):
        return False

    return matchList(matchPath(filename, site), site.getConfig(['files', 'index']))


def isCont(filename, site):
    """ Checks if file is content for the page
    (text that will be converted to HTML).

    :param filename: Filename to check
    :type filename: str

    :param site: Relevant site (for configuration)
    :type site: :class:`stawebg.site.Site`

    :rtype: bool
    """
    if not os.path.isfile(filename):
        return False

    return matchList(matchPath(filename, site), site.getConfig(['files', 'content']))


def isExcluded(filename, site, config):
    """ Checks if file is excluded by current configuration.

    :param filename: Filename to check
    :type filename: str

    :param site: Relevant site (for configuration)
    :type site: :class:`stawebg.site.Site`

    :param config: Configuration that contains exclude rules.
    :type config: :class:`stawebg.config.Config`

    :rtype: bool
    """
    exclude_list = config.get(['files', 'exclude'], False, [])
    return matchList(matchPath(filename, site), exclude_list)


def isHidden(filename, site, config):
    """ Checks if file is hidden by current configuration.

    :param filename: Filename to check
    :type filename: str

    :param site: Relevant site (for configuration)
    :type site: :class:`stawebg.site.Site`

    :param config: Configuration that contains hidden rules.
    :type config: :class:`stawebg.config.Config`

    :rtype: bool
    """
    hidden_list = config.get(['files', 'hidden'], False, [])
    return matchList(matchPath(filename, site), hidden_list)


def matchPath(filename, site):
    """ Get relative path of filename to source path of site.

    :param filename: Filename which relative path should be returned
    :type filename: str

    :param site: Relevant site (for source path)
    :type site: :class:`stawebg.site.Site`

    :rtype: str
    """
    abs_filename = os.path.abspath(filename)
    abs_src_path = os.path.abspath(site.getAbsSrcPath())
    return os.path.relpath(abs_filename, abs_src_path)
    #return os.path.abspath(filename)[len(os.path.abspath(site.getAbsSrcPath()))+1:]


#
# Debug and errors
#


def fail(text):
    """ Print error message and exit with return code 1.

    :param text: Error message.
    :type text: str
    """
    sys.stderr.write(text + os.linesep)
    sys.exit(1)
