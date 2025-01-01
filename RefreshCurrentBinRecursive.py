#!/usr/bin/env python

#
#############################################################################
#
# RefreshCurrentBinRecursive.py
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
rrm.refreshMedia("RefreshCurrentBinRecursive")
