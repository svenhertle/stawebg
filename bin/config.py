#!/usr/bin/python3

from os.path import *

#
# Directories
#

dirs = {}

# Diectory with binary files
dirs["bin"]         = abspath(dirname(__file__))

# Root directory of stawebg
dirs["root"]        = dirname(dirs["bin"])

# Directory with site content
dirs["sites"]       = join(dirs["root"], "sites")

# Directory with layout files
dirs["layouts"]      = join(dirs["root"], "layouts")

# Directory for output
dirs["out"]         = join(dirs["root"], "out")


#
# Layout
#

layout = {}

# Default layout
layout["default"] = "default"

# File with begin of html code
layout["head"]      = "head.html"

# File with end of html code
layout["bottom"]    = "bottom.html"
