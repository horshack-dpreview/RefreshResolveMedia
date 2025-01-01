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

defaultAction = 'RefreshSelectedClips'

#
# imports
#
import os
import sys
import time

if 'app' in globals():
    fRunningInsideResolve = True
    resolve = app.GetResolve()
else:
    # running as stand-alone script. This requires the Studio version
    fRunningInsideResolve = False
    if sys.platform == 'win32':
        sys.path.append(r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules")
    elif sys.platform == 'darwin':
        sys.path.append('/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules')
    import DaVinciResolveScript as dvr
    resolve = dvr.scriptapp("Resolve")


#
# Adds each clip in 'clips' the list of clips sharing the same
# directory, creating new lists for any clips with a directory
# that hasn't been encountered yet
#
def addClipsToFolderDict(dictFolderList, clips):
    if clips:
        for clip in clips:
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
# Peforms refresh of media clips in running Davinci Resolve session
#
# Actions:
#
# RefreshAll                    - All clips in project
# RefreshCurrentBin             - Clips in current bin
# RefreshCurrentBinRecursive    - Clips in current bin and all sub-bins
# RefreshSelectedClips          - Selected clips
#
def refreshMedia(action):

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
    if actionLowercase == 'refreshall':
        print("Processing all clips in project...")
        addFolderClipsToFolderDict(dictFolderList, mediaPool.GetRootFolder())
    elif actionLowercase == 'refreshcurrentbin' or actionLowercase == 'refreshcurrentbinrecursive':
        binFolder = mediaPool.GetCurrentFolder()
        if binFolder:
            if actionLowercase == 'refreshcurrentbin':
                print("Processing clips in bin \"{:s}\"...".format(binFolder.GetName()))
                addClipsToFolderDict(dictFolderList, binFolder.GetClipList())
            else:
                print("Processing clips in bin tree rooted at \"{:s}\"...".format(binFolder.GetName()))
                addFolderClipsToFolderDict(dictFolderList, binFolder)
    elif actionLowercase == 'refreshselectedclips':
        print("Processing selected clips...")
        clips = mediaPool.GetSelectedClips()
        addClipsToFolderDict(dictFolderList, clips)  
    else:
        print("Unknown action \"{:s}\"".format(action))
        return True
        
    #
    # Relink clips for each unique directory found
    #
    countClipsProcessed = 0
    for folder, listClips in dictFolderList.items():
        # process next list of clips
        countClipsProcessed += len(listClips)
        mediaPool.RelinkClips(listClips, folder)

    timeElapsed = time.time() - timeStart
    print("Processed {:d} clips in {:d} unique directories in {:.2f} seconds".format(\
        countClipsProcessed, len(dictFolderList), timeElapsed))
    
    return False

#
# script logic entry point when running as a stand-alone script outside of Resolve
#
if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
    else:
        action = defaultAction
    result = refreshMedia(action)
    sys.exit(result)
