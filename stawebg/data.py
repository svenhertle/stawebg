#!/usr/bin/python3

import json
import os,sys
import re
from subprocess import Popen, PIPE
from stawebg.config import Config
from stawebg.helper import (listFolders, findFiles, findDirs, copyFile, mkdir, fail,
                            matchList, cleverCapitalize)

version="0.1"

isFile = lambda f: os.path.isfile(f)
matchPath = lambda f, c: os.path.abspath(f)[len(os.path.abspath(c.getAbsSrcPath()))+1:]
isIndex = lambda f, site: matchList(matchPath(f, site), site.getConfig(['files', 'index']))
isCont = lambda f, site: matchList(matchPath(f, site), site.getConfig(['files', 'content']))
isExcluded = lambda f, site, c: matchList(matchPath(f, site), c.get(['files', 'exclude'], False, []))
isHidden = lambda f, site, c: matchList(matchPath(f, site), c.get(['files', 'hidden'], False, []))


class Project:
    def __init__(self, project_dir="", test=False):
        self._sites = []
        self._layouts = {}
        self._root_dir = project_dir
        self._test = test

        markup_struct = (list, str, True)
        config_struct = {"dirs":
                (dict, {"sites": (str, None, False),
                    "layouts": (str, None, False),
                    "out": (str, None, False),
                    "test": (str, None, True)}, False),
                "files": (dict, {"index": (list, str, True),
                    "content": (list, str, True),
                    "hidden": (list, str, True),
                    "exclude": (list, str, True)}, True),
                "markup": ("mapping", (str, markup_struct, True), True)}
        self._config = Config(os.path.join(self._root_dir, "stawebg.json"), config_struct)

        # Make directories absolute
        dirs = self._config.get(["dirs"])
        for k in dirs:
            dirs[k] = os.path.join(self._root_dir, dirs[k])

    def read(self):
        self._readLayouts()
        self._readSites()

    def copy(self):
        for s in self._sites:
            s.copy()

    def getConfig(self, key, fail=True, default=None):
        return self._config.get(key, fail, default)

    def getLayout(self, name=None):
        if not name:
            name = "default"

        layout = self._layouts.get(name)

        if not layout:
            fail("Can't find layout: " + name)

        return layout

    def getOutputDir(self):
        if self._test:
            return self.getConfig(["dirs", "test"])
        else:
            return self.getConfig(["dirs", "out"])

    # Add all layouts to list
    def _readLayouts(self):
        for name in listFolders(self.getConfig(['dirs', 'layouts'])):
            self._layouts[name] = Layout(self, name)
            self._layouts[name].read()

    # Add all site directories to list
    def _readSites(self):
        for s in listFolders(self.getConfig(['dirs', 'sites'])):
            site = Site(s, self)
            self._sites.append(site)
            site.read()


class Layout:
    def __init__(self, project, name):
        self._project = project
        self._name = name
        self._dir = os.path.join(self._project.getConfig(['dirs', 'layouts']), name)
        self._template = os.path.join(self._dir, 'template.html')
        self._other_files = []

        print("Found layout: " + self._name)

    def read(self):
        for f in findFiles(self._dir, [".html"]):
            print("\tFound file: " + f)
            self._other_files.append(OtherFile(self._dir,
                                               os.path.relpath(f, self._dir)))

    def copy(self, dest, site):
        for f in self._other_files:
            f.copy(site, os.path.join(dest, self.getSubdir()))

    def getSubdir(self):
        return os.path.join("style", self._name)

    def getTemplate(self):
        return self._template


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

    def addLayout(self, name):
        layout = self._project.getLayout(name)
        if layout not in self._layouts:
            self._layouts.append(layout)

    def getSiteTitle(self):
        tmp = self.getConfig(["title"], False)
        if tmp:
            return tmp

        return self._name

    def getSiteSubtitle(self):
        tmp = self.getConfig(["subtitle"], False)
        if tmp:
            return tmp

        return ""

    def read(self):
        self._readConfig()
        self._createFileIndex()
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
        self._cleanupOutput()

    def _readConfig(self):
        filename = os.path.join(self.getConfig(["dirs", "sites"]), self._name + ".json")

        if not os.path.isfile(filename):
            fail("Can't find config file: " + filename)

        config_struct = {"dirs": (None, None, None),
                "markup": (None, None, None),
                "title": (str, None, True),
                "subtitle": (str, None, True),
                "layout": (str, None, True),
                "files": (dict, {"index": (list, str, True),
                    "content": (list, str, True),
                    "hidden": (list, str, True),
                    "exclude": (list, str, True)}, True)}
        site_config = Config(filename, config_struct)
        self._config = Config.merge(self._config, site_config, True)

    def _readHelper(self, dir_path, parent, dir_hidden=False, page_config=None):
        if page_config:
            page_config.delete(["files", "sort"], False)
            page_config.delete(["files", "rename"], False)
        else:
            page_config = self._config

        entries = sorted(os.listdir(dir_path))

        if "stawebg.json" in entries:
            config_struct = {"layout": (str, None, True),
                "files": (dict, {"sort": (list, str, True),
                    "exclude": (list, str, True),
                    "hidden": (list, str, True),
                    "rename": ("mapping", (str, str), True)}, True)}
            tmp_config = Config(os.path.join(dir_path, "stawebg.json"), config_struct)
            page_config = Config.merge(page_config, tmp_config, False)

        # Add layout to list -> copy later
        self.addLayout(page_config.get(["layout"], False))

        # First we have to find the index file in this directory…
        idx = None
        for f in entries:
            absf = os.path.join(dir_path, f)
            if isFile(absf) and isCont(absf, self) and isIndex(absf, self):
                idx = Page(os.path.split(dir_path)[1], absf,
                        self, parent, dir_hidden or isHidden(absf, self, page_config),
                        page_config)
                entries.remove(f)
                break
        # …or create an empty page as index
        if not idx:
            dirname = os.path.split(dir_path)[1]
            idx = Page(dirname, None, self, parent, dir_hidden or isHidden(dirname, self, page_config),
                    page_config)

        if parent:
            parent.appendPage(idx)
        else:
            self._root = idx

        # Sort entries as specified in configuration
        sorted_entries = page_config.get(["files","sort"], False, [])
        for s in reversed(sorted_entries):
            absf = os.path.join(dir_path, s)
            if not s in entries:
                print("\tFile not found (specified in sort): " + absf)
            else:
                entries.remove(s)
                entries.insert(0, s)

        # Make absolute paths and check if it's a page
        for f in entries:
            absf = os.path.join(dir_path, f)
            hidden = dir_hidden or isHidden(absf, self, page_config)

            # Content file -> Page
            if isFile(absf) and isCont(absf, self):
                print("\tFound page: " + absf)
                idx.appendPage(Page(os.path.splitext(f)[0], absf, self, idx,
                                hidden, page_config))
            # Directory -> Go inside
            elif os.path.isdir(absf):
                self._readHelper(absf, idx, hidden, page_config.copy())
            # Unknown object
            else:
                if not isExcluded(absf, self, page_config):
                    tmp = OtherFile(self.getAbsSrcPath(),
                                    os.path.relpath(
                                        absf, self.getAbsSrcPath()),
                                    self.getAbsDestPath())
                    self._other_files.append(tmp)
                    print("\tFound unkown object: " + absf)

    def createMenu(self, cur_page):
        return self._root.createMenu(cur_page)

    def _createFileIndex(self):
        path = self.getAbsDestPath()
        if os.path.isdir(path):
            self._file_index = findFiles(path)

    def delFromFileIndex(self, path):
        if path in self._file_index:
            self._file_index.remove(path)

    def _rmFileIndex(self):
        for f in self._file_index:
            print("\tRemove old file: " + f)
            try:
                os.remove(f)
            except OSError as e:
                print("\tError: " + str(e))

    def _cleanupOutput(self):
        self._rmFileIndex()

        # Delete empty directories
        for d in findDirs(self.getAbsDestPath()):
            if not os.listdir(d):
                print("\tRemove empty directory: " + d)
                try:
                    os.rmdir(d)
                except OSError as e:
                    print("\tError: " + str(e))


class Page:
    def __init__(self, name, absPath, site, parent, hidden, config):
        self._name = name
        self._absSrc = absPath
        self._site = site
        self._hidden = hidden
        self._parent = parent
        self._subpages = []
        self._config = config

        self._site.delFromFileIndex(self._getDestFile())

    def appendPage(self, p):
        self._subpages.append(p)

    def getPages(self):
        return self._subpages

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

    def copy(self):
        mkdir(os.path.dirname(self._getDestFile()))

        # Use 'codecs' package to support UTF-8?
        try:
            outf = open(self._getDestFile(), 'w')
            tplf = open(self.getLayout().getTemplate())
            outf.write(self._replaceKeywords(tplf.read()))
            tplf.close()
            outf.close()
        except IOError as e: #TODO: check exceptions
            fail("Error creating " + self._getDestFile() + ": " + str(e))

        # Copy subpages
        for p in self._subpages:
            p.copy()

    def _translateMarkup(self):
        text = ''

        if not self._absSrc:
            return text

        with open(self._absSrc, "rt") as src:
            text = src.read()

        config = self._site.getConfig(["markup"], False)
        if not config:
            return text
        tool = config.get(os.path.splitext(self._absSrc)[1])

        if tool:
            out, err = Popen(tool, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate(text.encode())
            if len(err):
                fail(' '.join(tool) + ": " + err.decode())
            return out.decode()
        return text

    def _replaceKeywords(self, text):
        reps = {"%ROOT%": self.getRootLink(),
                "%CUR%": self.getCurrentLink(),
                "%LAYOUT%": self.getLayoutDir(),
                "%TITLE%": self.getTitle(),
                "%SITETITLE%": self._site.getSiteTitle(),
                "%SITESUBTITLE%": self._site.getSiteSubtitle(),
                "%MENU%": self._site.createMenu(self)}
        trans = lambda m: reps[m.group(0)]
        rc = re.compile('|'.join(map(re.escape, reps)))
        return rc.sub(trans, text.replace("%CONTENT%", self._translateMarkup()))

    def _getDestFile(self):
        tmp_path = ""

        parent = self.getParent()
        while parent and not parent.isRoot():
            tmp_path = os.path.join(parent.getName(), tmp_path)
            parent = parent.getParent()

        if not self.isRoot():
            tmp_path = os.path.join(tmp_path, self.getName())

        return os.path.join(self._site.getAbsDestPath(), tmp_path,
                            "index.html")

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
        tmp = self.getRootLink()
        if len(tmp):
            tmp += "/"
        tmp += self.getLayout().getSubdir() + "/"
        return tmp

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
            tmp = "."

        return tmp

    def getShortTitle(self):
        if self._absSrc:
            rename = self._config.get(["files", "rename", os.path.basename(self._absSrc)], False)
        else:
            rename = None

        if not self.getParent():
            return "Home"
        elif rename:
            return rename
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
        tmp = "<ul>\n"
        for p in items:
            if p == cur_page:
                found = True

            if p.isHidden():
                continue

            active = ""
            if p.pageIsInPathTo(cur_page) and (not p.isRoot() or p == cur_page):
                active = " class=\"active\""

            tmp = ''.join([tmp, "<li><a href=\"", p.getLink(cur_page), "\"",
                          active, ">", p.getShortTitle(), "</a></li>\n"])

            # Create submenu
            if not p.isRoot() and p.pageIsInPathTo(cur_page) and not last:
                tmp += p.createMenu(cur_page, found)

        return tmp + "</ul>\n"

    def pageIsInPathTo(self, dest):
        parent = dest
        while parent:
            if parent == self:
                return True
            parent = parent.getParent()

        return False


class OtherFile:
    """ Copy other file """
    def __init__(self, src_path_root, src_path_rel, dest_dir=None):
        """ src_path_root / src_path_rel ==> dest_dir / src_path_rel """
        self._src_path_root = src_path_root
        self._src_path_rel = src_path_rel
        self._dest_dir = dest_dir

    def copy(self, site, to=None):
        if not to:
            to = self._dest_dir

        # Create directory
        out_file = os.path.join(to, self._src_path_rel)
        out_dir = os.path.dirname(out_file)
        mkdir(out_dir)

        site.delFromFileIndex(out_file)

        copyFile(os.path.join(self._src_path_root, self._src_path_rel), out_dir)
