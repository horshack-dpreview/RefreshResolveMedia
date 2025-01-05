#!/usr/bin/env python

#
#############################################################################
#
# WorkerRefreshResolveMedia.py
# Copyright (c) 2025, Horshack
#
# Davinci Resolve has a long-standing issue where it fails to automatically
# detect changes to media files, causing the old/stale version of the media
# to be used. This script solves this issue by telling Resolve to relink
# media clips, using each clip's existing path. This triggers Resolve to
# recognize the latest version of the clip.
#
# This module is licensed under GPL v3: http://www.gnu.org/licenses/gpl-3.0.html
#

#
# defaults/settings
#
defaultAction = 'RefreshSelectedClips'
defaultMethod = 'Relink'
versionPrefixInFilename = "--refresh--"
fDeleteOlderVersionAfterCopyAndReplace = True

#
# imports
#
import os
import shutil
import sys
import time

if 'app' in globals():
    # we're running inside Resolve's python instance, ie script is run view Workplace -> Scripts
    fRunningInsideResolve = True
    resolve = app.GetResolve()
else:
    # running as stand-alone script. FYI, I believe this requires the Studio version
    fRunningInsideResolve = False
    if sys.platform == 'win32':
        sys.path.append(r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules")
    elif sys.platform == 'darwin':
        sys.path.append('/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules')
    import DaVinciResolveScript as dvr
    resolve = dvr.scriptapp("Resolve")


#
# logging logic
#
LOGGING_FLAG_ERRORS     = 0x01
LOGGING_FLAG_WARNINGS   = 0x02
LOGGING_FLAG_INFO       = 0x04
LOGGING_FLAG_VERBOSE    = 0x08
LoggingFlags = LOGGING_FLAG_ERRORS | LOGGING_FLAG_WARNINGS | LOGGING_FLAG_INFO | LOGGING_FLAG_VERBOSE

def isLoggingVerbose():
    return LoggingFlags & LOGGING_FLAG_VERBOSE

def logError(msg):
    if LoggingFlags & LOGGING_FLAG_ERRORS:
        print("Error: {:s}".format(msg))
        
def logWarning(msg):
    if LoggingFlags & LOGGING_FLAG_WARNINGS:
        print("Warning: {:s}".format(msg))

def logInfo(msg):
    if LoggingFlags & LOGGING_FLAG_INFO:
        print(msg)

def logVerbose(msg):
    if LoggingFlags & LOGGING_FLAG_VERBOSE:
        print(msg)
 

#
# deletes a media file we created as a version of an original
#
def deleteMediaVersionFile(filename):

    logVerbose("Deleting file \"{:s}\"".format(filename))

    # failsafe - make sure we only attempt to delete files we created
    if filename.find(versionPrefixInFilename) == -1:
        logError("Critical Error: Logic path attempted to delete a non-version file \"{:s}\". Report to developer".format(filename))
        return True

    try:
        os.remove(filename)
    except Exception as e:
        logError("Unable to delete \"{:s}\", {:s}".format(filename, str(e)))
        return True
    return False
 

#
# Adds each clip in 'clips' the list of clips sharing the same
# directory, creating new lists for any clips with a directory
# that hasn't been encountered yet
#
def addClipsToFolderDict(dictFolderList, clips):
    if clips:
        for clip in clips:
            if isLoggingVerbose():
                logVerbose("Found clip \"{:s}\", type \"{:s}\", path \"{:s}\"".format(\
                    clip.GetClipProperty('Clip Name'),
                    clip.GetClipProperty('Type'),
                    clip.GetClipProperty('File Path')))
            path = os.path.dirname(clip.GetClipProperty('File Path'))
            # we assume clip is a media file if it has a path defined
            if path:            
                if path in dictFolderList:
                    # previous clips have been found with this path. add this clip
                    listClipsInFolder = dictFolderList[path]
                    listClipsInFolder.append(clip)
                else:
                    # first time this clip's path was encountered. create new list
                    dictFolderList[path] = [clip]


#
# Processes media items in the specified folder, including
# items in all subfolders within folder
#
def addFolderClipsToFolderDict(dictFolderList, folder):
    if folder:
        # recurse through subfolders before processing this folder's clips
        subFolders = folder.GetSubFolderList()
        for subFolder in subFolders:
            addFolderClipsToFolderDict(dictFolderList, subFolder)

        # process this folder's clips
        clipsInFolder = folder.GetClipList()
        addClipsToFolderDict(dictFolderList, clipsInFolder)


#
# Converts a path to a media file into its parts, including potentially
# a version # if it's a filename we previously generated
# 
def decodePathWithVersionNumber(path):
    directory, filenameWithExt = os.path.split(path)
    filename, ext = os.path.splitext(filenameWithExt)
    indexFirstCharRefreshSegmentInFilename = filename.find(versionPrefixInFilename) 
    if indexFirstCharRefreshSegmentInFilename != -1:
        # file has a version sequence
        indexFirstDigitRefreshNumInFilename = indexFirstCharRefreshSegmentInFilename+len(versionPrefixInFilename) # past '-refresh-'
        # extract version # from filename
        try:
            versionNum = int(filename[indexFirstDigitRefreshNumInFilename:indexFirstDigitRefreshNumInFilename+4])
        except ValueError:
            # non-digits after refresh prefix. Shouldn't happen. As failsafe don't rename
            logWarning("File \"{:s}\" has a mangled rename".format(path))
            return (None, None, None, None)
        filename = filename[0:indexFirstCharRefreshSegmentInFilename] # filename root without version # suffix
    else:
        versionNum = -1
    return (directory, filename, ext, versionNum)


#
# performs Resolve 'Replace Clip' operation. Normally this automatically
# changes the clip's name to match its new filename but sometimes
# resolve doesn't change the clip name, so we change that as well
#
def resolveReplaceClip(clip, fullPath, newClipName):
    if not clip.ReplaceClip(fullPath):
        return True
    if newClipName:
        clip.SetClipProperty('Clip Name', newClipName)
        # note: any failure to set the clip name isn't a serious error so we ignore it
    return False


#
# Replaces a clip, using a filename with an embedded version # that increments
# each time the clip is replaced. This is done to workaround the Resolve bug where
# it caches a clip in RAM based on its name, ie to force Resolve to recognize the
# latest version of a media file we have to generate a unique filename each time
# the user refreshes (regenerates) a new render of the media
#
# Example of usage:
# 
#   1)  Original media file is named mypict.jpg and user adds it to their Resolve project
#   2a) User later decides he needs to generate a new version of mypict.jpg, using an
#       external tool such as Photoshop. He generates new render into mypict.jpg but
#       Resovle fails to recognize the contents have changed (Resolve bug)
#   2b) This method is called, copies mypict.jpg -> mypict--refresh--0001.jpg, and 
#       tells Resolve to replace the clip with the file of the new name, to force
#       Resolve to see the contents of the image have changed. 
#   3a) User decides he needs to generate a new image again. He generates a new render
#       into mypict.jpg
#   3b) This method is called, copies mypict.jpg -> mypict--refresh--0002.jpg,
#       and tells Resolve to replace the clip with the file of the new name, to force
#       Resolve to see the contents of the image have changed. We delete mypict--refresh--0001.jpg
#   .. repeats as many times as user changes the media ..
#

def replaceClipWithCopy(clip):

    #
    # we use a "--refresh--xxxx" suffix to generate unique renamed filenames
    #
    # For example:
    #       mypict.jpg                  -> mypict--refresh--0001.jpg
    #       mypict--refresh--0001.jpg   -> mypict--refresh--0002.jpg
    #
    # Variables:
    #
    #   'origFullPath'
    #   The original filename of media, ie the filename the user put his media into
    #   Example: mypict.jpg
    #
    #   'currentVersionFullPath', 'newVersionFullPath'
    #   currentVersionFullPath - Most recent version filename generated by this method (name on entry to this invocation)
    #   newVersionFullPath - Filename this invocation generates and switches to
    #   Example: mypict.jpg (current) -> mypict--refresh--0001.jpg (new)
    #   Example: mypict--refresh--0001.jpg (current) -> mypict--refresh--0002.jpg (new)
    #
    #
    currentVersionFullPath = clip.GetClipProperty('File Path')
    directory, filename, ext, versionNum = decodePathWithVersionNumber(currentVersionFullPath)
    if directory == None:
        # something wrong with filename - don't process
        return True
    if versionNum == -1:
        # first time we're processing this file - set version # to 1
        versionNum = 1
    else:
        # advance version #
        versionNum += 1        
    newVersionFilename = "{:s}{:s}{:04d}".format(filename, versionPrefixInFilename, versionNum)
    newVersionFullPath = os.path.join(directory, newVersionFilename + ext)
    origFullPath = os.path.join(directory, filename + ext)
        
    if isLoggingVerbose():
        logVerbose("Copying \"{:s}\" to \"{:s}\"".format(origFullPath, newVersionFullPath))
    try:
        shutil.copyfile(origFullPath, newVersionFullPath)
    except Exception as e:
        logError("Unable to copy \"{:s}\" to \"{:s}\": {:s}".format(origFullPath, newVersionFullPath, str(e)))
        return True

    logVerbose("Replacing with {:s}".format(newVersionFullPath))
    if resolveReplaceClip(clip, newVersionFullPath, newVersionFilename):
        deleteMediaVersionFile(newVersionFullPath) # delete copied file when replace fails
        logError("ReplaceClip() failed for \"{:s}\"".format(currentVersionFullPath))
        return True
    # successful - delete previous version if there is one (never delete user's original!)
    if fDeleteOlderVersionAfterCopyAndReplace and currentVersionFullPath != origFullPath:
        deleteMediaVersionFile(currentVersionFullPath)
    
    return False


#
# Replaces a clip with the original that version copies were made from. This is
# done to revert the clip to the original media, typically for media the user
# is done changing. The current version of the media file is deleted
#
# Example of usage:
#
#   1)  Original media file is named mypict.jpg and user adds it to their Resolve project
#   2)  User performs replaceClipWithCopy() that replaces mypict.jpg with mypict--refresh--0001.jpg
#   3)  User performs replaceClipWithCopy() that replaces mypict.jpg with mypict--refresh--0002.jpg
#   ...
#   x)  User performs replaceClipWithOriginal() that replaces mypict--refresh--0002.jpg with mypict.jpg
#
#
def replaceClipWithOriginal(clip):
    currentVersionFullPath = clip.GetClipProperty('File Path')
    directory, filename, ext, versionNum = decodePathWithVersionNumber(currentVersionFullPath)
    if directory == None:
        # something wrong with filename - don't process
        return True        
    if versionNum == -1:
        # clip is already set to original - nothing to do
        logVerbose("Already at original for \"{:s}\"".format(currentVersionFullPath))
        return True
    origFullPath = os.path.join(directory, filename + ext)
    if os.path.exists(origFullPath):        
        logVerbose("Replacing \"{:s}\" with original \"{:s}\"".format(currentVersionFullPath, origFullPath))
        if resolveReplaceClip(clip, origFullPath, filename+ext):
            logError("ReplaceClip() failed for \"{:s}\"".format(currentVersionFullPath))
            return True
        # delete previous version
        if fDeleteOlderVersionAfterCopyAndReplace:
            deleteMediaVersionFile(currentVersionFullPath)    

    return False

#
# Peforms refresh of media clips in running Davinci Resolve session
#
# Actions:
#
# RefreshAll                    - All clips in project
# RefreshCurrentBin             - Clips in current bin
# RefreshCurrentBinRecursive    - Clips in current bin and all sub-bins
# RefreshSelectedClips          - Selected clips
#
# Methods:
#
# Relink                        - Resolve 'Relink Clips'
# CopyAndReplace                - Copies file to new version, does Resolve 'Replace Clip'
# ReplaceWithOriginal           - does Resolve 'Replace Clip' with original file
#
def refreshMedia(action, method):

    logVerbose("refreshMedia(action={:s}, method={:s})".format(action, method))

    timeStart = time.time()

    #
    # get resolve objects
    #
    projectManager = resolve.GetProjectManager()
    project = projectManager.GetCurrentProject()
    mediaPool = project.GetMediaPool()

    #
    # We induce a refresh via the MediaPool.RelinkClips() method.
    # RelinkClips() accepts a list of lips but only one directory,
    # so all the clips for a given invocation must be in the same
    # directory. Calling RelinkClips() for each individual clip is slow,
    # so as an optimization we generate a separate list for each set of
    # clips that share the same directory, organized in a dictionary
    # with the directory for each list as the key
    #
    dictFolderList = dict()
    actionLowercase = action.lower()
    methodLowercase = method.lower()
    if actionLowercase == 'refreshall':
        logInfo("Processing all clips in project...")
        addFolderClipsToFolderDict(dictFolderList, mediaPool.GetRootFolder())
    elif actionLowercase == 'refreshcurrentbin' or actionLowercase == 'refreshcurrentbinrecursive':
        binFolder = mediaPool.GetCurrentFolder()
        if binFolder:
            if actionLowercase == 'refreshcurrentbin':
                logInfo("Processing clips in bin \"{:s}\"...".format(binFolder.GetName()))
                addClipsToFolderDict(dictFolderList, binFolder.GetClipList())
            else:
                logInfo("Processing clips in bin tree rooted at \"{:s}\"...".format(binFolder.GetName()))
                addFolderClipsToFolderDict(dictFolderList, binFolder)
    elif actionLowercase == 'refreshselectedclips':
        logInfo("Processing selected clips...")
        clips = mediaPool.GetSelectedClips()
        addClipsToFolderDict(dictFolderList, clips)  
    else:
        logError("Unknown action \"{:s}\"".format(action))
        return True
        
    countClipsProcessed = 0
    countClipsSuccessfullyProcessed = 0
    if methodLowercase == 'relink':          
        #
        # Relink clips for each unique directory found
        #
        for folder, listClips in dictFolderList.items():
            # process next list of clips
            countClipsProcessed += len(listClips)
            if isLoggingVerbose():                        
                filesInList = ', '.join(clip.GetClipProperty('Clip Name') for clip in listClips)
                logVerbose("Relinking \"{:s}\" in folder \"{:s}\"".format(filesInList, folder))
            if mediaPool.RelinkClips(listClips, folder):
                countClipsSuccessfullyProcessed += 1
            
    elif methodLowercase == 'copyandreplace':
    
        for folder, listClips in dictFolderList.items():
            # process next list of clips
            countClipsProcessed += len(listClips)
            for clip in listClips:
                if not replaceClipWithCopy(clip):
                    countClipsSuccessfullyProcessed += 1

    elif methodLowercase == 'replacewithoriginal':

        for folder, listClips in dictFolderList.items():
            # process next list of clips
            countClipsProcessed += len(listClips)
            for clip in listClips:
                if not replaceClipWithOriginal(clip):
                    countClipsSuccessfullyProcessed += 1


    else:
        logError("Unknown refresh method \"{:s}\"".format(method))
        return True

    timeElapsed = time.time() - timeStart
    logInfo("Succesfully processed {:d} of {:d} clips [{:d} unique directories] in {:.2f} seconds".format(\
        countClipsSuccessfullyProcessed, countClipsProcessed,
        len(dictFolderList), timeElapsed))

    return False


#
# script logic entry point when running as a stand-alone script outside of Resolve
#
if __name__ == "__main__":
    action = defaultAction
    method = defaultMethod
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if len(sys.argv) > 2:
            method = sys.argv[2]
    result = refreshMedia(action, method)
    sys.exit(result)
