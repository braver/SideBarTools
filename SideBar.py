# coding=utf8
import sublime, sublime_plugin

import os
import threading
import time

from .SideBarAPI import SideBarItem, SideBarSelection, SideBarProject

global s, Cache
s = {}
Cache = {}

def CACHED_SELECTION(paths = []):
	if Cache.cached:
		return Cache.cached
	else:
		return SideBarSelection(paths)

def Window(window = None):
	return window if window else sublime.active_window()

def window_set_status(key, name =''):
	for window in sublime.windows():
		for view in window.views():
			view.set_status('SideBar-'+key, name)

class Cache():
	pass
Cache = Cache()
Cache.cached = False

class SideBarCopyNameCommand(sublime_plugin.WindowCommand):
	def run(self, paths = []):
		items = []
		for item in SideBarSelection(paths).getSelectedItems():
			items.append(item.name())

		if len(items) > 0:
			sublime.set_clipboard("\n".join(items));
			if len(items) > 1 :
				sublime.status_message("Items copied")
			else :
				sublime.status_message("Item copied")

	def is_enabled(self, paths = []):
		return CACHED_SELECTION(paths).len() > 0

	def is_visible(self, paths =[]):
		return not s.get('disabled_menuitem_copy_name', False)

class SideBarCopyPathCommand(sublime_plugin.WindowCommand):
	def run(self, paths = []):
		items = []
		for item in SideBarSelection(paths).getSelectedItems():
			items.append(item.path())

		if len(items) > 0:
			sublime.set_clipboard("\n".join(items));
			if len(items) > 1 :
				sublime.status_message("Items copied")
			else :
				sublime.status_message("Item copied")

	def is_enabled(self, paths = []):
		return CACHED_SELECTION(paths).len() > 0

class SideBarCopyDirPathCommand(sublime_plugin.WindowCommand):
	def run(self, paths = []):
		items = []
		for item in SideBarSelection(paths).getSelectedDirectoriesOrDirnames():
			items.append(item.path())

		if len(items) > 0:
			sublime.set_clipboard("\n".join(items));
			if len(items) > 1 :
				sublime.status_message("Items copied")
			else :
				sublime.status_message("Item copied")

	def is_enabled(self, paths = []):
		return CACHED_SELECTION(paths).len() > 0

	def is_visible(self, paths =[]):
		return not s.get('disabled_menuitem_copy_dir_path', False)

class SideBarCopyPathRelativeFromProjectCommand(sublime_plugin.WindowCommand):
	def run(self, paths = []):
		items = []
		for item in SideBarSelection(paths).getSelectedItems():
			items.append(item.pathRelativeFromProject())

		if len(items) > 0:
			sublime.set_clipboard("\n".join(items));
			if len(items) > 1 :
				sublime.status_message("Items copied")
			else :
				sublime.status_message("Item copied")

	def is_enabled(self, paths = []):
		return CACHED_SELECTION(paths).len() > 0 and CACHED_SELECTION(paths).hasItemsUnderProject()

class SideBarCopyPathAbsoluteFromProjectCommand(sublime_plugin.WindowCommand):
	def run(self, paths = []):
		items = []
		for item in SideBarSelection(paths).getSelectedItems():
			items.append(item.pathAbsoluteFromProject())

		if len(items) > 0:
			sublime.set_clipboard("\n".join(items));
			if len(items) > 1 :
				sublime.status_message("Items copied")
			else :
				sublime.status_message("Item copied")

	def is_enabled(self, paths = []):
		return CACHED_SELECTION(paths).len() > 0 and CACHED_SELECTION(paths).hasItemsUnderProject()

class SideBarDuplicateCommand(sublime_plugin.WindowCommand):
	def run(self, paths = [], new = False):
		import functools
		Window().run_command('hide_panel');
		view = Window().show_input_panel("Duplicate As:", new or SideBarSelection(paths).getSelectedItems()[0].path(), functools.partial(self.on_done, SideBarSelection(paths).getSelectedItems()[0].path()), None, None)
		view.sel().clear()
		view.sel().add(sublime.Region(view.size()-len(SideBarSelection(paths).getSelectedItems()[0].name()), view.size()-len(SideBarSelection(paths).getSelectedItems()[0].extension())))

	def on_done(self, old, new):
		key = 'duplicate-'+str(time.time())
		SideBarDuplicateThread(old, new, key).start()

	def is_enabled(self, paths = []):
		return CACHED_SELECTION(paths).len() == 1 and CACHED_SELECTION(paths).hasProjectDirectories() == False

class SideBarDuplicateThread(threading.Thread):
	def __init__(self, old, new, key):
		self.old = old
		self.new = new
		self.key = key
		threading.Thread.__init__(self)

	def run(self):
		old = self.old
		new = self.new
		key = self.key
		window_set_status(key, 'Duplicating…')

		item = SideBarItem(old, os.path.isdir(old))
		try:
			if not item.copy(new):
				window_set_status(key, '')
				if SideBarItem(new, os.path.isdir(new)).overwrite():
					self.run()
				else:
					SideBarDuplicateCommand(Window()).run([old], new)
				return
		except:
			window_set_status(key, '')
			sublime.error_message("Unable to copy:\n\n"+old+"\n\nto\n\n"+new)
			SideBarDuplicateCommand(Window()).run([old], new)
			return
		item = SideBarItem(new, os.path.isdir(new))
		if item.isFile():
			item.edit();
		SideBarProject().refresh();
		window_set_status(key, '')
