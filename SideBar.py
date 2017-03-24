# coding=utf8
import sublime, sublime_plugin

import os
import threading
import time

from .SideBarAPI import SideBarItem, SideBarSelection, SideBarProject

global s, Cache
s = {}
Cache = {}

def CACHED_SELECTION():
	if Cache.cached:
		return Cache.cached
	else:
		return SideBarSelection()

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

def copy_to_clipboard_and_inform(data):
	sublime.set_clipboard(data)
	sublime.status_message('copied "{}" to clipboard'.format(data))

class SideBarCopyNameCommand(sublime_plugin.WindowCommand):
	def run(self):
		name = os.path.split(self.window.active_view().file_name())[1]
		copy_to_clipboard_and_inform(name)

class SideBarCopyAbsolutePathCommand(sublime_plugin.WindowCommand):
	def run(self):
		path = self.window.active_view().file_name()
		copy_to_clipboard_and_inform(path)

class SideBarCopyRelativePathCommand(sublime_plugin.WindowCommand):
	def run(self):
		path = self.window.active_view().file_name()
		project_file_name = self.window.project_file_name()
		root_dir = ''
		if project_file_name:
			root_dir = os.path.dirname(project_file_name)
		else:
			root_dir = self.window.project_data()['folders'][0]['path']
		# I would like to use os.path.commonpath, but that is only available
		# since Python 3.5. We are on Python 3.3.
		common = os.path.commonprefix([root_dir, path])
		path = path[len(common):]
		if path.startswith('/') or path.startswith('\\'):
			path = path[1:]
		copy_to_clipboard_and_inform(path)

class SideBarCopyDirPathCommand(sublime_plugin.WindowCommand):
	def run(self):
		path = self.window.active_view().file_name()
		copy_to_clipboard_and_inform(os.path.dirname(path))

class SideBarDuplicateCommand(sublime_plugin.WindowCommand):
	def run(self, new = False):
		import functools
		Window().run_command('hide_panel');
		view = Window().show_input_panel("Duplicate As:", new or SideBarSelection().getSelectedItems()[0].path(), functools.partial(self.on_done, SideBarSelection().getSelectedItems()[0].path()), None, None)
		view.sel().clear()
		view.sel().add(sublime.Region(view.size()-len(SideBarSelection().getSelectedItems()[0].name()), view.size()-len(SideBarSelection().getSelectedItems()[0].extension())))

	def on_done(self, old, new):
		key = 'duplicate-'+str(time.time())
		SideBarDuplicateThread(old, new, key).start()

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
		SideBarProject().refresh();
		window_set_status(key, '')

class SideBarOpenCommand(sublime_plugin.WindowCommand):
	def run(self):
		for item in SideBarSelection().getSelectedItems():
			item.open()
