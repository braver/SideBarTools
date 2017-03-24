# coding=utf8
import sublime
import sublime_plugin
import os
import threading
import time
import shutil
import functools

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

	def run(self):
		self.view = self.window.active_view()
		self.source = self.view.file_name()
		base, leaf = os.path.split(self.source)
		name, ext = os.path.splitext(leaf)
		initial_text = name + ' (Copy)' + ext
		self.window.show_input_panel('Duplicate As:', 
			initial_text, self.on_done, None, None)

	def on_done(self, destination):
		base, _ = os.path.split(self.source)
		destination = os.path.join(base, destination)
		threading.Thread(target=self.copy, 
			args=(self.source, destination)).start()

	def copy(self, source, destination):
		print(source, destination)
		self.view.set_status('ZZZ', 'copying "{}" to "{}"'.format(
			source, destination))
		shutil.copy2(source, destination)
		self.view.erase_status('ZZZ')

class SideBarOpenCommand(sublime_plugin.WindowCommand):

	def run(self):
		path = self.window.active_view().file_name()
		print(path)
		self.window.run_command('open_url', args={'url': path})
