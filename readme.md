# Sidebar Tools

<img src="https://raw.githubusercontent.com/braver/SideBarTools/master/screenshot.png" width="461">

Some useful tools to add to your sidebar context menu and command palette:

- Reveal In Sidebar
- Copy Filename
- Copy Relative Path
- Copy Absolute Path
- Duplicate

To open a file in its default application, consider installing the [Open in Default Application][2] package.

If you're looking for "Reveal in Finder/Explorer" for directories, [Open in Default Application][2] does that too.

If you're looking for a command to "Move" a file or folder, note that you can use the existing "Rename" command. It accepts paths relative from the file's current location, as well as absolute paths (e.g. `file.txt` -> `../file.txt`). 

This package offers fewer commands than [SidebarEnhancements][1], striking a balance somewhere between the bare minimum 
and going overboard. This has benefits:

- The default context menu isn't replaced, this package just adds some useful 
  new commands.
- It's tiny, light-weight and reliable.
- We won't [track][3] [you][5]. Ever.

---------

License: [GNU GPL][4]

[1]: https://packagecontrol.io/packages/SideBarEnhancements
[3]: https://github.com/SideBarEnhancements-org/SideBarEnhancements/blob/d1c7fa4bac6a1f31ba177bc41ddd0ca902e43609/Stats.py
[2]: https://packagecontrol.io/packages/Open%20in%20Default%20Application
[4]: http://www.gnu.org/licenses/gpl.html
[5]: https://forum.sublimetext.com/t/rfc-default-package-control-channel-and-package-telemetry/30157
