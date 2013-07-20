#!/usr/bin/python3

import argparse
import os
from stawebg.data import Project

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="static website generator")
    parser.add_argument("directory", nargs="?", default=os.getcwd(),
                        help='the web project root directory')

    args = parser.parse_args()

    project = Project(args.directory)
    project.read()
    project.copy()
