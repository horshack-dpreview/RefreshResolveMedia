#!/usr/bin/env python

#
#############################################################################
#
# CopyReplace_SelectedClips.py
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

import WorkerRefreshResolveMedia as rrm

#
# creates and displays dialog indicating that we're processing the clips 
#
def createProcessingDialog(msg):
    ui = fusion.UIManager
    disp = bmd.UIDispatcher(ui)
    dlg = disp.AddWindow({ "WindowTitle": "Refresh Resolve Media [Script]", "ID": "MyWin", "Geometry": [ 800, 400, 400, 100 ],  },
        [
            ui.VGroup(
            [
                ui.Label({ "ID": "MyLabel", "Text": msg, "Alignment" : { "AlignHCenter": True, "AlignVCenter": True } }),
            ]), 
        ])
    dlg.Show()
    return dlg
    
#
# closes dialog previous created by createProcessingDialog()
#
def closeProcessingDialog(dlg):
    dlg.Hide()

dlg = createProcessingDialog("Copying+Replacing selected clips...")
rrm.refreshMedia("RefreshSelectedClips", "CopyAndReplace")
closeProcessingDialog(dlg)
