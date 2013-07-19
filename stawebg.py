#!/usr/bin/python3

import argparse
from stawebg.data import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="static website generator")
    parser.add_argument("directory", type=str, nargs="?",
                               help='the directory with the project data')
    args = parser.parse_args()

    project_dir=""
    if args.directory:
        project_dir = args.directory

    project = Project(project_dir)
    project.read()
    project.copy()
