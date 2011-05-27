showsorter
=========
A Python script to intelligently sort television shows into folders based on filename.

Usage
-----
* Flags:
 *  -m, --move: force moving of normal files (extracted files are always moved)
 *  -d, --dry: dry run - only display what would be moved/copied
* Source options:
 *  /path/to/folder
 *  rtorrent://localhost/scgi_path

Process
-----
* Parse all [target folders] for subfolders, and parse any .auto files inside (more on .auto files later)
* Extract a series name, season number, and episode number from the each file/folder in [source].
* Match each series name exactly with a folder in one of the target folders, or skip that series for the entire run.
* If the source path is a folder, check inside for archives to extract (currently only rar via 'unrar' works) and extract them, then check for video files to move (currently only a single resulting .avi or .mkv works) and set the copy flag to false for this file (because we extracted it ourselves, we assume moving instead of copying won't disrupt anything)
* Copy (or move, if we extracted an archive) the video file we have decided to sort to [target folder]/[series]/Season [season]/[series] S[season]E[season].[ext]

.auto files
-----
If a text file '.auto' exists in a series folder, it can override the series name match via regex and the resulting match. The regex is treated as case-insensitive.

Example:

    regex: (dr\.?|doctor) who
    name: Season %(season)i/Dr. Who %(epstr)s

Available format options:

* %(season)i - replaced with the season number
* %(episode)i - replaced with the episode number
* %(name)s - replaced with the series name
* %(epstr)s - replaced with the season+episode format: e.g. S01E01
* %(season)02d - season number, left-padded to two digits with zeros
* %(episode)02d - episode number, same as above

Default naming scheme:

* Season %(season)s/%(name)s %(epstr)s
Result: Season 1/Name S01E01

Example alternate naming scheme:

* Season %(season)i/%(name)s %(season)ix%(episode)02d
Result: Season 1/Name 1x01
