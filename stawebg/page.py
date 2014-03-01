#!/usr/bin/python3

import locale
import os
import re
import shutil
from datetime import datetime
from subprocess import Popen, PIPE
from stawebg.config import Config
from stawebg.helper import (listFolders, findFiles, findDirs, fail, matchList,
                            cleverCapitalize, mkdir)

class Page:
    def __init__(self, name, absPath, site, parent, hidden, config):
        self._name = name
        self._absSrc = absPath
        self._site = site
        self._hidden = hidden
        self._parent = parent
        self._subpages = []
        self._config = config
        self._content = None

        self._site.delFromFileIndex(self._getDestFile())

    def setContent(self, content, extension):
        self._content = (content, extension)

    def appendPage(self, p):
        self._subpages.append(p)

    def getParent(self):
        return self._parent

    def getName(self):
        return self._name

    def isRoot(self):
        return self._parent is None

    def isHidden(self):
        return self._hidden

    def getLayout(self):
        layout = self._config.get(["layout"], False)
        return self._site.getProject().getLayout(layout)

    def getReps(self):
        return {"%ROOT%": self.getRootLink(),
                "%CUR%": self.getCurrentLink(),
                "%LAYOUT%": self.getLayoutDir(),
                "%TITLE%": self.getTitle(),
                "%SITETITLE%": self._site.getSiteTitle(),
                "%SITESUBTITLE%": self._site.getSiteSubtitle(),
                "%MENU%": self._site.createMenu(self),
                "%VERSION%": version,
                "%GENERATIONTIME%": datetime.now().strftime(self._config.get(["timeformat"], False, "%c")),
                "%GENERATIONYEAR%": datetime.now().strftime("%Y"),
                "%URL%": self._config.get(["url"], False, "")}

    def copy(self):
        user_reps = self._config.get(["variables"], False, [])

        # regular file
        output = ""
        content = ""
        if not self._content:
            output, content = self.getLayout().useTemplate(self._absSrc, self.getReps(), user_reps)
        else:
            output, content = self.getLayout().useTemplate(self._content[0], self.getReps(), user_reps, self._content[1])

        self.getLayout().createOutput(self._getDestFile(), output)

        # Copy subpages
        for p in self._subpages:
            p.copy()

    def _getDestFile(self):
        tmp_path = ""

        parent = self.getParent()
        while parent and not parent.isRoot():
            tmp_path = os.path.join(parent.getName(), tmp_path)
            parent = parent.getParent()

        if not self.isRoot():
            tmp_path = os.path.join(tmp_path, self.getName())

        return os.path.join(self._site.getAbsDestPath(), tmp_path, "index.html")

    def getRootLink(self):
        tmp = ""

        parent = self.getParent()
        while parent:
            tmp = tmp + "../"
            parent = parent.getParent()

        return tmp

    def getCurrentLink(self):
        return '' if self._absSrc and isIndex(self._absSrc, self._site) else '../'

    def getLayoutDir(self):
        return self.getRootLink() + self.getLayout().getSubdir() + "/"

    def getLink(self, origin=None):
        tmp = ""
        parent = self
        while parent and not parent.isRoot():
            tmp = parent.getName() + "/" + tmp
            parent = parent.getParent()

        if not origin:
            origin = self

        tmp = origin.getRootLink() + tmp

        if tmp == "":
            tmp = "./"

        return tmp

    def getShortTitle(self):
        key = None
        if self._absSrc:
            key = os.path.basename(self._absSrc)

        rename = self._config.get(["files", "rename", key], False)

        if rename:
            return rename
        elif not self.getParent():
            return "Home"
        else:
            return cleverCapitalize(self.getName())

    def getTitle(self, no_home=False):
        if not self.getParent():
            if no_home:
                return self._site.getSiteTitle()
            else:
                return self._site.getSiteTitle() + " > " + self.getShortTitle()
        else:
            return self.getParent().getTitle(True) + " > " + self.getShortTitle()

    def createMenu(self, cur_page, last=False):
        items = self._subpages[:]

        # Add root link
        if self.isRoot():
            items.insert(0, self)

        # Create HTML Code
        found = False
        tmp = ""
        for p in items:
            if p == cur_page:
                found = True

            if p.isHidden():
                continue

            active = ""
            if p._pageIsInPathTo(cur_page) and (not p.isRoot() or p == cur_page):
                active = " class=\"active\""

            tmp = ''.join([tmp, "<li><a href=\"", p.getLink(cur_page), "\"",
                          active, ">", p.getShortTitle(), "</a></li>\n"])

            # Create submenu
            if not p.isRoot() and p._pageIsInPathTo(cur_page) and not last:
                tmp += p.createMenu(cur_page, found)

        return "<ul>\n" + tmp + "</ul>\n" if tmp else ""

    def _pageIsInPathTo(self, dest):
        parent = dest
        while parent:
            if parent == self:
                return True
            parent = parent.getParent()

        return False
