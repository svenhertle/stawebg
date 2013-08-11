#!/usr/bin/python3

import json
import os
from copy import deepcopy
from stawebg.helper import fail

class Config:
    def __init__(self, filename, struct, displayname=None):
        self._config = {}

        if displayname:
            self._displayname = displayname
        else:
            self._displayname = filename

        if filename:
            self._read(filename, struct)

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

    def copy(self):
        return deepcopy(self)

    def _read(self, filename, struct):
        try:
            conff = open(filename, "r")
            tmp = json.load(conff)
            self._config = self._checkDict(tmp, struct)
        except IOError as e:
            fail("Can't open file: " + filename + os.linesep + str(e))
        except Exception as e:
            fail("Error parsing configuration file: " + filename + os.linesep + str(e))
        conff.close()

    def _checkDict(self, obj, struct):
        if not struct:
            return obj

        result = {}
        for k in struct:
            if obj.get(k):
                # Check dictionary
                if struct[k][0] == dict:
                    if type(obj[k]) == dict:
                        result[k] = self._checkDict(obj[k], struct[k][1])
                        del obj[k]
                        # TODO: delete empty dict?
                    else:
                        fail(str(k) + " should be a dictionary in file " + self._displayname)
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
                    fail("Can't configure " + str(k) + " in " + self._displayname)
                # Check other types
                elif struct[k][0] == type(obj[k]):
                    result[k] = obj[k]
                    del obj[k]
                # Requested and given type are not equal
                else:
                    fail(str(k) + " has the wrong type in file " + self._displayname)
            elif not struct[k][2] and struct[k][0]:  # Not optional
                fail("Can't find " + str(k) + " in " + self._displayname)

        if len(obj):
            print("Warning: unknown config options: " + str(obj))

        return result

    def _checkList(self, lst, typeof, name):
        if type(lst) != list:
            fail(name + " should be a list in file " + self._displayname)
        for i in lst:
            if type(i) != typeof:
                fail("Some elements of the list " + name + " in the file " + self._displayname + " have a wrong type")

    def _checkMapping(self, mapping, typeof, name):
        if type(mapping) != dict:
            fail(name + " must be a dictionary")
        # View all entries
        for i in mapping:
            # Check type1
            if type(i) == typeof[0]:
                # Check type2
                if typeof[2] == "1" and type(mapping[i]) != typeof[1]:
                    pass
                elif typeof[2] == "+":
                    self._checkList(mapping[i], typeof[1], mapping[i])
                else:
                    fail(str(mapping[i]) + " has the wrong type in file " + self._displayname)
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
