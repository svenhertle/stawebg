#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import shutil
from stawebg.helper import mkdir


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
        shutil.copyfile(os.path.join(self._src_path_root, self._src_path_rel),
                        os.path.join(out_dir,
                                     os.path.basename(self._src_path_rel)))
