#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
from datetime import datetime
from stawebg.helper import (isIndex, createFile)
from stawebg.version import version


class Page:
    """ This class represents one page of a site """
    def __init__(self, name, absSrc, site, parent, hidden, config):
        """ Initialize variables and delete output file from index.

        :param name: Name of the page.
        :type name: str

        :param absSrc: Absolute path of source file.
        :type absSrc: str

        :param site: Corresponding site.
        :type site: :class:`stawebg.site.Site`

        :param parent: Parent page.
        :type parent: :class:`stawebg.page.Page`

        :param hidden: Is page hidden?
        :type hidden: bool

        :param config: Configuration for this page.
        :type config: `stawebg.config.Config`
        """
        self._name = name
        self._absSrc = absSrc
        self._site = site
        self._hidden = hidden
        self._parent = parent
        self._subpages = []
        self._config = config
        self._content = None

        self._site.delFromFileIndex(self._getDestFile())

    def appendPage(self, page):
        """ Add page as child.

        :param page: Page that should be added.
        :type page: :class:`stawebg.page.Page`
        """
        self._subpages.append(page)

    def getParent(self):
        """ Get parent of page.

        :rtype: :class:`stawebg.page.Page`
        """
        return self._parent

    def getName(self):
        """ Get name of page.

        :rtype: str
        """
        return self._name

    def isRoot(self):
        """ Check is this page is the root page.

        This means that the page has no parent.

        :rtype: bool
        """
        return self._parent is None

    def isHidden(self):
        """ Check if this page is hidden.

        :rtype: bool
        """
        return self._hidden

    def getLayout(self):
        """ Get layout of page.

        :rtype: :class:`stawebg.layout.Layout`
        """
        layout = self._config.get(["layout"], False)
        return self._site.getProject().getLayout(layout)

    def getReps(self):
        """ Get replacements for this page.

        This are the replacements done by stawebg (without CONTENT) and
        without the user replacements.

        :rtype: dict
        """
        timeformat = self._config.get(["timeformat"], False, "%c")
        return {"%ROOT%": self.getRootLink(),
                "%CUR%": self.getCurrentLink(),
                "%LAYOUT%": self.getLayoutDir(),
                "%TITLE%": self.getTitle(),
                "%SITETITLE%": self._site.getSiteTitle(),
                "%SITESUBTITLE%": self._site.getSiteSubtitle(),
                "%MENU%": self._site.createMenu(self),
                "%VERSION%": version,
                "%GENERATIONTIME%": datetime.now().strftime(timeformat),
                "%GENERATIONYEAR%": datetime.now().strftime("%Y"),
                "%URL%": self._config.get(["url"], False, "")}

    def copy(self):
        """ Copy this page."""
        user_reps = self._config.get(["variables"], False, [])

        # regular file
        output = ""
        content = ""
        if not self._content:
            output, content = self.getLayout().useTemplate(self._absSrc,
                                                           self.getReps(),
                                                           user_reps)
        else:
            output, content = self.getLayout().useTemplate(self._content[0],
                                                           self.getReps(),
                                                           user_reps,
                                                           self._content[1])

        createFile(self._getDestFile(), output)

        # Copy subpages
        for p in self._subpages:
            p.copy()

    def _getDestFile(self):
        """ Get destination file for output.

        :rtype: str
        """
        tmp_path = ""

        parent = self.getParent()
        while parent and not parent.isRoot():
            tmp_path = os.path.join(parent.getName(), tmp_path)
            parent = parent.getParent()

        if not self.isRoot():
            tmp_path = os.path.join(tmp_path, self.getName())

        return os.path.join(self._site.getAbsDestPath(), tmp_path,
                            "index.html")

    def getLayoutDir(self):
        """ Get directory of used layout for URLs

        :rtype: str
        """
        return self.getRootLink() + self.getLayout().getOutputDir() + "/"

    def getRootLink(self):
        """ Get relative link from page to root directory.

        :rtype: str
        """
        tmp = ""

        parent = self.getParent()
        while parent:
            tmp = tmp + "../"
            parent = parent.getParent()

        return tmp

    def getCurrentLink(self):
        """ Get link to files that were in the same input directory.

        This may be '' or '../'.

        :rtype: str
        """
        if self._absSrc and isIndex(self._absSrc, self._site):
            return ''
        else:
            return '../'

    def getLink(self, origin=None):
        """ Get link from origin page to this page.

        :param origin: Page where the link should be used.
        :type origin: :class:`stawebg.page.Page`

        :rtype: str
        """
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
        """ Get short title of this page.

        This title is used in the menu.

        :rtype: str
        """
        key = None
        if self._absSrc:
            key = os.path.basename(self._absSrc)

        rename = self._config.get(["files", "rename", key], False)

        if rename:
            return rename
        elif not self.getParent():
            return "Home"
        else:
            return self.getName().capitalize()

    def getTitle(self, no_home=False):
        """ Get complete title of this page.

        :param no_home: Do not include the root page ("Home") in the title.
        :type no_home: bool

        :rtype: str
        """
        if not self.getParent():
            if no_home:
                return self._site.getSiteTitle()
            else:
                return self._site.getSiteTitle() + " > " + self.getShortTitle()
        else:
            return self.getParent().getTitle(True) + " > " + \
                self.getShortTitle()

    def createMenu(self, active_page, last=False):
        """ Create menu (HTML output).

        :param active_page: Active page (for highlight).
        :type active_page: :class:`stawebg.page.Page`

        :param last: Do not go deeper in menu.
        :type last: bool

        :rtype: str
        """
        items = self._subpages[:]

        # Add root link
        if self.isRoot():
            items.insert(0, self)

        # Create HTML Code
        found = False
        tmp = ""
        for p in items:
            if p == active_page:
                found = True

            if p.isHidden():
                continue

            active = ""
            if p._pageIsInPathTo(active_page) and \
                    (not p.isRoot() or p == active_page):
                active = " class=\"active\""

            tmp = ''.join([tmp, "<li><a href=\"", p.getLink(active_page), "\"",
                          active, ">", p.getShortTitle(), "</a></li>\n"])

            # Create submenu
            if not p.isRoot() and p._pageIsInPathTo(active_page) and not last:
                tmp += p.createMenu(active_page, found)

        return "<ul>\n" + tmp + "</ul>\n" if tmp else ""

    def _pageIsInPathTo(self, other_page):
        """ Check if current page is in path from root to other page.

        :param other_page: Other page.
        :type other_page: :class:`stawbeg.page.Page`

        :rtype: bool
        """
        parent = other_page
        while parent:
            if parent == self:
                return True
            parent = parent.getParent()

        return False
