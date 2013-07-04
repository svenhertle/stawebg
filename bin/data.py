#!/usr/bin/python3

from helper import *
import json

config = {}

class Project:
    def __init__(self):
        global config
        self._sites = []
        self._layouts = {}
        with open('config.json', 'r') as conff:
            config = json.load(conff)

    def read(self):
        self._readLayouts()
        self._readSites()

    def copy(self):
        for s in self._sites:
            s.copy()

    def getLayoutByName(self, name = 'default'):
        return self._layouts.get(name)

    # Add all layouts to list
    def _readLayouts(self):
        for name in listFolders(config['dirs']['layouts']):
            layout = Layout(name)
            self._layouts[name] = layout
            layout.read()

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

        self._head = os.path.join(self._dir, config['layout']["head"])
        self._bottom = os.path.join(self._dir, config['layout']["bottom"])

        self._other_files = []

        debug("Found layout: " + self._name)

    def read(self):
        for f in findFiles(self._dir, [".html"]):
            debug("\tFound file: " + f)
            self._other_files.append(OtherFile(self._dir, os.path.relpath(f, self._dir), None))

    def copy(self, dest):
        for f in self._other_files:
            f.copy(dest)

    def getHead(self):
        return self._head

    def getBottom(self):
        return self._bottom

class Site:
    def __init__(self, name, project):
        self._project = project

        self._name = name

        self._pages = []

        self._other_files = []

        self._layout_name = None

        self._sitetitle = None
        self._sitesubtitle = None

        debug("Found site: " + self._name)

    def getAbsSrcPath(self):
        return os.path.join(config['dirs']["sites"], self._name)

    def getAbsDestPath(self):
        return os.path.join(config['dirs']["out"], self._name)

    def getLayout(self):
        return self._project.getLayoutByName(self._layout_name)

    def getLayoutHead(self):
        return self.getLayout().getHead()

    def getLayoutBottom(self):
        return self.getLayout().getBottom()

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
        self._readHelper(self.getAbsSrcPath(), [])

    def copy(self):
        # Check if layout exists
        if not self.getLayout():
            fail("Can't find layout: " + self._layout_name + "\nAbort.")

        # Pages
        for p in self._pages:
            p.copy()

        # Layout
        self.getLayout().copy(self.getAbsDestPath())

        # Other files
        for f in self._other_files:
            f.copy()

    def _readConfig(self):
        filename = os.path.join(self.getAbsSrcPath(), config['config']["site"])
        if os.path.isfile(filename):
            json = jsonFromFile(filename)

            if json:
                if "title" in json:
                    self._sitetitle = json["title"]
                if "subtitle" in json:
                    self._sitesubtitle = json["subtitle"]
                if "layout" in json:
                    self._layout_name = json["layout"]

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
                if not name in config['files']["index"]:
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
                if not stringEndsWith(absf, config['files']["exclude"]):
                    tmp = OtherFile(self.getAbsSrcPath(), os.path.relpath(absf, self.getAbsSrcPath()), self.getAbsDestPath())
                    self._other_files.append(tmp)

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
        mkdir(os.path.dirname(self._getDestFile()))

        # Write to file
        outf = open(self._getDestFile(), 'w')

        self._appendAndReplaceFile(outf, self._site.getLayoutHead())
        self._appendAndReplaceFile(outf, self._absSrc)
        self._appendAndReplaceFile(outf, self._site.getLayoutBottom())

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

        # %SITETITLE%
        new = new.replace("%SITETITLE%", self._site.getSiteTitle())

        # %SITESUBTITLE%
        new = new.replace("%SITESUBTITLE%", self._site.getSiteSubtitle())

        # %MENU%
        new = new.replace("%MENU%", self._site.createMenu(self))

        return new

    def _getDestFile(self):
        result = self._site.getAbsDestPath()

        for p in self._path:
            result = os.path.join(result, p)

        return os.path.join(result, "index.html") #TODO: -> config?

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
            return "Home" # TODO: use page title?
        else:
            last = len(self._path) - 1
            return cleverCapitalize(self._path[last])

    def _getTitle(self):
        if len(self._path) == 0:
            return "Home" # TODO: use page title?
        else:
            result = ""
            for t in self._path:
                if len(result) == 0:
                    result = cleverCapitalize(t)
                else:
                    result += " > " + cleverCapitalize(t)

        return result

class OtherFile:
    """ Copy other file """
    def __init__(self, src_path_root, src_path_rel, dest_dir):
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
