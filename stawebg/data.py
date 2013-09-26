#!/usr/bin/python3

import cgi
import errno
import locale
import math
import os
import re
import shutil
from datetime import datetime
from subprocess import Popen, PIPE
from stawebg.config import Config
from stawebg.helper import (listFolders, findFiles, findDirs, fail, matchList,
                            cleverCapitalize, cutStr, mkdir)

version = "0.1-dev"

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

        self._config = Config(os.path.join(self._root_dir, "stawebg.json"),
                              Config.global_struct)

        # Make directories absolute
        dirs = self._config.get(["dirs"])
        for k in dirs:
            dirs[k] = os.path.join(self._root_dir, dirs[k])

        # Set locale
        try:
            locale.setlocale(locale.LC_ALL, self.getConfig(["locale"], False, ""))
        except locale.Error as e:
            fail("Failed to set the locale \"" + self.getConfig(["locale"], False, "") + "\": " + str(e))

        # Add all layouts to list
        for name in listFolders(self.getConfig(['dirs', 'layouts'])):
            self._layouts[name] = Layout(self, name)
            self._layouts[name].read()

        # Add all site directories to list
        for s in listFolders(self.getConfig(['dirs', 'sites'])):
            site = Site(s, self)
            self._sites.append(site)
            site.read()

        # copy files to out dir
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


class Layout:
    def __init__(self, project, name):
        self._project = project
        self._name = name
        self._dir = os.path.join(self._project.getConfig(['dirs', 'layouts']),
                                 name)
        self._other_files = []

        self._files = {}
        self._files["template"] = os.path.join(self._dir, 'template.html')
        self._files["entry"] = os.path.join(self._dir, 'blog', 'entry.html')
        self._files["separator"] = os.path.join(self._dir, 'blog', 'separator.html')
        self._files["begin"] = os.path.join(self._dir, 'blog', 'begin.html')
        self._files["end"] = os.path.join(self._dir, 'blog', 'end.html')
        self._files["singleentry"] = os.path.join(self._dir, 'blog', 'singleentry.html')

        self._templates = {}

        print("Found layout: " + self._name)

    def read(self):
        # Check if template files exist and read them
        for i in self._files:
            if not isFile(self._files[i]):
                fail("Error in template \"" + self._name + "\":" + self._files[i] + " does not exist")
            self._templates[i] = self._readFile(self._files[i])

        # Search other files (CSS, images, ...)
        for f in findFiles(self._dir, [".html"]):
            print("\tFound file: " + f)
            self._other_files.append(OtherFile(self._dir,
                                               os.path.relpath(f, self._dir)))

    def copy(self, dest, site):
        for f in self._other_files:
            f.copy(site, os.path.join(dest, self.getSubdir()))

    def getSubdir(self):
        return os.path.join("style", self._name)

    def useTemplate(self, src, reps, user_reps, ext=None):
        content = self._translateMarkup(src, ext)
        text = self._prepareTemplate("template", user_reps, reps, content)
        return (text, content)

    def useBlogEntry(self, src, reps, user_reps):
        return self._prepareTemplate("entry", user_reps, reps, self._translateMarkup(src))

    def useBlogSeparator(self, user_reps):
        return self._prepareTemplate("separator", user_reps, [], "")

    def useBlogSingleEntry(self, src, reps, user_reps):
        return self._prepareTemplate("singleentry", user_reps, reps, self._translateMarkup(src))

    def useBlogBegin(self, reps, user_reps):
        return self._prepareTemplate("begin", user_reps, reps, "")

    def useBlogEnd(self, reps, user_reps):
        return self._prepareTemplate("end", user_reps, reps, "")

    def useBlogRSSEntry(self, src, reps, user_reps):
        text = self._removeHTML(self._translateMarkup(src))
        text = self.replaceKeywords(text, self._transformUserReps(user_reps))
        return self.replaceKeywords(text, reps)

    def _readFile(self, src):
        try:
            return open(src).read()
        except IOError as e:
            fail("Error reading \"" + src + "\": " + str(e))

    def createOutput(self, dest, text):  # TODO: move to helper.py?, use for other files too?
        mkdir(os.path.dirname(dest))

        try:
            outf = open(dest, 'w')
            outf.write(text)
            outf.close()
        except IOError as e: #TODO: check exceptions
            fail("Error creating " + dest + ": " + str(e))

    def _translateMarkup(self, src, ext=None):
        text = ''

        # src is string -> file extension given
        if ext:
            text = src
        # src if filename
        else:
            if not src:
                return text

            with open(src, "rt") as f:
                text = f.read()

            ext = os.path.splitext(src)[1]

        config = self._project.getConfig(["markup"], False)
        if not config:
            return text

        tool = config.get(ext)

        if tool:
            out, err = Popen(tool, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate(text.encode())
            if len(err):
                fail(' '.join(tool) + ": " + err.decode())
            return out.decode()
        return text

    def replaceKeywords(self, text, reps):
        if not reps:
            return text

        trans = lambda m: reps[m.group(0)]
        rc = re.compile('|'.join(map(re.escape, reps)))
        return rc.sub(trans, text)

    def _prepareTemplate(self, name, user_reps, reps, content):
        # User reps -> content -> user reps -> reps
        text = self._templates[name][:]
        text = self.replaceKeywords(text, self._transformUserReps(user_reps))
        text = text.replace("%CONTENT%", content)
        text = self.replaceKeywords(text, self._transformUserReps(user_reps))
        return self.replaceKeywords(text, reps)

    def _removeHTML(self, text):
        return re.sub('<.*?>', '', text)

    def _transformUserReps(self, reps):
        result = {}
        for i in reps:
            result["%_" + i + "%"] = reps[i]
        return result


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
            for d in findDirs(self.getAbsDestPath()):
                if not os.listdir(d):
                    print("\tRemove empty directory: " + d)
                    try:
                        os.rmdir(d)
                    except OSError as e:
                        print("\tError: " + str(e))
        elif len(self._file_index) != 0:
            # Print old files
            print("This are old files:")
            for f in self._file_index:
                print("\t" + f)

    def _readHelper(self, dir_path, parent, dir_hidden=False, blog_data_dir=False, page_config=None):
        index_rename = None
        if page_config:
            index_rename = page_config.get(["files", "rename",
                                            os.path.basename(dir_path)], False)
            page_config.delete(["files", "sort"], False)
            page_config.delete(["files", "rename"], False)
            page_config.delete(["blog"], False)
        else:
            page_config = self._config

        entries = sorted(os.listdir(dir_path))
        blog = None

        idx = None
        if not blog_data_dir:
            if "stawebg.json" in entries:
                tmp_config = Config(os.path.join(dir_path, "stawebg.json"),
                                    Config.directory_struct)
                page_config = Config.merge(page_config, tmp_config, False)

            # Add layout to list -> copy later
            layout = self._project.getLayout(page_config.get(["layout"], False))
            if layout not in self._layouts:
                self._layouts.append(layout)

            # Create blog, if there is config for it
            if page_config.get(["blog"], False):
                blog = Blog(dir_path, page_config, self)

            # First we have to find the index file in this directory…
            idx = None
            for f in entries:
                absf = os.path.join(dir_path, f)
                if isFile(absf) and isCont(absf, self) and isIndex(absf, self):
                    if index_rename:
                        page_config.add(["files", "rename", f], index_rename)
                    idx = Page(os.path.split(dir_path)[1], absf, self, parent,
                               dir_hidden or isHidden(absf, self, page_config),
                               blog, page_config)
                    entries.remove(f)
                    break
            # …or create an empty page as index
            if not idx:
                dirname = os.path.split(dir_path)[1]
                if index_rename:
                    page_config.add(["files", "rename", None], index_rename)
                idx = Page(dirname, None, self, parent, dir_hidden or
                           isHidden(dirname, self, page_config), blog, page_config)

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

        # Make absolute paths and check if it's a page
        for f in entries:
            absf = os.path.join(dir_path, f)
            if isExcluded(absf, self, page_config):
                continue
            hidden = dir_hidden or isHidden(absf, self, page_config)
            new_blog_data_dir = blog_data_dir or (blog and os.path.samefile(absf, blog.getAbsDir()))

            # Content file -> Page
            if isFile(absf) and isCont(absf, self):
                if new_blog_data_dir:
                    continue
                print("\tFound page: " + absf)
                idx.appendPage(Page(os.path.splitext(f)[0], absf, self, idx,
                                    hidden, blog, page_config))
            # Directory -> Go inside
            elif os.path.isdir(absf):
                print("\tFound dir:  " + absf)
                self._readHelper(absf, idx, hidden, new_blog_data_dir, page_config.copy())
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
    def __init__(self, name, absPath, site, parent, hidden, blog, config):
        self._name = name
        self._absSrc = absPath
        self._site = site
        self._hidden = hidden
        self._parent = parent
        self._subpages = []
        self._blog = blog
        self._config = config
        self._content = None

        self._site.delFromFileIndex(self._getDestFile())

        if self._blog and isIndex(self._absSrc, self._site):
            self._blog.setIndexPage(self)

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

        if self._blog:
            output = self._blog.getPageOne(self, output)
            self._blog.createPages(self, content)

        self.getLayout().createOutput(self._getDestFile(), output)

        # Copy subpages
        for p in self._subpages:
            p.copy()

        # Copy blog
        if self._blog and isIndex(self._absSrc, self._site):
            self._blog.copy()

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
        tmp = "<ul>\n"
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

        return tmp + "</ul>\n"

    def _pageIsInPathTo(self, dest):
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

        out_file = os.path.join(to, self._src_path_rel)
        out_dir = os.path.dirname(out_file)
        mkdir(out_dir)

        site.delFromFileIndex(out_file)
        shutil.copy(os.path.join(self._src_path_root, self._src_path_rel),
                    os.path.join(out_dir, os.path.basename(self._src_path_rel)))

class Blog:
    def __init__(self, dir, config, site):
        self._dir = dir
        self._config = config
        self._site = site
        self._index_page = None

        # Key: datetime object
        # Value: (title, filename)
        self._entries = {}

        self._read()

    def setIndexPage(self, index):
        self._index_page = index

    def getDir(self):
        return self._config.get(["blog", "dir"])

    def getAbsDir(self):
        return os.path.join(self._dir, self.getDir())

    def getLayout(self): #NOTE: Copy from Page…
        layout = self._config.get(["layout"], False)
        return self._site.getProject().getLayout(layout)

    def getPageOne(self, page_obj, template):
        tmp = self._getHTML(page_obj, 1, True)
        if not tmp:
            tmp = ""
        return template.replace("%BLOG%", tmp)

    def createPages(self, parent_page, template):
        if self._config.get(["blog", "per-page"], False, 0) == 0:
            return

        page_number = 1
        while True:
            page = Page(str(page_number), None, self._site, parent_page, True, None, self._config)
            tmp = self._getHTML(page, page_number, False)
            if not tmp:
                return
            content = template.replace("%BLOG%", tmp)
            page.setContent(content, "html")
            page.copy()
            page_number += 1

    def copy(self):
        user_reps = self._config.get(["variables"], False, [])
        for i in sorted(self._entries, reverse=True):
            page = Page(self._getTitle(i), None, self._site, self._index_page, True, None, self._config)
            content = self.getLayout().useBlogSingleEntry(self._entries[i][1], self._getEntryReps(i, page), user_reps)
            page.setContent(content, "md")
            page.copy()

        self._createRSS()

    def _getLinks(self, page, root=False):
        per_page = self._config.get(["blog", "per-page"], False, 0)
        if per_page == 0:
            return ""

        link = ""
        if not root:
            link = "../"

        tmp = "<ul>\n"
        number_of_pages = math.ceil(len(self._entries) / per_page)
        for i in range(number_of_pages):
            if i+1 == page:
                tmp += "<li>" + str(i+1) + "</li>\n"
            else:
                tmp += "<li><a href=\"" + link + str(i+1) + "\">" + str(i+1) + "</a></li>\n"
        tmp += "</ul>"

        return tmp

    def _getDirectLink(self, page, root, configname, default, relative=0, first=False, last=False):
        per_page = self._config.get(["blog", "per-page"], False, 0)
        if per_page == 0:
            return ""
        number_of_pages = math.ceil(len(self._entries) / per_page)

        to_page = 1   # to first page
        if relative:  # relative to current page
            to_page = page + relative
        elif last:    # to last page
            to_page = number_of_pages

        link = ""
        if not root:
            link = "../"

        if per_page == 0 or to_page < 1 or to_page > number_of_pages or page == to_page:
            return self._config.get(["blog", configname], False, default)
        else:
            return "<a href=\"" + link + str(to_page) + "\">" + self._config.get(["blog", configname], False, default) + "</a>"

    def _getHTML(self, page_obj, page, root):
        user_reps = self._config.get(["variables"], False, [])
        per_page = self._config.get(["blog", "per-page"], False, 0)

        start = (page-1)*per_page
        end = page*per_page-1

        if start >= len(self._entries) or (per_page == 0 and page != 1):  # No entries for this page
            return None

        tmp = self.getLayout().useBlogBegin(self._getCommonReps(page, root), user_reps)
        for n, i in enumerate(sorted(self._entries, reverse=True)):
            if (n < start or n > end) and per_page != 0:
                continue

            tmp += self.getLayout().useBlogEntry(self._entries[i][1], self._getEntryReps(i, page_obj), user_reps)
            if n != end and n != len(self._entries)-1:  # Last element on page or last element of all entries
                tmp += self.getLayout().useBlogSeparator(user_reps)
        tmp += self.getLayout().useBlogEnd(self._getCommonReps(page, root), user_reps)

        return tmp

    def _read(self):
        for f in findFiles(self.getAbsDir()):
            if isCont(f, self._site):
                # meta = (time, title)
                meta = self._getMeta(f)
                if meta:
                    print("\tFound blog entry: " + f)
                    self._entries[meta[0]] = (meta[1], f)
                else:
                    print("\tWarning: content file with invalid filename for blog: " + f)
            else:
                pass # FIXME: OtherFile

    def _getMeta(self, path):
        filename = os.path.basename(os.path.splitext(path)[0])
        data = re.match(r"([0-9]{4})-([0-9]{2})-([0-9]{2})-([0-9]{2})-([0-9]{2})-(.+)", filename)

        if not data:
            return None

        # FIXME: check range of values
        time = datetime(int(data.group(1)), int(data.group(2)), int(data.group(3)), int(data.group(4)), int(data.group(5)))
        title = data.group(6)
        return (time, title)

    def _getTitle(self, key):
        return os.path.splitext(os.path.basename(self._entries[key][1]))[0]

    def _getCommonReps(self, page, root):
        return {"%PAGELIST%": self._getLinks(page, root),
                "%PAGEPREV%": self._getDirectLink(page, root, "previous", "<", relative=-1),
                "%PAGENEXT%": self._getDirectLink(page, root, "next", ">", relative=+1),
                "%PAGEFIRST%": self._getDirectLink(page, root, "first", "<<", first=True),
                "%PAGELAST%": self._getDirectLink(page, root, "last", ">>", last=True)}

    def _getEntryReps(self, key, page_obj, full_link=False):
        reps = {"%DATE%": key.strftime(self._config.get(["timeformat"])),
                "%LINK%": self._getLinkTo(key, page_obj, full_link)}
        reps.update(page_obj.getReps())
        reps["%CUR%"] = self._index_page.getLink(page_obj) + "/" + self.getDir() + "/" + os.path.relpath(os.path.dirname(self._entries[key][1]), self.getAbsDir()) + "/"
        return reps

    def _getLinkTo(self, key, page_obj, full=False):
        tmp = ""
        if full:
            tmp = self._config.get(["url"], False, "") + "/"
        return tmp + self._index_page.getLink(page_obj) + self._getTitle(key)

    def _createRSS(self):
        if not self._config.get(["blog", "rss"], False):
            return

        user_reps = self._config.get(["variables"], False, [])
        dest = os.path.join(self._site.getAbsDestPath(), self._config.get(["blog", "rss", "file"]))
        with open(dest, "wt") as f:
            locale_backup = locale.getlocale(locale.LC_ALL)
            locale.setlocale(locale.LC_ALL, "en_GB")

            url = self._config.get(["url"], False)
            if not url:
                print("\tWarning: No URL given in configuration. Generating invalid RSS feed.")
                url=""

            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f.write('<rss version="2.0">\n')
            f.write('<channel>\n')
            f.write('<title>' + self._RSSencode(self._config.get(["blog", "rss", "title"])) + '</title>\n')
            f.write('<link>' + self._RSSencode(url) + '</link>\n')
            f.write('<description>' + self._RSSencode(self._config.get(["blog", "rss", "description"])) + '</description>\n')
            copyright = self._config.get(["blog", "rss", "copyright"], False)
            if copyright:
                f.write('<copyright>' + self._RSSencode(copyright) + '</copyright>\n')
            if self._config.get(["blog", "rss", "show_generator"], False, True):
                f.write('<generator>stawebg ' + self._RSSencode(version) + '</generator>\n')

            f.write('<pubDate>' + self._getRSSDate(datetime.now()) + '</pubDate>\n')

            for i in sorted(self._entries, reverse=True):
                html=self.getLayout().useBlogRSSEntry(self._entries[i][1], self._getEntryReps(i, self._site.getRoot(), True), user_reps)
                # FIXME: remove HTML
                f.write('<item>\n')
                f.write('<title>' + self._RSSencode(self._getRSSTitle(html)) + '</title>\n')
                f.write('<description>' + self._RSSencode(self._getRSSContent(html)) + '</description>\n')
                f.write('<link>' + self._RSSencode(url + '/' + self._getLinkTo(i, self._site.getRoot())) + '</link>\n')
                f.write('<guid>' + self._RSSencode(self._getTitle(i)) + '</guid>\n')
                f.write('<pubDate>' + self._RSSencode(self._getRSSDate(i)) + '</pubDate>\n')
                f.write('</item>\n')

            f.write('</channel>\n')
            f.write('</rss>\n')

            locale.setlocale(locale.LC_ALL, locale_backup)

        self._site.delFromFileIndex(dest)

    def _RSSencode(self, text):
        return cgi.escape(text).encode('ascii', 'xmlcharrefreplace').decode('utf-8')

    def _getRSSDate(self, data):
        return data.strftime('%d %b %Y %H:%M') + " " + self._config.get(["timezone"],False, '+0000')

    def _getRSSGroups(self, text, group):
        #FIXME: ignore empty lines at begin (and at the end)
        match = re.match(r'(.*?)$[\n\r\t ]*(.*)', text, re.MULTILINE | re.DOTALL)
        if match:
            return match.group(group)
        return ""

    def _getRSSTitle(self, text):
        return cutStr(self._getRSSGroups(text, 1), self._config.get(["blog", "rss", "title_length"], False, 0))

    def _getRSSContent(self, text):
        return cutStr(self._getRSSGroups(text, 2), self._config.get(["blog", "rss", "content_length"], False, 0))
