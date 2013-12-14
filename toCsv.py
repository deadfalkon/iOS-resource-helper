#! /usr/bin/env python



import xml.etree.ElementTree as etree
import csv
import os
import getopt
import sys

params = ["android-strings="]

def usage():
    print "possible params:"
    for param in params:
        explanation = "(add this param to enable the feature)"
        if param.endswith("="):
            explanation = "(a string)"
        print "[" + param[0:1] + "]" + param[1:] + " " + explanation

try:
    opts, args = getopt.getopt(sys.argv[1:], "crs", params)
except getopt.GetoptError, err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"

androidStringFile = None
csvFileName = "strings.csv"

for o, a in opts:
    if o in "--android-strings":
        androidStringFile = a
    else:
        assert False, "unhandled option" + o + a

baseFolder = os.path.join(os.getcwd(), os.path.split(sys.argv[0])[0])
os.chdir(baseFolder)


tree = etree.parse(androidStringFile)
root = tree.getroot()

translations = {}

for child in root:
    print child.tag, child.attrib["name"], child.text
    if child.tag != "string":
        continue

    translationKey = child.attrib["name"].upper()
    translation = child.text
    if child.text is None:
        translation = ""

    translation = translation.encode("utf-8")

    translations[translationKey] = translation

with open(csvFileName, 'wb') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    spamwriter.writerow(["key", "description", "DE"])

    for key in sorted(translations.keys()):
        spamwriter.writerow([key, "", translations[key]])




