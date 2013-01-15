#! /usr/bin/env python

import glob
import os
import sys
import getopt

params = ["resources-folder=","configuration="]
configuration = None
criticalError = False
files = set([])
path = None

def useage():
	print "possible params:"
	for param in params:
		explanation = "(add this param to enable the feature)"
		if param.endswith("="):
			explanation = "(a string)"	
		print "["+param[0:1]+"]"+param[1:]+" "+explanation

try:
	opts, args = getopt.getopt(sys.argv[1:], "cr", params)
except getopt.GetoptError, err:
	# print help information and exit:
	print str(err) # will print something like "option -a not recognized"
	sys.exit(2)


for o, a in opts:
	if  o in ("-r", "--resources-folder"):
		path = a	
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

localFile = open(os.path.join(path,"ResourcesConstants.h"), 'w')
localFile.write(constantsString)
localFile.close()

if criticalError and not configuration is None and not "debug" in configuration.lower():
	sys.exit(1)
else:
	sys.exit(0)	

				
