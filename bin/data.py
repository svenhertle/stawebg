#!/usr/bin/python3

import config
from helper import *

import errno

class Project:
    def __init__(self):
        self._sites = []

    def read(self):
        # Get all directories -> this are the sites
        sites = listFolders(config.dirs["sites"])

        # Add sites to list
        for s in sites:
            site = Site(s)
            self._sites.append(site)
            site.read()

    def copy(self):
        for s in self._sites:
            s.copy()

class Site:
    def __init__(self, name):
        self._name = name

        self._pages = []

        self._other_files = []

        debug("Found site: " + self._name)

    def getAbsSrcPath(self):
        return os.path.join(config.dirs["sites"], self._name)

    def getAbsDestPath(self):
        return os.path.join(config.dirs["out"], self._name)

    def read(self):
        self._readHelper(self.getAbsSrcPath(), [])

    def copy(self):
        # Pages
        for p in self._pages:
            p.copy()

        # Stylesheet
        copyFileToDir(config.layout["css"], self.getAbsDestPath())

        # Other files
        for f in self._other_files:
            src_path = self.getAbsSrcPath()
            for p in f:
                src_path = os.path.join(src_path, p)

            dest_dir = self.getAbsDestPath()
            if len(f) > 1:
                for p in f[0:-1]:
                    dest_dir = os.path.join(dest_dir, p)

            copyFile(src_path, dest_dir)

    def _readHelper(self, dir_path, path):
        files = os.listdir(dir_path)

        # Make absolute pathes and check if it's a page
        for f in files:
            absf = os.path.join(dir_path, f)
            # HTML File -> Page
            if isPageFile(absf):
                name = os.path.basename(absf)

                # Hidden files begin with _
                hidden = False
                if name.startswith("_") and len(name) > 1:
                    hidden = True
                    name = name[1:]

                is_index = True
                new_path = path[:]
                if name != "index.html": #TODO: -> config
                    is_index = False
                    new_path.append(os.path.splitext(name)[0])

                debug("\tFound page: " + absf)

                page = Page(self, absf, new_path, hidden, is_index)
                self._pages.append(page)
            # Directory -> Go inside
            elif os.path.isdir(absf):
                name = os.path.basename(absf)

                new_path = path[:]
                new_path.append(name)

                self._readHelper(absf, new_path)
            # Unknown object
            else:
                name = os.path.basename(absf)

                new_path = path[:]
                new_path.append(name)

                self._other_files.append(new_path)

                debug("\tFound unkown object: " + absf)

    def createMenu(self, cur_page):
        return self._createMenuHelper(1, cur_page, False)

    def _createMenuHelper(self, level, cur_page, last):
        items = []
        home = None # Add home later to begin of list of items

        # Collect items
        for p in self._pages:
            if level == 1 and len(p.getPath()) <= 1:
                # Home / in list -> don't add now -> add it later to the begin of the sorted list of items
                if len(p.getPath()) == 0:
                    home = p
                    continue
                listInsertUnique(items, p)
            # Until cur_page
            elif listBeginsWith(cur_page.getPath(), p.getPath()[0:-1]) and len(p.getPath()) == level:
                listInsertUnique(items, p)
            # After cur_page
            elif listBeginsWith(p.getPath(), cur_page.getPath()) and len(p.getPath()) == level:
                listInsertUnique(items, p)

        # Sort items
        items = sorted(items, key=lambda i: i.getShortTitle())
        if home:
            items.insert(0, home)

        # Create HTML Code
        found=False
        tmp = "<ul>\n"
        for p in items:
            if p == cur_page:
                found=True

            if p.isHidden():
                continue

            active=""
            if p == cur_page or listBeginsWith(cur_page.getPath(), p.getPath()):
                active="class=\"active\""

            tmp += "<li><a href=\" " + p.getLink(cur_page) + "\" " + active + ">" + p.getShortTitle() + "</a></li>\n"

            # Create submenu
            if listBeginsWith(cur_page.getPath(), p.getPath()) and not last:# and len(p.getPath()) != 0: # Subdir AND current site not yet displayed AND not home /
                tmp += self._createMenuHelper(level+1, cur_page, found)

        tmp += "</ul>\n"

        return tmp

class Page:
    def __init__(self, site, absPath, path, hidden, is_index):
        self._site = site

        self._absSrc = absPath

        self._path = path

        self._hidden = hidden

        # was index.html in original file structure (important for %CUR%)
        self._is_index = is_index

    def getPath(self):
        return self._path

    def isHidden(self):
        return self._hidden

    def copy(self):
        # Create directory
        try:
            os.makedirs(os.path.dirname(self._getDestFile()))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        # Write to file
        outf = open(self._getDestFile(), 'w')

        self._appendAndReplaceFile(outf, config.layout["head"])
        self._appendAndReplaceFile(outf, self._absSrc)
        self._appendAndReplaceFile(outf, config.layout["bottom"])

        outf.close()

    def _appendAndReplaceFile(self, to, src):
        tmp = open(src, 'r')
        for l in tmp:
            new = self._replaceKeywords(l)
            to.write(new)
        tmp.close()

    def _replaceKeywords(self, line):
        # %ROOT%
        new = line.replace("%ROOT%", self.getRootLink())

        # %CUR%
        new = new.replace("%CUR%", self.getCurrentLink())

        # %TITLE%
        new = new.replace("%TITLE%", self._getTitle())

        # %MENU%
        new = new.replace("%MENU%", self._site.createMenu(self))

        return new

    def _getDestFile(self):
        result = self._site.getAbsDestPath()

        for p in self._path:
            result = os.path.join(result, p)

        return os.path.join(result, "index.html") #TODO: -> config

    def getRootLink(self):
        return "../" * len(self._path)

    def getCurrentLink(self):
        if self._is_index:
            return ""
        else:
            return "../"

    def getLink(self, origin=None):
        if not origin:
            origin = self

        tmp = origin.getRootLink()

        for t in self.getPath():
            tmp += t + "/"

        if tmp == "":
            tmp = "."

        return tmp

    def getShortTitle(self):
        if len(self._path) == 0:
            return "Home" # TODO: use page title
        else:
            last = len(self._path) - 1
            return cleverCapitalize(self._path[last])

    def _getTitle(self):
        if len(self._path) == 0:
            return "Home" # TODO: use page title
        else:
            result = ""
            for t in self._path:
                if len(result) == 0:
                    result = cleverCapitalize(t)
                else:
                    result += " > " + cleverCapitalize(t)

        return result
