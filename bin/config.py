#!/usr/bin/python3

import os

dirs = {}
dirs["bin"]         = os.path.abspath(os.path.dirname(__file__))
dirs["root"]        = os.path.dirname(dirs["bin"])
dirs["sites"]       = os.path.join(dirs["root"], "sites")
dirs["layout"]      = os.path.join(dirs["root"], "layout")
dirs["out"]         = os.path.join(dirs["root"], "out")

layout = {}
layout["head"]      = os.path.join(dirs["layout"], "default", "head.html")
layout["bottom"]    = os.path.join(dirs["layout"], "default", "bottom.html")
layout["css"]       = os.path.join(dirs["layout"], "default", "stylesheet.css") #TODO: support more than one css file
