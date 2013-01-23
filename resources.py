#! /usr/bin/env python

import glob
import os
import sys
import getopt
import csv

params = ["resources-folder=","configuration=","string-csv="]
configuration = None
criticalError = False
files = set([])
path = None
stringCsv = None

def useage():
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
	else:
		assert False, "unhandled option"+ o+a
		
if path == None:
	print "the resource path was not defined"
	useage()
	sys.exit(1)

baseFolder =  os.path.join(os.getcwd(),os.path.split(sys.argv[0])[0])
os.chdir(baseFolder)
resourceConstantsHeaderFile = os.path.join(path,"ResourcesConstants.h")


constantsString = "//this file contains the names of all resouces as constants\n\n"

if stringCsv is not None:
	stringCsvFile = open(stringCsv,"r")
	strings = csv.reader(stringCsvFile)
	for row in strings:
		if len(row[1]) > 0 and not row[len(row)-2].lower() in ["section","type"]:
			
			name = row[0].upper().replace(" ","_")
			constantsString += "#define STRING_" + name + " NSLocalizedString(\"" + row[0] + "\",\"" + row[len(row)-1]  +"\")\n"
	constantsString += "\n\n"

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

fileSetChanged =  not (fileHash.startswith(oldFileHash) and len(fileHash) == len(oldFileHash))
gitRevisionChanged = not (gitHash.startswith(oldGitHash) and len(gitHash) == len(oldGitHash))
stringsProvided = stringCsv is not None


constantsString += "//<hash>" + fileHash + "</hash>\n"
constantsString += "//<gitHash>" + gitHash + "</gitHash>\n"
constantsString += "#define GIT_INFO @\"" + str(gitInfo) + "\" \n"


fileExceptions = ["Default-568h@2x.png"]
for filename in sorted(files):
	
#	filename = os.path.basename(filepath)
	
	isImage = ".png" in filename
	filenameNoEnding = filename.split(".")[0].replace("-","_").replace("~","_")
	constantName = filenameNoEnding.upper();
	
	for forbiddenChar in [":"]:
		if forbiddenChar.lower() in filename.lower():
			criticalError = True
			print filename + " contains a fobidden character " + forbiddenChar
	
	if isImage:
		if not "@2x" in filename:
			name2x = filename.replace(".png", "@2x.png");
			if not name2x in files:
				print "missing 2x file for:" + filename
				if not "default" in filename:
					criticalError = True
			constantsString += "#define IMG_" + constantName + " @\"" + filename + "\" \n"
		else:
			normalName = filename.replace("@2x.png", ".png");
			# ADDED exception on iPhone5 splashscreen
			if not normalName in files and filename not in fileExceptions:
				print "missing normal file for:" + filename
				criticalError = True
	elif ".otf" in filename:
		constantsString += "#define FONT_" + constantName + " @\"" + filename + "\" \n"
	elif ".plist" in filename:
		constantsString += "#define PLIST_" + constantName + " @\"" + filename + "\" \n"	

if fileSetChanged or gitRevisionChanged or stringsProvided:
	print "writing " + resourceConstantsHeaderFile
	localFile = open(resourceConstantsHeaderFile, 'w')
	localFile.write(constantsString)
	localFile.close()
else:
	print "no changes in " + resourceConstantsHeaderFile

#"and not "debug" in configuration.lower()" should be added
if criticalError and not configuration is None:
	sys.exit(1)
else:
	sys.exit(0)	

				
