#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
from stawebg.config import Config
from stawebg.helper import (findFiles, findDirs, fail, isIndex,
                            isHidden, isExcluded, isCont)
from stawebg.otherfile import OtherFile
from stawebg.page import Page


class Site:
    """ This class represents a site (pages and other files). """
    def __init__(self, name, project):
        """ Read site config and content.

        :param name: Name of site.
        :type name: str

        :param project: Corresponding project.
        :type project: :class:`stawebg.project.Project`
        """
        self._project = project
        self._name = name
        self._root = None
        self._other_files = []
        self._config = self._project._config
        self._used_layouts = []
        self._file_index = []  # List of all existent files in output directory

        print("Found site: " + self._name)

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

    def getConfig(self, key, fail=True, default=None):
        """ Get configuration of project.

        :param key: Key of config option.
        :type key: list of strings

        :param fail: Print error message and exit if option is not found in
                     configuration file.
        :type fail: bool

        :param default: Default value if option is not found.
        :type default: type of expected value.

        :return: value of option
        """
        return self._config.get(key, fail, default)

    def getAbsSrcPath(self):
        """ Get absolute path of source directory.

        :rtype: str
        """
        return os.path.join(self.getConfig(['dirs', "sites"]), self._name)

    def getAbsDestPath(self):
        """ Get absolute path of destination directory.

        :rtype: str
        """
        return os.path.join(self._project.getOutputDir(), self._name)

    def getProject(self):
        """ Get corresponding project.

        :rtype: :class:`stawebg.project.Project`
        """
        return self._project

    def getRoot(self):
        """ Get root page.

        :rtype: :class:`stawebg.page.Page`
        """
        return self._root

    def getSiteTitle(self):
        """ Get site title.

        :rtype: str
        """
        return self.getConfig(["title"], False, self._name)

    def getSiteSubtitle(self):
        """ Get site subtitle.

        :rtype: str
        """
        return self.getConfig(["subtitle"], False, "")

    def copy(self):
        """ Copy site to destination directory. """
        print("Create site: " + self._name)

        # Pages
        self._root.copy()

        # Layouts
        for l in self._used_layouts:
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

    def _readHelper(self, dir_path, parent, dir_hidden=False,
                    page_config=None):
        """ Read content and configuration of a site.

        This function is used recursive.

        :param dir_path: Path to look at.
        :type dir_path: str

        :param parent: Parent page.
        :type parent: :class:`stawebg.page.Page`

        :param dir_hidden: Is current directory already hidden?
        :type dir_hidden: bool

        :param page_config: Configuration of the parent directory.
        :type page_config: :class:`stawebg.config.Config`
        """
        index_rename = None
        if page_config:
            index_rename = page_config.get(["files", "rename",
                                            os.path.basename(dir_path)],
                                           False, None)

            # Delete not inherited config
            page_config.delete(["files", "sort"], False)
            page_config.delete(["files", "rename"], False)
        else:
            page_config = self._config

        # Get all files and directories and sort them
        entries = sorted(os.listdir(dir_path))

        # Search config and merge it
        if "stawebg.json" in entries:
            tmp_config = Config(os.path.join(dir_path, "stawebg.json"),
                                Config.directory_struct)
            page_config = Config.merge(page_config, tmp_config, False)

        # Add layout to list -> copy later
        layout = self._project.getLayout(page_config.get(["layout"], False))
        if layout not in self._used_layouts:
            self._used_layouts.append(layout)

        # First we have to find the index file in this directory…
        idx = None
        for f in entries:
            absf = os.path.join(dir_path, f)
            if isIndex(absf, self):
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

        # Build tree
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
            if isCont(absf, self):
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
        """ Create menu relative to cur_page.

        :param cur_page: Page where menu is used.
        :type cur_page: :class:`stawebg.page.Page`

        :rtype: str
        """
        return self._root.createMenu(cur_page)

    def delFromFileIndex(self, path):
        """ Delete generated file from file index.

        The file index is used to find out which files in the output directory
        are old. If you don't use this function your new files could be
        deleted.

        :param path: Path of generated file.
        :type path: str
        """
        if path in self._file_index:
            self._file_index.remove(path)
