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

class Layout:
    def __init__(self, project, name):
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

    def copy(self, dest, site):
        for f in self._other_files:
            f.copy(site, os.path.join(dest, self.getSubdir()))

    def getSubdir(self):
        return os.path.join("style", self._name)

    def useTemplate(self, src, reps, user_reps, ext=None):
        content = self._translateMarkup(src, ext)

        text = self._templates["template"][:]
        text = self.replaceKeywords(text, self._transformUserReps(user_reps))
        text = text.replace("%CONTENT%", content)
        text = self.replaceKeywords(text, self._transformUserReps(user_reps))
        text = self.replaceKeywords(text, reps)

        return (text, content)

    def createOutput(self, dest, text):  # TODO: move to helper.py?, use for other files too?
        mkdir(os.path.dirname(dest))

        try:
            outf = open(dest, 'w')
            outf.write(text)
            outf.close()
        except IOError as e:  # TODO: check exceptions
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
        if not reps:
            return text

        trans = lambda m: reps[m.group(0)]
        rc = re.compile('|'.join(map(re.escape, reps)))
        return rc.sub(trans, text)

    def _transformUserReps(self, reps):
        result = {}
        for i in reps:
            result["%_" + i + "%"] = reps[i]
        return result
