#!/usr/bin/python3

from stawebg.helper import *
import json
import subprocess

config = {}


class Project:
    def __init__(self):
        global config
        self._sites = []
        self._layouts = {}

        if not os.path.isfile("config.json"):
            fail("Can't find config.json")

        with open('config.json', 'r') as conff:
            try:
                config = json.load(conff)
            except Exception as e:
                fail("Error parsing JSON file: " + str(e))

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
        self._head = os.path.join(self._dir, config['layout']["head"])
        self._bottom = os.path.join(self._dir, config['layout']["bottom"])
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

    def getHead(self):
        return self._head

    def getBottom(self):
        return self._bottom


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
        filename = os.path.join(self.getAbsSrcPath(), config['config']["site"])

        if not os.path.isfile(filename):
            fail("Can't find config file: " + filename)

        j = {}
        with open(filename, 'r') as f:
            try:
                j = json.load(f)
            except Exception as e:
                fail("Error parsing JSON file: " + str(e))

            self._sitetitle = j.get("title")
            self._sitesubtitle = j.get("subtitle")
            self._layout_name = j.get("layout")

    def _readHelper(self, dir_path, parent):
        files = os.listdir(dir_path)

        if not parent:
            parent = self._root

        # Make absolute pathes and check if it's a page
        for f in files:
            absf = os.path.join(dir_path, f)
            name = os.path.basename(absf)
            ext = os.path.splitext(absf)[1]

            # HTML or Markdown File -> Page
            if os.path.isfile(absf) and ext in config["files"]["content"]:
                # Hidden files begin with _ # LOOK: hidden
                hidden = False
                if name.startswith("_") and len(name) > 1:
                    hidden = True
                    name = name[1:]

                # Is index file
                is_index = name in config['files']["index"]

                # Delete file extension
                name = os.path.splitext(name)[0]

                print("\tFound page: " + absf)

                newpage = Page(name, absf, self, parent, hidden, is_index)
                if parent:
                    parent.appendPage(newpage)
                else:
                    self._root = newpage
            # Directory -> Go inside
            elif os.path.isdir(absf):
                self._readHelper(absf, parent)
            # Unknown object
            else:
                if not (name.startswith("_") or
                        stringEndsWith(absf, config["files"]["exclude"])):
                    tmp = OtherFile(self.getAbsSrcPath(),
                                    os.path.relpath(absf, self.getAbsSrcPath()),
                                    self.getAbsDestPath())
                    self._other_files.append(tmp)

                    print("\tFound unkown object: " + absf)

#    def createMenu(self, cur_page):
#        return self._createMenuHelper(1, cur_page, False)
#
#    def _createMenuHelper(self, level, cur_page, last):
#        items = []
#        home = None  # Add home later to begin of list of items
#
#        # Collect items
#        for p in self._pages:
#            if level == 1 and len(p.getPath()) <= 1:
#                # Home / in list -> don't add now
#                # add it later to the begin of the sorted list of items
#                if len(p.getPath()) == 0:
#                    home = p
#                    continue
#                items.append(p)
#            # Until cur_page
#            elif (listBeginsWith(cur_page.getPath(), p.getPath()[:-1]) and
#                  len(p.getPath()) == level):
#                items.append(p)
#            # After cur_page
#            elif (listBeginsWith(p.getPath(), cur_page.getPath()) and
#                  len(p.getPath()) == level):
#                items.append(p)
#
#        # Sort items
#        items = sorted(set(items), key=lambda i: i.getShortTitle())
#        if home:
#            items.insert(0, home)
#
#        # Create HTML Code
#        found = False
#        tmp = "<ul>\n"
#        for p in items:
#            if p == cur_page:
#                found = True
#
#            if p.isHidden():
#                continue
#
#            active = ""
#            if p == cur_page or listBeginsWith(cur_page.getPath(), p.getPath()):
#                active = "class=\"active\""
#
#            tmp = ''.join([tmp, "<li><a href=\" ", p.getLink(cur_page), "\" ",
#                          active, ">", p.getShortTitle(), "</a></li>\n"])
#
#            # Create submenu
#            if listBeginsWith(cur_page.getPath(), p.getPath()) and not last:
#                tmp += self._createMenuHelper(level+1, cur_page, found)
#
#        tmp += "</ul>\n"
#
#        return tmp


class Page:
    def __init__(self, name, absPath, site, parent, hidden, is_index):
        self._name = name # None -> root
        self._absSrc = absPath
        self._site = site
        self._hidden = hidden
        self._parent = parent
        self._subpages = []

        # was index.html in original file structure (important for %CUR%)
        self._is_index = is_index

    def appendPage(self, p):
        self._subpages.append(p)

    def getPages(self):
        return self._subpages

    def getParent(self):
        return self._parent

    def getName(self):
        return self._name

    def isHidden(self):
        return self._hidden

    def copy(self):
        # Create directory
        mkdir(os.path.dirname(self._getDestFile()))

        print(self._absSrc + " -> " + self._getDestFile());

        # Write to file
        outf = open(self._getDestFile(), 'w')

        self._appendAndReplaceFile(outf, self._site.getLayoutHead())
        self._appendAndReplaceFile(outf, self._absSrc, True)
        self._appendAndReplaceFile(outf, self._site.getLayoutBottom())

        outf.close()

        # Copy subpages
        for p in self._subpages:
            p.copy()

    def _appendAndReplaceFile(self, to, src, translate=False):
        with open(src, 'r') as f:
            content = "".join(f.readlines())

            # Markdown
            if translate:
                content = self._translateMarkup(self._absSrc, content)

            new = self._replaceKeywords(content)
            to.write(new)

    def _translateMarkup(self, filename, text):
        extension = os.path.splitext(filename)[1]

        if extension in config["files"]["markup"]:
            p = subprocess.Popen(config["files"]["markup"][extension],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True)
            out, err = p.communicate(text.encode())

            if err != "":
                fail(config["files"]["markup"][extension] + ": " + err)

            return out

        return text

    def _replaceKeywords(self, text):
        new = text

        # %ROOT%
        new = new.replace("%ROOT%", self.getRootLink())

        # %CUR%
        new = new.replace("%CUR%", self.getCurrentLink())

        # %TITLE%
        new = new.replace("%TITLE%", self.getTitle())

        # %SITETITLE%
        new = new.replace("%SITETITLE%", self._site.getSiteTitle())

        # %SITESUBTITLE%
        new = new.replace("%SITESUBTITLE%", self._site.getSiteSubtitle())

        # %MENU%
        #new = new.replace("%MENU%", self._site.createMenu(self))

        return new

    def _getDestFile(self):
        tmp_path = ""
        parent = self.getParent()

        if parent:
            tmp_path = os.path.join(parent.getName(), tmp_path);
            parent = parent.getParent()

        return os.path.join(self._site.getAbsDestPath(), tmp_path, "index.html")

    def getRootLink(self):
        tmp = ""

        parent = self.getParent()

        if parent:
            tmp = tmp + "../"
            parent = parent.getParent()

        return tmp

    def getCurrentLink(self):
        if self._is_index:
            return ""
        else:
            return "../"

    def getLink(self, origin=None):
        if not origin:
            origin = self

        tmp = origin.getRootLink()

        parent = self.getParent()
        if parent:
            tmp = t + "/" + tmp
            parent = parent.getParent()

        if tmp == "":
            tmp = "."

        return tmp

    def getShortTitle(self):
        if not self.getParent():
            return "Home"
        else:
            return cleverCapitalize(self.getName())

    def getTitle(self):
        result = ""
        if not self.getParent():
            return self._site.getSiteTitle() + " > " + self.getShortTitle()
        else:
            return self.getParent().getTitle() + " > " + self.getShortTitle()


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
