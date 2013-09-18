#!/usr/bin/python3

import json
import os
from copy import deepcopy
from stawebg.helper import fail


class Config:
    global_struct = {"dirs": (dict, {"sites": (str, None, False),
                                     "layouts": (str, None, False),
                                     "out": (str, None, False),
                                     "test": (str, None, True)}, False),
                     "files": (dict, {"index": (list, str, True),
                                      "content": (list, str, True),
                                      "hidden": (list, str, True),
                                      "exclude": (list, str, True)}, True),
                     "markup": ("mapping",
                                (str, (list, str, True), True),
                                True),
                     "locale" : (str, None, True),
                     "timeformat" : (str, None, True),
                     "timezone" : (str, None, True),
                     "variables": ("mapping",
                                   (str, str, True),
                                   True)}
    site_struct = {"dirs": (None, None, None),
                   "markup": (None, None, None),
                   "title": (str, None, True),
                   "subtitle": (str, None, True),
                   "layout": (str, None, True),
                   "files": (dict, {"index": (list, str, True),
                                    "content": (list, str, True),
                                    "hidden": (list, str, True),
                                    "exclude": (list, str, True)}, True),
                   "locale" : (str, None, True),
                   "timeformat" : (str, None, True),
                   "timezone" : (str, None, True),
                   "url": (str, None, True),
                   "variables": ("mapping",
                                 (str, str, True),
                                 True)}
    directory_struct = {"layout": (str, None, True),
                        "files": (dict,
                                  {"sort": (list, str, True),
                                   "exclude": (list, str, True),
                                   "hidden": (list, str, True),
                                   "rename": ("mapping", (str, str), True)},
                                  True),
                        "blog": (dict,
                                 {"dir": (str, None, False),
                                  "per-page": (int, None, True),
                                  "rss": (dict,
                                          {"file": (str, None, False),
                                           "title": (str, None, False),
                                           "description": (str, None, False),
                                           "copyright": (str, None, True),
                                           "show_generator": (bool, None, True),
                                           "title_length": (int, None, True),
                                           "content_length": (int, None, True)},
                                          True)},
                                 True),
                        "variables": ("mapping",
                                       (str, str, True),
                                       True)}

    def __init__(self, filename, struct, displayname=None):
        self._config = {}

        if displayname:
            self._displayname = displayname
        else:
            self._displayname = filename

        if filename:  # filename is not set if Config is created in merge
            try:
                conff = open(filename, "r")
                try:
                    self._config = self._checkDict(json.load(conff), struct)
                except Exception as e:
                    fail("Error parsing configuration file: " + filename +
                         os.linesep + str(e))
                finally:
                    conff.close()
            except IOError as e:
                fail("Can't open file: " + filename + os.linesep + str(e))

    def get(self, key, do_fail=True, default=None):
        config = self._config
        for k in key:
            config = config.get(k)

            if not config:
                if do_fail:
                    fail("Can't find " + str(key))
                else:
                    return default

        return config

    def delete(self, key, do_fail=False):
        data = self.get(key[:-1], do_fail)

        if key[-1] in data:
            del data[key[-1]]
        elif do_fail:
            fail("Can't find " + str(key))

    def add(self, key, value):
        config = self._config
        for n, k in enumerate(key):
            if config.get(k):
                config = config.get(k)
            else:
                if n == len(key)-1:
                    config[k] = value
                else:
                    config[k] = {}
                    config = config[k]

    def copy(self):
        return deepcopy(self)

    def _checkDict(self, obj, struct):
        if not struct:
            return obj

        if type(obj) != dict:
            fail(str(obj) + " should be a dictionary in file " +
                 self._displayname)

        result = {}
        for k in struct:
            if not obj.get(k) is None:
                # Check dictionary
                if struct[k][0] == dict:
                    if type(obj[k]) == dict:
                        result[k] = self._checkDict(obj[k], struct[k][1])
                        del obj[k]
                        # TODO: delete empty dict?
                    else:
                        fail(str(k) + " should be a dictionary in file " +
                             self._displayname)
                # Check list
                elif struct[k][0] == list:
                    self._checkList(obj[k], struct[k][1], k)
                    result[k] = obj[k]
                    del obj[k]
                # Mapping
                # (type1, type2, "1") means type1 : type2
                # (type1, type2, "+") means type1 : [type2]
                elif struct[k][0] == "mapping":
                    self._checkMapping(obj[k], struct[k][1], str(k))
                    result[k] = obj[k]
                    del obj[k]
                # Mustn't be here
                elif struct[k][0] is None:
                    fail("Can't configure " + str(k) + " in " +
                         self._displayname)
                # Check other types
                elif struct[k][0] == type(obj[k]):
                    result[k] = obj[k]
                    del obj[k]
                # Requested and given type are not equal
                else:
                    fail(str(k) + " has the wrong type in file " +
                         self._displayname)
            elif not struct[k][2] and struct[k][0]:  # Not optional
                fail("Can't find " + str(k) + " in " + self._displayname)

        if len(obj):
            print("Warning: unknown config options in file " +
                  self._displayname + ": " + str(obj))

        return result

    def _checkList(self, lst, typeof, name):
        if type(lst) != list:
            fail(name + " should be a list in file " + self._displayname)
        for i in lst:
            if type(i) != typeof:
                fail("Some elements of the list " + name + " in the file " +
                     self._displayname + " have a wrong type")

    def _checkMapping(self, mapping, typeof, name):
        if type(mapping) != dict:
            fail(name + " must be a dictionary")
        # View all entries
        # Mapping: type1 -> type2
        # type1 must be primitive
        for i in mapping:
            # Check type1
            if type(i) == typeof[0]:
                # Check type2
                # type2 is tupel -> complex datatype
                if type(typeof[1]) == tuple and len(typeof[1]) == 3:
                    if typeof[1][0] == dict:
                        mapping[i] = self._checkDict(mapping[i], typeof[1][1])
                    elif typeof[1][0] == list:
                        self._checkList(mapping[i], typeof[1][1], mapping[i])
                    else:
                        fail("config.py, _checkMapping: type not supported")
                elif type(mapping[i]) != typeof[1]:
                    fail(str(mapping[i]) + " has the wrong type in file " +
                         self._displayname)
            else:
                fail(name + " has the wrong type in file " + self._displayname)

    @staticmethod
    def merge(a, b, overwrite_lists=False):
        if not a:
            return b
        if not b:
            return a

        result_dict = deepcopy(a._config)
        b_dict = b._config

        result = Config._mergeDict(result_dict, b_dict, overwrite_lists)
        result = Config(None, None, a._displayname + " or " + b._displayname)
        result._config = result_dict

        return result

    @staticmethod
    def _mergeDict(a, b, overwrite_lists):
        for k in b:
            if k in a:
                if type(b[k]) == dict:
                    a[k] = Config._mergeDict(a[k], b[k], overwrite_lists)
                elif not overwrite_lists and type(b[k]) == list:
                    a[k].extend(b[k])
                else:
                    a[k] = b[k]
            else:
                a[k] = b[k]

        return a
