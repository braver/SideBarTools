# Sidebar Tools

<img src="https://raw.githubusercontent.com/braver/SideBarTools/master/screenshot.png" width="502">

Some useful tools to add to your sidebar and tab context menu's:

- Copy Filename
- Copy Relative Path
- Copy Absolute Path
- Duplicate (ie. copy to a target path)
- Move
- Compare
- New file

All except Compare are also available via the command palette, in addition to:

- Reveal In Sidebar

To use the **Compare command**, configure a ["difftool"](https://github.com/braver/SideBarTools/blob/master/SideBarTools.sublime-settings#L8). For instance, [Xcode][4] comes with FileMerge that you can call via `opendiff`. The command will then become available when two files, or two folders are selected.

An additional **Edit command** is available, for ease of use on touch screens (thanks @PetrKryslUCSD). Enable it via the [settings](https://github.com/braver/SideBarTools/blob/master/SideBarTools.sublime-settings#L11). 

To open a file in its default application, consider installing the [Open in Default Application][2] package.

If you're looking for "Reveal in Finder/Explorer" for directories, [Open in Default Application][2] does that too.

## Goals of this package

This package offers fewer commands than e.g. [SidebarEnhancements][1], striking a balance somewhere between the bare minimum 
and going overboard. This has benefits:

- The default context menu isn't replaced, this package just adds some useful 
  new commands.
- It's tiny, light-weight and reliable.
- We won't [track][3] [you][5]. Ever.

## Settings

- `difftool`: configure what tool to use, and thereby enable the Compare command.
- `edit_command`: enable the Edit command.
- `tab_context`: optionally disable the context menu on file tabs.
- `posix_copy_command`: enable the command to copy relative paths in POSIX format, e.g. for use in WSL (Windows only).


## Credits

We used [SidebarEnhancements][1] as a starting point, but completely re-implemented everything we wanted to keep. Now it comes in at just over 200 lines of super clean Python with zero legacy. Special thanks go out to [@rwols][6] and [@mandx][7] to make this happen.


[1]: https://packagecontrol.io/packages/SideBarEnhancements
[2]: https://packagecontrol.io/packages/Open%20in%20Default%20Application
[3]: https://github.com/SideBarEnhancements-org/SideBarEnhancements/blob/d1c7fa4bac6a1f31ba177bc41ddd0ca902e43609/Stats.py
[4]: https://developer.apple.com/xcode/
[5]: https://forum.sublimetext.com/t/rfc-default-package-control-channel-and-package-telemetry/30157
[6]: https://github.com/braver/SideBarTools/pull/2
[7]: https://github.com/braver/SideBarTools/pulls?q=is%3Apr+author%3Amandx

## Buy me a coffee 

☕️👌🏻

Please feel free to make a little [donation via PayPal](https://paypal.me/koenlageveen) towards the coffee that keeps this labour of love running. It's much appreciated!
