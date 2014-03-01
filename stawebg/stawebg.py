#!/usr/bin/python3

import argparse
import os
from stawebg.project import Project
from stawebg.version import version

def run():
    parser = argparse.ArgumentParser(description="static website generator")
    parser.add_argument("directory", nargs="?", default=os.getcwd(),
                        help='the web project root directory')
    parser.add_argument("-t", "--test", action='store_true',
                        help='write output to test directory')
    parser.add_argument("-o", "--output", metavar="output",
                        type=str, default=None,
                        help='write output to this directory')
    parser.add_argument("-v", "--version", action="version",
                        version="%(prog)s " + version)

    args = parser.parse_args()

    project = Project(args.directory, args.test, args.output)
