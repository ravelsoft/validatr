#!/usr/bin/env python

from simplejson import load
from test import validate

f = open("/home/chris/Downloads/biens.json", "r")
o = load(f)
f.close()

print validate(o)
