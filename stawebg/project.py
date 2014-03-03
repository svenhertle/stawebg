#!/usr/bin/python3
# -*- coding: utf-8 -*-

import locale
import os
from stawebg.config import Config
from stawebg.helper import (listDirs, fail)
from stawebg.layout import Layout
from stawebg.site import Site


class Project:
    """A project is a collection of sites and layouts"""
    def __init__(self, project_dir="", test=False, output=None):
        """ Reads all sites and create output.

        :param project_dir: directory off stawebg project.
        :type project_dir: str

        :param test: write output to test directory, not to out directory.
        :type test: bool

        :param output: other output directory than test and out.
        :type output: str
        """
        self._sites = []
        self._layouts = {}

        self._root_dir = project_dir
        self._test = test
        self._other_output = output

        # Read global config from stawebg.json
        self._config = Config(os.path.join(self._root_dir, "stawebg.json"),
                              Config.global_struct)

        # Make directories absolute
        dirs = self._config.get(["dirs"])
        for k in dirs:
            dirs[k] = os.path.join(self._root_dir, dirs[k])

        # Set locale
        try:
            locale.setlocale(locale.LC_ALL, self.getConfig(["locale"],
                             False, ""))
        except locale.Error as e:
            fail("Failed to set the locale \"" +
                 self.getConfig(["locale"], False, "") + "\": " + str(e))

        # Add all layouts to list
        for name in listDirs(self.getConfig(['dirs', 'layouts'])):
            self._layouts[name] = Layout(self, name)

        # Add all site directories to list
        for s in listDirs(self.getConfig(['dirs', 'sites'])):
            site = Site(s, self)
            self._sites.append(site)

        # copy files to out dir
        for s in self._sites:
            s.copy()

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

    def getLayout(self, name=None):
        """ Get layout for given name

        :param name: Name of layout.
        :type name: str

        :rtype: :class:`stawebg.layout.Layout`
        """
        if not name:
            name = "default"

        layout = self._layouts.get(name)

        if not layout:
            fail("Can't find layout: " + name)

        return layout

    def getOutputDir(self):
        """ Get directory for output.

        This depends on runtime options like --test or -\ -output <dir>.

        :rtype: str
        """
        if self._other_output:
            return self._other_output
        elif self._test:
            return self.getConfig(["dirs", "test"])
        else:
            return self.getConfig(["dirs", "out"])
