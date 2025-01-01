
# RefreshResolveMedia

Scripts to force Davinci Resolve to reload the latest version of media files

Davinci Resolve has a long-standing issue where it fails to automatically detect changes to media files, causing the old/stale version of the media to be used. For example, if you generate an image or video outside of Resolve and add it to your project and then later update that media file, Resolve will continue to use the original version until you either restart Resolve or manually intervene using multi-step UI interventions that aren't equipped to handle a large number of assets spread over multiple folders. 

This script solves this issue by automating the refresh of media files at their existing folder locations, implemented using Resolve's Relinking functionality. 
 
## Installation

 1. Install the latest version of Python 3.x from [https://www.python.org/downloads/](https://www.python.org/downloads/)
 2. Download the scripts as a zip file via [this link](https://github.com/horshack-dpreview/RefreshResolveMedia/archive/refs/heads/main.zip) to this repository.
 3. Unzip the file to your Resolve script directory. For Windows it's `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\Utility`. On Mac it's `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility`. You may need to restart Resolve to recognize the copied script
 4.  Invoke the script using the Workspace -> Scripts menu

Here are the scripts provided:
|Action| How to Use |
|--|--|
|Refresh only selected clips  |Select the clips you want to refresh, then Workspace -> Scripts -> **RefreshSelectedClips**  |
|Refresh all clips in bin  | Choose the bin you want to refresh, then Workspace -> Scripts -> **RefreshCurrentBin**  |
|Refresh all clips in bin and sub-bins  | Choose the root bin you want to refresh, then Workspace -> Scripts -> **RefreshCurrentBinRecursive**  |
|Refresh all clips project  | Workspace -> Scripts -> **RefreshAll**  |
