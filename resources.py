#! /usr/bin/env python

import glob
import os
import sys
import getopt
import csv
import plistlib

params = ["resources-folder=", "configuration=", "string-csv=", "checkImageUsage", "checkStringUsage",
          "stringsFileName=", "stringsFilePath=", "replaceRecursive", "verbose", "infoPlistFile=", "doNotWriteStringDefinitions"]
configuration = None
criticalError = False
files = set([])
imgConstants = []
stringConstants = []
paths = None
stringCsv = None
checkImageUsage = False
checkStringUsage = False
stringsFilePath = ""
stringsFileName = "Localizable"
replaceRecursive = False
verbose = False
infoPlistFilePath = None
infoPlistFile = None
doNotWriteStringDefinitions = False


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
    sys.exit(2)

for o, a in opts:
    if o in ("-r", "--resources-folder"):
        paths = a.split(",")
    elif o in ("-s", "--string-csv"):
        stringCsv = a
    elif o in ("-c", '--configuration'):
        configuration = a
    elif o in "--checkImageUsage":
        checkImageUsage = True
    elif o in "--checkStringUsage":
        checkStringUsage = True
    elif o in "--stringsFileName":
        stringsFileName = a
    elif o in "--stringsFilePath":
        stringsFilePath = a
    elif o in "--replaceRecursive":
        replaceRecursive = True
    elif o in ("--verbose", "-v"):
        verbose = True
    elif o in "--infoPlistFile":
        infoPlistFilePath = a
    elif o in "--doNotWriteStringDefinitions":
        doNotWriteStringDefinitions = True
    else:
        assert False, "unhandled option" + o + a

if paths is None:
    print "the resource path was not defined"
    usage()
    sys.exit(1)

baseFolder = os.path.join(os.getcwd(), os.path.split(sys.argv[0])[0])
os.chdir(baseFolder)
resourceConstantsHeaderFile = os.path.join(paths[0], "ResourcesConstants.h")

constantsString = "//this file contains the names of all resouces as constants\n\n"


def scanDirs(path):
    for currentFile in glob.glob(os.path.join(path, '*')):
        if os.path.isdir(currentFile):
            scanDirs(currentFile)
        else:
            files.add(os.path.basename(currentFile))
            if currentFile.endswith(".psd"):
                print "fools added a Photoshop file: " + currentFile
                criticalError = True

for path in paths:
    scanDirs(path)

oldFileHash = ""
oldGitHash = ""
if os.path.exists(resourceConstantsHeaderFile):
    localFile = open(resourceConstantsHeaderFile, 'r')
    while 1:
        line = localFile.readline()
        if "<hash>" in line and "</hash>" in line:
            hashStart = line.find("<hash>") + len("<hash>")
            hashEnd = line.find("</hash>")
            oldFileHash = str(line[hashStart:hashEnd].lstrip())
        if "<gitHash>" in line and "</gitHash>" in line:
            hashStart = line.find("<gitHash>") + len("<gitHash>")
            hashEnd = line.find("</gitHash>")
            oldGitHash = str(line[hashStart:hashEnd].lstrip())
        if len(oldFileHash) > 0 and len(oldGitHash) > 0:
            break
        if not line:
            break
        pass
    localFile.close()


#changin the directory in the mother git module
os.chdir("../../")
process = os.popen("git rev-parse HEAD", "r")
gitHash = process.readline().strip()
process = os.popen("git log -1 --pretty=format:'%H %aD %cn'", "r")
gitInfo = process.readline()
#changing the directory back
os.chdir(baseFolder)

#hashing the list of files
fileHash = str(hash(frozenset(files)))

fileSetChanged = not (fileHash.startswith(oldFileHash) and len(fileHash) == len(oldFileHash))
gitRevisionChanged = not (gitHash.startswith(oldGitHash) and len(gitHash) == len(oldGitHash))
stringsProvided = stringCsv is not None

constantsString += "//<hash>" + fileHash + "</hash>\n"
constantsString += "//<gitHash>" + gitHash + "</gitHash>\n"
constantsString += "#define GIT_INFO @\"" + str(gitInfo) + "\" \n"
#constantsString += "// Localization\n#define lStr(key) NSLocalizedStringFromTable(key, @\"{0}\", nil)".format(stringsFileName)


def replaceRecursiveAll(a, b):
    print "replacing {0} with {1}".format(a, b)
    sed = "find . -name *.m | while read i; do sed -i'.bak' -e's/{0}/'\"{1}\"'/' $i;rm $i.bak; done".format(a, b)
    os.popen(sed)



if stringCsv is not None:
    # need to handle multiple files
    localFile = open(os.path.join(stringsFilePath, "{0}.strings".format(stringsFileName)), 'w')

    constantsString += "\n\n"
    stringCsvFile = open(stringCsv, "r")
    strings = csv.reader(stringCsvFile)
    for row in strings:
        if len(row[1]) > 0 and not row[len(row) - 2].lower() in ["section", "type"]:
            cleanName = row[0].upper().replace(" ", "_")
            constantName = cleanName
            comment = row[len(row) - 1]
            german = row[1]
            if not doNotWriteStringDefinitions:
                constantsString += "#define {0} NSLocalizedStringFromTable(@\"{2}\",@\"{1}\",@\"{3}\")\n".format(
                    constantName, stringsFileName, cleanName, comment)
            stringConstants.append(constantName)
            localFile.write("\"{0}\" = \"{1}\";\n".format(cleanName, german))

    constantsString += "\n\n"

    localFile.close()

fileExceptions = ["Default-568h@2x.png"]

if infoPlistFilePath is not None:
    infoPlistFile = plistlib.readPlist(infoPlistFilePath)
    infoPlistFile["UIAppFonts"] = []

def addFontToPlist(fileName):
    if infoPlistFile is not None:
        infoPlistFile["UIAppFonts"].append(fileName)


for fileName in sorted(files):

#	fileName = os.path.basename(filepath)

    isImage = fileName.endswith(".png") or fileName.endswith( ".jpg")

    fileNameNoEnding = fileName.split(".")[0]
    fileNameNoEnding_sanitized = fileNameNoEnding.replace("-", "_").replace("~", "_")
    constantName = fileNameNoEnding_sanitized.upper()

    for forbiddenChar in [":"]:
        if forbiddenChar.lower() in fileName.lower():
            criticalError = True
            print fileName + " contains a fobidden character " + forbiddenChar

    if isImage:
        if "568h" in fileName:
            print "ignoring {0} because ist a long phone file".format(fileName)
            continue
        if not "@2x" in fileName:
            name2x = fileName.replace(".png", "@2x.png");
            if not name2x in files:
                print "missing 2x file for:" + fileName
                if not "default" in fileName:
                    criticalError = True
            constantName = "IMG_" + constantName
            constantsString += "#define {0} @\"{1}\" \n".format(constantName, fileName)
            imgConstants.append([constantName, fileName])
            if replaceRecursive:
                replaceRecursiveAll("@\"{0}\"".format(fileName), constantName)
                replaceRecursiveAll("@\"{0}\"".format(fileNameNoEnding), constantName)
        else:
            normalName = fileName.replace("@2x.png", ".png");
            # ADDED exception on iPhone5 splashscreen
            if not normalName in files and fileName not in fileExceptions:
                print "missing normal file for: {0}".format(fileName)
                criticalError = True
    elif ".otf" in fileName or ".ttf" in fileName:
        constantsString += "#define FONT_{0} @\"{1}\" \n".format(constantName, fileNameNoEnding)
        if infoPlistFile is not None:
            addFontToPlist(fileName);
    elif ".plist" in fileName:
        constantsString += "#define PLIST_{0} @\"{1}\" \n".format(constantName, fileName)

if infoPlistFile is not None:
    if len(infoPlistFile["UIAppFonts"]) > 0:
        print "writing the modified plist"
        plistlib.writePlist(infoPlistFile, infoPlistFilePath)
    else:
        print "not writing the modified plist because no fonts were found"

if fileSetChanged or gitRevisionChanged or stringsProvided:
    print "writing " + resourceConstantsHeaderFile
    localFile = open(resourceConstantsHeaderFile, 'w')
    localFile.write(constantsString)
    localFile.close()
else:
    print "no changes in " + resourceConstantsHeaderFile

if checkStringUsage:
    os.chdir("../../")
    for stringConstant in stringConstants:
        numOfOccurences = len(
            os.popen("grep -R -i -n '{0}' --include=*.{1} *".format(stringConstant, "{h,m}"), "r").readlines())
        if numOfOccurences <= 1:
            print "{0} seems not to be used in the project".format(stringConstant)
    os.chdir(baseFolder)

imageOccuranceExceptions = ["Default~ipad.png", "Default~iphone.png", "Icon-72.png", "Icon-Small-50.png",
                            "Icon-Small.png"]

unusedImages = []


def logVerbose(param):
    if verbose:
        print(param)


if checkImageUsage:
    os.chdir("../../")
    for imgSet in imgConstants:

        imgConstant = imgSet[0]
        imgName = imgSet[1]

        logVerbose("checking useage of {0} and {1}".format(imgConstant, imgName))

        if imgName in imageOccuranceExceptions:
            continue
        numOfOccurences = len(
            os.popen("grep -R -i -n '{0}' --include=*.{1} *".format(imgConstant, "{m,pch}"), "r").readlines())
        if numOfOccurences == 0:
            numOfOccurences = len(
                os.popen("grep -R -i -n '{0}' --include=*.{1} *".format(imgName, "{xib,plist}"), "r").readlines())
        if numOfOccurences == 0:
            unusedImages.append(imgName)
            print "{0} seems not to be used in the project".format(imgName)
    os.chdir(baseFolder)
    print "unused images: {0}".format(", ".join(unusedImages))


if criticalError and (configuration is not None) and (not "debug" in configuration.lower()):
    print "errors where there should not be any!"
    sys.exit(1)
else:
    sys.exit(0)


