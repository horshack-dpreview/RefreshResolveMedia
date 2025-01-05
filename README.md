
# RefreshResolveMedia

Scrip workarounds to Davinci Resolve's failure to recognize the latest version of media files

Davinci Resolve has a long-standing issue where it fails to automatically detect changes to media files, causing the old/stale version of the media to be used. For example, if you generate an image or video outside of Resolve and add it to your project and then later update that media file, Resolve will continue to use the original version until you either restart Resolve or manually intervene using various multi-step UI interventions that aren't equipped to handle a large number of assets spread over multiple folders. 

This script solves this issue by automating various workarounds that force Resolve to recognize the latest version of media files.
 
## Installation

 1. Install the latest version of Python 3.x from [https://www.python.org/downloads/](https://www.python.org/downloads/)
 2. Download the scripts as a zip file via [this link](https://github.com/horshack-dpreview/RefreshResolveMedia/archive/refs/heads/main.zip) to this repository.
 3. Unzip the file to your Resolve script directory. For Windows it's `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\Utility`. On Mac it's `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility`. You may need to restart Resolve to recognize the copied script
 4.  Invoke the script using the Workspace -> Scripts menu

## Relinking
Non-automated method to relink clips - right-click on a clip in the media pool:
![enter image description here](https://raw.githubusercontent.com/horshack-dpreview/RefreshResolveMedia/refs/heads/main/doc/image_relink_menu.png)
The first workaround automated by these scripts is to relink to the same files. This is the simplest and fastest method. When performed manually, Resolve prompts you for the directory of the selected files you want to relink to, using the most recent directory you navigated to previously in a Resolve dialog rather than the actual directory of the files you selected. That's the first nuisance.  The second nuisance is all the selected files must be in that same directory, so if you need to refresh files across multiple directories then you have to perform multiple, separate relink operations. This script automates this by automatically relinking to whatever the current path is for each file, allowing clips across multiple directories to be relinked in a single operation.

This script provides multiple selection scopes for relinking, from most-specific to least:

|Scope| Menu |
|--|--|
|Relink selected clips|In the media pool, select the clips you want to refresh, then Workspace -> Scripts -> **Relink_SelectedClips**  |
|Relink all clips in bin| In the media pool, choose the bin you want to refresh, then Workspace -> Scripts -> **Relink_CurrentBin**  |
|Relink all clips in bin and sub-bins| In the media pool, choose the root bin you want to refresh, then Workspace -> Scripts -> **Relink_CurrentBinRecursive**  |
|Relink all clips in project| Workspace -> Scripts -> **Relink_All**  |

You can optionally monitor what clips the script acts upon by opening the script console via Workspace -> Console

## Copying (Renaming) and Replacing
Non-automated method to replace clips - right-click on a clip in the media pool:
![enter image description here](https://raw.githubusercontent.com/horshack-dpreview/RefreshResolveMedia/refs/heads/main/doc/image_replace_menu.png)
The second workaround automated by these scripts is to copy (duplicate) the media file associated with a clip and perform a Replace Clip operation. This addresses Resolve's stickiest of the stale media problem, where it'll continue to use the stale version of a clip until the path+filename to that clip has changed regardless of which other workaround you use until you restart Resolve to clear its RAM cache. Here's a sample scenario:

 1. You add a still-image named `image-1.tif` to your Resolve project
 2. You decide to make a change to that still image, which you do externally in a tool like Photoshop, saving the changes to the same image-1.tif filename
 3. Resolve fails to recognize the update media file, even after attempts to relink to the same file or a forced-refresh operation in the Media page
 4. You duplicate or rename `image-1.tif` to `image-1-rev2.tif`, then right-click on the clip in its media bin and perform a "Replace selected clip...", navigating to the `image-1-rev2.tif` file in the file dialog that Resolve presents you with. Resolve uses the refreshed version of the media.
 5. Repeat for each clip...
 6. Repeat each time you update the media associated with clips, using a new unique name each time because if you reuse any previous name then Resolve will use the stale version that was stored in that previous filename.

Here's this same scenario automated with this script, running one of the "CopyAndReplace" scripts provided here, which does the following on all the clips you have selected prior to running the script:

 1. Creates a copy of the media file associated with clip, saving it to the same directory as the existing media file. The name of the copy is `image-1--refresh--0001.tif`
 2. Performs a Replace Clip with the renamed copy

If you need to make additional changes to your media file, make those changes to the original file `image-1.tif` and run the "CopyAndReplace" script again, which will perform the following:

 1. Creates a new copy of the media file, using an incremented version number and saving to `image-1--refresh--0002.tif`
 2. Performs a Replace Clip with the renamed copy
 3. Deletes the previous created revision file `image-1--refresh--0001.tif`

You can repeat this as many times as is necessary each time you make a change to your media files that you need Resolve to recognize.
 
Like relinking, this script provides multiple selection scopes for relinking, from most-specific to least:

|Scope| Menu |
|--|--|
|Copy+Replace selected clips|In the media pool, select the clips you want to refresh, then Workspace -> Scripts -> **CopyReplace_SelectedClips**  |
|Copy+Replace all clips in bin| In the media pool, choose the bin you want to refresh, then Workspace -> Scripts -> **CopyReplace_CurrentBin**  |
|Copy+Replace all clips in bin and sub-bins| In the media pool, choose the root bin you want to refresh, then Workspace -> Scripts -> **CopyReplace_CurrentBinRecursive**  |
|Copy+Replace all clips in project| Workspace -> Scripts -> **CopyReplace_All**  |

Note that the script will sometimes be unable to delete the previous revision due to Resolve keeping the file open. When your project is done you can manually delete these old versions. The script will never delete your original media files - it will only attempt to delete the copies it creates.

You can optionally monitor what clips the script acts upon by opening the script console via Workspace -> Console

### Replacing back to original filenames
When you are done with your edits you can optionally use another script provided here to replace each clip back to the original name. For example, if the current version of the clip is named `image-1--refresh--0004.tif` and you run Workspace -> Scripts -> **ReplaceWithOriginal_SelectedClips**,  this script will perform a Replace Clip operation to `image-1.tif` and delete `image-1--refresh--0004.tif`. 
Warning: Make sure you restart Resolve prior to performing the Replace With Original scripts, otherwise you'll run into the same RAM stale media bug and Resolve will use an older version of your media instead of the latest. 
