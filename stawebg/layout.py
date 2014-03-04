#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
from subprocess import Popen, PIPE
from stawebg.helper import (findFiles, fail, mkdir)
from stawebg.otherfile import OtherFile


class Layout:
    """ One layout für a page. """
    def __init__(self, project, name):
        """ Read template.

        :param project: stawebg project.
        :type project: :class:`stawebg.project.Project`

        :param name: Name of layout
        :type name: str
        """
        self._project = project
        self._name = name
        self._dir = os.path.join(self._project.getConfig(['dirs', 'layouts']),
                                 name)
        self._other_files = []

        # TODO: is this list necessary?
        self._files = {}
        self._files["template"] = os.path.join(self._dir, 'template.html')

        self._templates = {}

        print("Found layout: " + self._name)

        # Check if template files exist and read them
        for i in self._files:
            try:
                self._templates[i] = open(self._files[i]).read()
            except IOError as e:
                fail("Error reading \"" + self._files[i] + "\": " + str(e))

        # Search other files (CSS, images, ...)
        for f in findFiles(self._dir, [".html"]):
            print("\tFound file: " + f)
            self._other_files.append(OtherFile(self._dir,
                                               os.path.relpath(f, self._dir)))

    def copy(self, site):
        """ Copy layout to output of one site.

        :param site: Site where layout is used.
        :type site: :class:`stawebg.site.Site`
        """
        for f in self._other_files:
            path = os.path.join(site.getAbsDestPath(), self.getOutputDir())
            f.copy(site, path)

    def getOutputDir(self):
        """ Get relative output directory of layout.

        This is the path relative to the document root of the site
        (e.g. style/default).

        :rtype: str
        """
        return os.path.join("style", self._name)

    def useTemplate(self, src, reps, user_reps, ext=None):
        """ Create output from source file.

        This contains:

        * Get content from markup interpreter using source
        * Apply user replacements to template
        * Replace "%CONTENT%" by content.
        * Apply user replacements again
        * Apply stawebg replacements

        src may be a filename or the source code as string.
        If ext is none, src is interpreted as filename and the file extension
        comes from the filename. Is ext is specified stawebg uses the
        corresponding markup interpreter to create HTML.

        :param src: Source for content (filename or source as string,
                    see above).
        :type src: str

        :param reps: Replacement from stawebg.
        :type reps: dict

        :param user_reps: User replacements
        :type reps: dict

        :param ext: File extension if src is source code.
        :type ext: str

        :return: Complete output using template and content
                 (source interpreted by markup interpreter).
        :rtype: (str, str)
        """
        content = self._translateMarkup(src, ext)

        text = self._templates["template"][:]
        text = self.replaceKeywords(text, self._transformUserReps(user_reps))
        text = text.replace("%CONTENT%", content)
        text = self.replaceKeywords(text, self._transformUserReps(user_reps))
        text = self.replaceKeywords(text, reps)

        return (text, content)

    def _translateMarkup(self, src, ext=None):
        """ Translate source code to HTML with a markup interpreter.

        :param src: Source code
        :type src: str

        :param ext: File extension used to determine markup interpreter
                    (see :func:`useTemplate`).
        :type ext: str

        :rtype: str
        """
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
            try:
                p = Popen(tool, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            except PermissionError as e:
                fail(' '.join(tool) + ": " + str(e))
            except FileNotFoundError as e:
                fail(' '.join(tool) + ": " + str(e))
            out, err = p.communicate(text.encode())
            if p.returncode:
                fail(' '.join(tool) + ": " + err.decode())
            if len(err):
                print("Warning from " + ' '.join(tool) + ": " + err.decode())
            return out.decode()
        return text

    def replaceKeywords(self, text, reps):
        """ Replace keywords from dictionary.

        :param text: Text where keywords should be replaced.
        :type text: str

        :param reps: Dictionary with keyword and replacement.
        :type reps: dict

        :rtype: str
        """
        if not reps:
            return text

        trans = lambda m: reps[m.group(0)]
        rc = re.compile('|'.join(map(re.escape, reps)))
        return rc.sub(trans, text)

    def _transformUserReps(self, reps):
        """ Create dictionary for further replace operations from configured
        user replacements.

        This functions changed the keyword from XYZ to %_XYZ%.

        :param reps: User replacements from configuration file.
        :type reps: dict

        :rtype: dict
        """
        result = {}
        for i in reps:
            result["%_" + i + "%"] = reps[i]
        return result
