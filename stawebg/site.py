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

class Site:
    def __init__(self, name, project):
        self._project = project
        self._name = name
        self._root = None
        self._other_files = []
        self._config = self._project._config
        self._layouts = []
        self._file_index = []
        print("Found site: " + self._name)

    def getConfig(self, key, fail=True, default=None):
        return self._config.get(key, fail, default)

    def getAbsSrcPath(self):
        return os.path.join(self.getConfig(['dirs', "sites"]), self._name)

    def getAbsDestPath(self):
        return os.path.join(self._project.getOutputDir(), self._name)

    def getProject(self):
        return self._project

    def getRoot(self):
        return self._root

    def getSiteTitle(self):
        return self.getConfig(["title"], False, self._name)

    def getSiteSubtitle(self):
        return self.getConfig(["subtitle"], False, "")

    def read(self):
        # read site specific config
        filename = os.path.join(self.getConfig(["dirs", "sites"]),
                                self._name + ".json")
        if not os.path.isfile(filename):
            fail("Can't find config file: " + filename)
        site_config = Config(filename, Config.site_struct)
        self._config = Config.merge(self._config, site_config, True)

        # create file index
        path = self.getAbsDestPath()
        if os.path.isdir(path):
            self._file_index = findFiles(path)

        # read all pages
        self._readHelper(self.getAbsSrcPath(), self._root)

    def copy(self):
        print("Create site: " + self._name)

        # Pages
        self._root.copy()

        # Layouts
        for l in self._layouts:
            l.copy(self.getAbsDestPath(), self)

        # Other files
        for f in self._other_files:
            f.copy(self)

        # Cleanup
        if self.getConfig(["delete-old"], False, 0):
            # remove files contained in the index
            for f in self._file_index:
                print("\tRemove old file: " + f)
                try:
                    os.remove(f)
                except OSError as e:
                    print("\tError: " + str(e))

            # Delete empty directories
            while True:
                deleted = False
                for d in findDirs(self.getAbsDestPath()):
                    if not os.listdir(d):
                        deleted = True
                        print("\tRemove empty directory: " + d)
                        try:
                            os.rmdir(d)
                        except OSError as e:
                            print("\tError: " + str(e))
                if not deleted:
                    break
        elif len(self._file_index) != 0:
            # Print old files
            print("This are old files:")
            for f in self._file_index:
                print("\t" + f)

    def _readHelper(self, dir_path, parent, dir_hidden=False, page_config=None):
        index_rename = None
        if page_config:
            index_rename = page_config.get(["files", "rename",
                                            os.path.basename(dir_path)], False)
            page_config.delete(["files", "sort"], False)
            page_config.delete(["files", "rename"], False)
        else:
            page_config = self._config

        entries = sorted(os.listdir(dir_path))

        idx = None
        if "stawebg.json" in entries:
            tmp_config = Config(os.path.join(dir_path, "stawebg.json"),
                                Config.directory_struct)
            page_config = Config.merge(page_config, tmp_config, False)

        # Add layout to list -> copy later
        layout = self._project.getLayout(page_config.get(["layout"], False))
        if layout not in self._layouts:
            self._layouts.append(layout)

        # First we have to find the index file in this directory…
        idx = None
        for f in entries:
            absf = os.path.join(dir_path, f)
            if isFile(absf) and isCont(absf, self) and isIndex(absf, self):
                if index_rename:
                    page_config.add(["files", "rename", f], index_rename)
                idx = Page(os.path.split(dir_path)[1], absf, self, parent,
                           dir_hidden or isHidden(absf, self, page_config),
                           page_config)
                entries.remove(f)
                break
        # …or create an empty page as index
        if not idx:
            dirname = os.path.split(dir_path)[1]
            if index_rename:
                page_config.add(["files", "rename", None], index_rename)
            idx = Page(dirname, None, self, parent, dir_hidden or
                       isHidden(dirname, self, page_config), page_config)

        if parent:
            parent.appendPage(idx)
        else:
            self._root = idx

        # Sort entries as specified in configuration
        sorted_entries = page_config.get(["files", "sort"], False, [])
        for s in reversed(sorted_entries):
            absf = os.path.join(dir_path, s)
            if not s in entries:
                print("\tFile not found (specified in sort): " + absf)
            else:
                entries.remove(s)
                entries.insert(0, s)

        # Make absolute paths and check if it's a content page or excludes
        for f in entries:
            absf = os.path.join(dir_path, f)
            if isExcluded(absf, self, page_config):
                continue
            hidden = dir_hidden or isHidden(absf, self, page_config)

            # Content file -> Page
            if isFile(absf) and isCont(absf, self):
                print("\tFound page: " + absf)
                idx.appendPage(Page(os.path.splitext(f)[0], absf, self, idx,
                                    hidden, page_config))
            # Directory -> Go inside
            elif os.path.isdir(absf):
                print("\tFound dir:  " + absf)
                self._readHelper(absf, idx, hidden, page_config.copy())
            # Unknown object
            else:
                tmp = OtherFile(self.getAbsSrcPath(),
                                os.path.relpath(absf, self.getAbsSrcPath()),
                                self.getAbsDestPath())
                self._other_files.append(tmp)
                print("\tFound unkown object: " + absf)

    def createMenu(self, cur_page):
        return self._root.createMenu(cur_page)

    def delFromFileIndex(self, path):
        if path in self._file_index:
            self._file_index.remove(path)


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
