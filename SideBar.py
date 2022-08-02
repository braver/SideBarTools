import sublime
import sublime_plugin
import subprocess
import os
import threading
import shutil
from functools import partial


def get_setting(window_command, setting):
    '''
    Sublime merges everything, including project settings, into view.settings
    Package specific settings can be set via namespaced dot-syntax everywhere
    '''
    defaults = sublime.load_settings("SideBarTools.sublime-settings")
    default_tool = defaults.get(setting)
    merged_settings = window_command.window.active_view().settings()

    return merged_settings.get('SideBarTools.' + setting, default_tool)


class SideBarCommand(sublime_plugin.WindowCommand):

    def copy_to_clipboard_and_inform(self, data):
        sublime.set_clipboard(data)
        lines = len(data.split('\n'))
        self.window.status_message('Copied {} to clipboard'.format(
            '{} lines'.format(lines) if lines > 1 else '"{}"'.format(data)
        ))

    def get_path(self, paths):
        try:
            return paths[0]
        except IndexError:
            return self.window.active_view().file_name()

    def is_visible(self, paths=[]):
        if paths:
            return len(paths) < 2
        return bool(self.window.active_view().file_name())

    @staticmethod
    def make_dirs_for(filename):
        destination_dir = os.path.dirname(filename)
        try:
            os.makedirs(destination_dir)
            return True
        except OSError:
            # TODO: It would be nice to surface this error to the user...
            return False


class SideBarCompareCommand(sublime_plugin.WindowCommand):

    def is_visible(self, paths):
        return len(paths) == 2 and get_setting(self, 'difftool')

    def is_enabled(self, paths):
        if len(paths) < 2 or not get_setting(self, 'difftool'):
            return False
        return os.path.isdir(paths[0]) == os.path.isdir(paths[1])

    def run(self, paths):
        tool = get_setting(self, 'difftool')
        if tool:
            if isinstance(tool, str):
                tool = [tool]
            subprocess.Popen(tool + paths[:2])
        else:
            self.window.status_message("No diff tool configured")


class MultipleFilesMixin(object):

    def get_paths(self, paths):
        return paths or [self.get_path(paths)]

    def is_visible(self, paths=[]):
        return bool(paths or self.window.active_view().file_name())


class SideBarCopyNameCommand(MultipleFilesMixin, SideBarCommand):

    def run(self, paths):
        names = (os.path.split(path)[1] for path in self.get_paths(paths))
        self.copy_to_clipboard_and_inform('\n'.join(names))

    def description(self):
        return 'Copy Filename'


class SideBarCopyAbsolutePathCommand(MultipleFilesMixin, SideBarCommand):

    def run(self, paths):
        paths = self.get_paths(paths)
        self.copy_to_clipboard_and_inform('\n'.join(paths))

    def description(self):
        return 'Copy Absolute Path'


class SideBarCopyRelativePathCommand(MultipleFilesMixin, SideBarCommand):

    def run(self, paths):
        paths = self.get_paths(paths)
        root_paths = self.window.folders()
        relative_paths = []

        for path in paths:
            if not root_paths:  # e.g. single file and using command palette
                relative_paths.append(os.path.basename(path))
            else:
                for root in root_paths:
                    if path.startswith(root):
                        p = os.path.relpath(path, root)
                        relative_paths.append(p)
                        break

        if not relative_paths:
            relative_paths.append(os.path.basename(path))

        self.copy_to_clipboard_and_inform('\n'.join(relative_paths))

    def description(self):
        return 'Copy Relative Path'


class SideBarDuplicateCommand(SideBarCommand):

    def run(self, paths):
        source = self.get_path(paths)
        base, leaf = os.path.split(source)

        name, ext = os.path.splitext(leaf)
        if ext != '':
            while '.' in name:
                name, _ext = os.path.splitext(name)
                ext = _ext + ext
                if _ext == '':
                    break

        source = self.get_path(paths)

        input_panel = self.window.show_input_panel(
            'Duplicate As:', source, partial(self.on_done, source), None, None)

        input_panel.sel().clear()
        input_panel.sel().add(
            sublime.Region(len(base) + 1, len(source) - len(ext))
        )

    def on_done(self, source, destination):
        base, _ = os.path.split(source)
        destination = os.path.join(base, destination)
        threading.Thread(
            target=self.copy,
            args=(source, destination)
        ).start()

    def copy(self, source, destination):
        self.window.status_message(
            'Copying "{}" to "{}"'.format(source, destination)
        )

        self.make_dirs_for(destination)
        try:
            if os.path.isdir(source):
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
                self.window.open_file(destination)
        except OSError as error:
            self.window.status_message(
                'Error copying: {error} ("{src}" to "{dst}")'.format(
                    src=source,
                    dst=destination,
                    error=error,
                )
            )

    def description(self):
        return 'Duplicate File…'


class SideBarMoveCommand(SideBarCommand):

    def run(self, paths):
        source = self.get_path(paths)

        input_panel = self.window.show_input_panel(
            'Move to:', source, partial(self.on_done, source), None, None)

        base, leaf = os.path.split(source)
        ext = os.path.splitext(leaf)[1]

        input_panel.sel().clear()
        input_panel.sel().add(
            sublime.Region(len(base) + 1, len(source) - len(ext))
        )

    def on_done(self, source, destination):
        threading.Thread(
            target=self.move,
            args=(source, destination)
        ).start()

    @staticmethod
    def retarget_all_views(source, destination):
        if source[-1] != os.path.sep:
            source += os.path.sep

        if destination[-1] != os.path.sep:
            destination += os.path.sep

        for window in sublime.windows():
            for view in window.views():
                filename = view.file_name()
                if not filename:
                    continue
                if os.path.commonprefix([source, filename]) == source:
                    view.retarget(
                        os.path.join(destination, filename[len(source):])
                    )

    @staticmethod
    def retarget_view(source, destination):
        source = os.path.normcase(os.path.abspath(source))
        destination = os.path.normcase(os.path.abspath(destination))
        for window in sublime.windows():
            for view in window.views():
                filename = view.file_name()
                if not filename:
                    continue
                path = os.path.abspath(filename)
                if os.path.normcase(path) == source:
                    view.retarget(destination)

    def move(self, source, destination):
        self.window.status_message(
            'Moving "{}" to "{}"'.format(source, destination)
        )

        self.make_dirs_for(destination)

        isfile = os.path.isfile(source)

        try:
            shutil.move(source, destination)
            if isfile:
                self.retarget_view(source, destination)
            else:
                self.retarget_all_views(source, destination)
        except OSError as error:
            self.window.status_message(
                'Error moving: {error} ("{src}" to "{dst}")'.format(
                    src=source,
                    dst=destination,
                    error=error,
                )
            )
        self.window.run_command('refresh_folder_list')

    def description(self):
        return 'Move File…'


class RemoveFolderListener(sublime_plugin.EventListener):

    def on_post_window_command(self, window, command_name, args):
        if command_name == 'delete_folder':
            for folder in window.project_data()['folders']:
                if not os.path.exists(folder['path']):
                    window.run_command(
                        'remove_folder',
                        {
                            'dirs': [folder['path']]
                        })


class SideBarNewCommand(SideBarCommand):
    NEW_FILENAME = 'New file.txt'

    def run(self, paths):
        source = self.get_path(paths)
        select_extension = False

        if os.path.isdir(source):
            source = os.path.join(source, self.NEW_FILENAME)
            select_extension = True

        filepath, filename = os.path.split(source)
        fileext = os.path.splitext(filename)[1]

        input_panel = self.window.show_input_panel(
            'New path:', source, self.on_done, None, None)

        selection = input_panel.sel()
        selection.clear()
        selection.add(sublime.Region(
            len(filepath) + 1,
            len(filepath) + 1 + len(filename) - (0 if select_extension else len(fileext)),
        ))

    def on_done(self, path):
        if path.endswith(os.path.sep) or path.endswith('/') or path.endswith('\\'):
            threading.Thread(target=self.create_directory, args=(path,)).start()
        else:
            threading.Thread(target=self.create_file, args=(path,)).start()

    def create_directory(self, path):
        self.window.status_message('Creating directory "{path}"'.format(path=path))
        if not self.make_dirs_for(os.path.join(path, 'dummy.file')):
            sublime.message_dialog('Directory "{path}" could not be created'.format(path=path))
        else:
            self.window.status_message('Directory "{path}" created'.format(path=path))

    def create_file(self, path):
        self.window.status_message('Creating file "{path}"'.format(path=path))

        if os.path.exists(path):
            sublime.message_dialog(
                'Opening existing file "{path}"'.format(path=path)
            )
        else:
            self.make_dirs_for(path)
            try:
                with open(path, 'wb') as fileobj:
                    fileobj.write(b'')
            except OSError as error:
                self.window.status_message(
                    'Error creating "{path}": {error}'.format(path=path, error=error),
                )

        self.window.open_file(path)

    def description(self):
        return 'New…'
