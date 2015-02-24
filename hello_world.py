#!/usr/bin/env python
"""
hello_world.py

This confirms that requests is installed and states
the version, which should be 2.7
"""
import requests
import sys

print "Hello World!"
print "The Python version is:", sys.version

version = sys.version_info
if version.major != 2 or version.minor != 7:
    raise(Exception("Version is not 2.7"))
