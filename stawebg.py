#!/usr/bin/python3

import argparse
import os
from stawebg.data import Project

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="static website generator")
    parser.add_argument("directory", nargs="?", default=os.getcwd(),
                        help='the web project root directory')
    parser.add_argument("-t", "--test", action='store_true',
                        help='write output to test directory')

    args = parser.parse_args()

    project = Project(args.directory, args.test)
    project.read()
    project.copy()
