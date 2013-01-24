#! /usr/bin/env python

import glob
import os
import sys
import getopt
import csv

params = ["resources-folder=","configuration=","string-csv=","checkImageUseage","checkStringUseage","stringsFileName="]
configuration = None
criticalError = False
files = set([])
imgConstants = []
stringConstants = []
path = None
stringCsv = None
checkImageUseage = False
checkStringUseage = False
stringsFileName = "Localizeable"

def usage():
	print "possible params:"
	for param in params:
		explanation = "(add this param to enable the feature)"
		if param.endswith("="):
			explanation = "(a string)"	
		print "["+param[0:1]+"]"+param[1:]+" "+explanation

try:
	opts, args = getopt.getopt(sys.argv[1:], "crs", params)
except getopt.GetoptError, err:
	# print help information and exit:
	print str(err) # will print something like "option -a not recognized"
	sys.exit(2)


for o, a in opts:
	if  o in ("-r", "--resources-folder"):
		path = a	
	elif  o in ("-s", "--string-csv"):
		stringCsv = a	
	elif  o in ("-c", "--configuration"):
		configuration = a
	elif o in ("--checkImageUseage"):
		checkImageUseage = True
	elif o in ("--checkStringUseage"):
		checkStringUseage = True
	elif o in ("--stringsFileName"):
		stringsFileName = a				
	else:
		assert False, "unhandled option"+ o+a
		
if path == None:
	print "the resource path was not defined"
	usage()
	sys.exit(1)

baseFolder =  os.path.join(os.getcwd(),os.path.split(sys.argv[0])[0])
os.chdir(baseFolder)
resourceConstantsHeaderFile = os.path.join(path,"ResourcesConstants.h")


constantsString = "//this file contains the names of all resouces as constants\n\n"

def scandirs(path):
	for currentFile in glob.glob( os.path.join(path, '*') ):
		if os.path.isdir(currentFile):
			scandirs(currentFile)
		else:
			files.add(os.path.basename(currentFile))
			if currentFile.endswith(".psd"):
				print "fools added a Photoshop file: " + currentFile
				criticalError = True

scandirs(path)

oldFileHash = ""
oldGitHash = ""
if (os.path.exists(resourceConstantsHeaderFile)):
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
process = os.popen("git rev-parse HEAD","r")
gitHash = process.readline().strip()
process = os.popen("git log -1 --pretty=format:'%H %aD %cn'","r")
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

if stringCsv is not None:
	localFile = open("../../resources/{0}.strings".format(stringsFileName), 'w')
	
	constantsString += "\n\n"
	stringCsvFile = open(stringCsv,"r")
	strings = csv.reader(stringCsvFile)
	for row in strings:
		if len(row[1]) > 0 and not row[len(row)-2].lower() in ["section","type"]:
			
			cleanName = row[0].upper().replace(" ","_")
			constantName = cleanName
			comment = row[len(row)-1]
			german = row[1]
			constantsString += "#define {0} NSLocalizedStringFromTable(@\"{1}\",@\"{2}\",@\"{3}\")\n".format(constantName,stringsFileName, cleanName,comment)
			stringConstants.append(constantName)
			localFile.write("\"{0}\" = \"{1}\";\n".format(cleanName,german))
			
	constantsString += "\n\n"
	
	localFile.close()
		

fileExceptions = ["Default-568h@2x.png"]

for fileName in sorted(files):
	
#	fileName = os.path.basename(filepath)
	
	isImage = ".png" in fileName
	fileNameNoEnding = fileName.split(".")[0].replace("-","_").replace("~","_")
	constantName = fileNameNoEnding.upper();
	
	for forbiddenChar in [":"]:
		if forbiddenChar.lower() in fileName.lower():
			criticalError = True
			print fileName + " contains a fobidden character " + forbiddenChar
	
	if isImage:
		if not "@2x" in fileName:
			name2x = fileName.replace(".png", "@2x.png");
			if not name2x in files:
				print "missing 2x file for:" + fileName
				if not "default" in fileName:
					criticalError = True
			constantName = "IMG_" + constantName
			constantsString += "#define {0} @\"{1}\" \n".format(constantName,fileName)
			imgConstants.append([constantName,fileName])
		else:
			normalName = fileName.replace("@2x.png", ".png");
			# ADDED exception on iPhone5 splashscreen
			if not normalName in files and fileName not in fileExceptions:
				print "missing normal file for:" + fileName
				criticalError = True
	elif ".otf" in fileName:
		constantsString += "#define FONT_" + constantName + " @\"" + fileName + "\" \n"
	elif ".plist" in fileName:
		constantsString += "#define PLIST_" + constantName + " @\"" + fileName + "\" \n"	

if fileSetChanged or gitRevisionChanged or stringsProvided:
	print "writing " + resourceConstantsHeaderFile
	localFile = open(resourceConstantsHeaderFile, 'w')
	localFile.write(constantsString)
	localFile.close()
else:
	print "no changes in " + resourceConstantsHeaderFile
	
if checkStringUseage:
	os.chdir("../../")
	for stringConstant in stringConstants:
		numOfOccurence = len(os.popen("grep -R -i -n '{0}' --include=*.{1} *".format(stringConstant,"{h,m}"),"r").readlines())
		if numOfOccurence <= 1:
			print "{0} seems not to be used in the project".format(stringConstant)
	os.chdir(baseFolder)

imageOccuranceExceptions = ["Default~ipad.png", "Default~iphone.png","Icon-72.png","Icon-Small-50.png","Icon-Small.png"]

unusedImages = []

if checkImageUseage:
	os.chdir("../../")
	for imgSet in imgConstants:
		imgConstant = imgSet[0]
		imgName = imgSet[1]
		if imgName in imageOccuranceExceptions:
			continue
		numOfOccurence = len(os.popen("grep -R -i -n '{0}' --include=*.{1} *".format(imgConstant,"{m,pch}"),"r").readlines())
		if numOfOccurence == 0:
			numOfOccurence = len(os.popen("grep -R -i -n '{0}' --include=*.{1} *".format(imgName,"{xib,plist}"),"r").readlines())
		if numOfOccurence == 0:
			unusedImages.append(imgName)
			print "{0} seems not to be used in the project".format(imgName)
	os.chdir(baseFolder)
	print "unused images: {0}".format(", ".join(unusedImages))


#"and not "debug" in configuration.lower()" should be added
if criticalError and not configuration is None:
	sys.exit(1)
else:
	sys.exit(0)	

				
