iOS-resource-helper
===================

A python script that helps you stay sane when working with external people who provide your iOS project with resources

#Integration with Xcode

In our project, we cloned the iOS-resource-helper to **/submodules/iOS-resource-helper/** and integrated the script as a script like this in XCode:

![image](https://raw.github.com/sinnerschrader-mobile/iOS-resource-helper/master/documentation/sample_XCode_integration.png)

Scan one folder:	

	./submodules/iOS-resource-helper/resources.py --configuration=${CONFIGURATION} --resources-folder=../../resources

You can also scan multiple folders:	
	
	./submodules/iOS-resource-helper/resources.py --configuration=${CONFIGURATION} --resources-folder=../../resources,../../otherResources
		
In Xcode 5 it became harder to add a custom script build script:

![image](https://raw.github.com/deadfalkon/iOS-resource-helper/master/documentation/xCode5addScriptBuildPhase.png)
