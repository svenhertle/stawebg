#!/usr/bin/python3

from data import *
import config

if __name__ == "__main__":
    project = Project()
    project.read()
    project.copy()
