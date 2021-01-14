# STRM-file auto-marker (service.strmfilemarker)

## What it does
This is a Kodi service addon to track the playback of *.strm files and automatically mark the associated library items as watched.

Becaus Kodi treats *.strm files as playlists internally, the integrated automatic setting of the watched state does not work for library items, that are based on *.strm files.
Such items are generally created by addons such as Netflix, when items are exported into the Kodi library. For those addons, that do not handle setting the watched state on their own, this addon can provide a more general solution.

## Restrictions / Known issues
The addon subscribes to `Player.OnPlay` and `Player.OnStop` notifications of the `xbmc.Monitor`. It is dependent on the info about the currently playing item which is provided alongside these notifications, especially the title.
There is currently no simple way in Kodi to determine the real underlying file of a playing item. Therefore, the addon tries to lookup the library item by the title.
It does a reasonable job for movies, series are confirmed to work with the current inputstream.adaptive-based Netflix plugin.

If it doesn't work for you with any plugin, turn on debug logging, check what data is passed alongside the `Player.OnStart` notification and open an issue. I'll look into making the matching work, but can't promise all-around compatibility, especially since this is a hobby project. 