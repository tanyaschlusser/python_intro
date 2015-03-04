#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
get_base_library_packages.py

This pulls data from the Python documentation listing
https://docs.python.org/2/py-modindex.html

I had to do "View Source" on that page to find something
that uniquely identified the things on the page I wanted
and then I could use BeautifulSoup to get those things.
"""
import requests  # for HTTP requests and much more
import sys  # to get command line arguments
from bs4 import BeautifulSoup  # to parse XML / html

default_outfile_name = "base_library_packages.txt"

def get_base_packages(outfile_name=default_outfile_name):
    response = requests.get("https://docs.python.org/2/py-modindex.html")
    soup = BeautifulSoup(response.text)

    modules = soup.find_all("tt", attrs={"class":"xref"})

    with open(outfile_name, "w") as outfile:
        for m in modules:
            if '.' not in m.text:
                # Ignore submodules by skipping anything
                # that has a '.' in the name
                outfile.write(m.text)
                outfile.write("\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print "Writing module list to file: ", sys.argv[1]
        get_base_packages(sys.argv[1])
    else:
        print "Writing module list to file: ", default_outfile_name
        get_base_packages()
