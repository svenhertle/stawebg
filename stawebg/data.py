#!/usr/bin/python3

import json
import os
import re
from subprocess import Popen, PIPE
from stawebg.helper import (listFolders, findFiles, copyFile, mkdir, fail,
                            cleverCapitalize)

config = {}

isFile = lambda f: os.path.isfile(f)
isIndex = lambda f: os.path.basename(f) in config['files']['index']
isCont = lambda f: os.path.splitext(f)[1] in config['files']['content']
isMarkup = lambda f: os.path.splitext(f)[1] in config['files']['markup']


class Project:
    def __init__(self, project_dir=""):
        global config
        self._sites = []
        self._layouts = {}
        self._root_dir = project_dir

        try:
            conff = open(os.path.join(self._root_dir, "config.json"), "r")
            config = json.load(conff)
        except Exception as e:
            fail("Error parsing configuration file: " + str(e))

        # Make directories absolute
        for k in config["dirs"]:
            config["dirs"][k] = os.path.join(self._root_dir, config["dirs"][k])

    def read(self):
        self._readLayouts()
        self._readSites()

    def copy(self):
        for s in self._sites:
            s.copy()

    def getLayoutByName(self, name=None):
        if not name:
            name = "default"

        return self._layouts.get(name)

    # Add all layouts to list
    def _readLayouts(self):
        for name in listFolders(config['dirs']['layouts']):
            self._layouts[name] = Layout(name)
            self._layouts[name].read()

    # Add all site directories to list
    def _readSites(self):
        for s in listFolders(config['dirs']['sites']):
            site = Site(s, self)
            self._sites.append(site)
            site.read()


class Layout:
    def __init__(self, name):
        self._name = name
        self._dir = os.path.join(config['dirs']['layouts'], name)
        self._template = os.path.join(self._dir, 'template.html')
        self._other_files = []

        print("Found layout: " + self._name)

    def read(self):
        for f in findFiles(self._dir, [".html"]):
            print("\tFound file: " + f)
            self._other_files.append(OtherFile(self._dir,
                                               os.path.relpath(f, self._dir)))

    def copy(self, dest):
        for f in self._other_files:
            f.copy(dest)

    def getTemplate(self):
        return self._template


class Site:
    def __init__(self, name, project):
        self._project = project
        self._name = name
        self._root = None
        self._other_files = []
        self._layout_name = None
        self._sitetitle = None
        self._sitesubtitle = None
        print("Found site: " + self._name)

    def getAbsSrcPath(self):
        return os.path.join(config['dirs']["sites"], self._name)

    def getAbsDestPath(self):
        return os.path.join(config['dirs']["out"], self._name)

    def getLayout(self):
        return self._project.getLayoutByName(self._layout_name)

    def getLayoutTemplate(self):
        return self.getLayout().getTemplate()

    def getSiteTitle(self):
        if self._sitetitle:
            return self._sitetitle

        return self._name

    def getSiteSubtitle(self):
        if self._sitesubtitle:
            return self._sitesubtitle

        return ""

    def read(self):
        self._readConfig()
        self._readHelper(self.getAbsSrcPath(), self._root)

    def copy(self):
        # Check if layout exists
        if not self.getLayout():
            fail("Can't find layout: " + self._layout_name + "\nAbort.")

        # Pages
        self._root.copy()

        # Layout
        self.getLayout().copy(self.getAbsDestPath())

        # Other files
        for f in self._other_files:
            f.copy()

    def _readConfig(self):
        filename = os.path.join(config["dirs"]["sites"], self._name + ".json")

        if not os.path.isfile(filename):
            fail("Can't find config file: " + filename)

        j = {}
        with open(filename) as f:
            try:
                j = json.load(f)
            except Exception as e:
                fail("Error parsing JSON file (" + filename + "): " + str(e))

            self._sitetitle = j.get("title")
            self._sitesubtitle = j.get("subtitle")
            self._layout_name = j.get("layout")

    def _readHelper(self, dir_path, parent):
        entries = sorted(os.listdir(dir_path))

        # First we have to find the index file in this directory…
        idx = None
        for f in entries:
            absf = os.path.join(dir_path, f)
            if isFile(absf) and isCont(absf) and isIndex(absf):
                idx = Page(os.path.split(dir_path)[1], absf,
                           self, parent, False)
                entries.remove(f)
                break
        # …or create an empty page as index
        if not idx:
                idx = Page(os.path.split(dir_path)[1], None,
                           self, parent, False)

        if parent:
            parent.appendPage(idx)
        else:
            self._root = idx

        # Sort entries as specified in configuration
        sorted_entries = []
        hidden_entries = []
        if "stawebg.json" in entries:
            absf = os.path.join(dir_path, "stawebg.json")

            j = {}
            with open(absf) as f:
                try:
                    j = json.load(f)
                except Exception as e:
                    fail("Error parsing JSON file (" + absf + "): " + str(e))

                sorted_entries = j.get("sort")
                hidden_entries = j.get("hidden")

        sorted_entries.reverse()
        for s in sorted_entries:
            absf = os.path.join(dir_path, s)

            if not s in entries:
                print("\tFile not found (specified in sort): " + absf)
            else:
                entries.remove(s)
                entries.insert(0, s)

        # Make absolute paths and check if it's a page
        for f in entries:
            absf = os.path.join(dir_path, f)

            # HTML or Markdown File -> Page
            if isFile(absf) and isCont(absf):
                print("\tFound page: " + absf)

                hidden = f in hidden_entries

                idx.appendPage(Page(os.path.splitext(f)[0], absf, self, idx,
                                hidden))
            # Directory -> Go inside
            elif os.path.isdir(absf):
                self._readHelper(absf, idx)
            # Unknown object
            else:
                if not absf.endswith(tuple(config["files"]["exclude"])):
                    tmp = OtherFile(self.getAbsSrcPath(),
                                    os.path.relpath(
                                        absf, self.getAbsSrcPath()),
                                    self.getAbsDestPath())
                    self._other_files.append(tmp)

                    print("\tFound unkown object: " + absf)

    def createMenu(self, cur_page):
        return self._root.createMenu(cur_page)


class Page:
    def __init__(self, name, absPath, site, parent, hidden):
        self._name = name
        self._absSrc = absPath
        self._site = site
        self._hidden = hidden
        self._parent = parent
        self._subpages = []

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

    def copy(self):
        mkdir(os.path.dirname(self._getDestFile()))

        # Use 'codecs' package to support UTF-8?
        try:
            outf = open(self._getDestFile(), 'w')
            tplf = open(self._site.getLayoutTemplate())
            outf.write(self._replaceKeywords(tplf.read()))
            tplf.close()
            outf.close()
        except Exception as e:
            fail("Error creating " + self._getDestFile() + ": " + str(e))

        # Copy subpages
        for p in self._subpages:
            p.copy()

    def _translateMarkup(self):
        text = ''

        if not self._absSrc:
            return text

        tool = config["files"]["markup"].get(os.path.splitext(self._absSrc)[1])

        with open(self._absSrc) as src:
            text = src.read()

        if tool:
            out, err = Popen(tool, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                             universal_newlines=True).communicate(text.encode())
            if err != '':
                fail(' '.join(tool) + ": " + err)
            return out
        return text

    def _replaceKeywords(self, text):
        reps = {"%ROOT%": self.getRootLink(),
                "%CUR%": self.getCurrentLink(),
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
            tmp_path = os.path.join(tmp_path, self._name)

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
        return '' if self._absSrc and isIndex(self._absSrc) else '../'

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
        if not self.getParent():
            return "Home"
        else:
            return cleverCapitalize(self.getName())

    def getTitle(self):
        if not self.getParent():
            return self._site.getSiteTitle() + " > " + self.getShortTitle()
        else:
            return self.getParent().getTitle() + " > " + self.getShortTitle()

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

    def copy(self, to=None):
        if not to:
            to = self._dest_dir

        # Create directory
        out_file = os.path.join(to, self._src_path_rel)
        out_dir = os.path.dirname(out_file)
        mkdir(out_dir)

        copyFile(os.path.join(self._src_path_root, self._src_path_rel), out_dir)
