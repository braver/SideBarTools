import sublime
import sublime_plugin
import os
import threading
import shutil
from functools import partial


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

    def is_visible(self, paths):
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
            return False


class MultipleFilesMixin(object):

    def get_paths(self, paths):
        return paths or [self.get_path(paths)]

    def is_visible(self, paths):
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
        project_file_name = self.window.project_file_name()
        root_dir = ''
        if project_file_name:
            root_dir = os.path.dirname(project_file_name)
        else:
            root_dir = self.window.project_data()['folders'][0]['path']

        paths = self.get_paths(paths)
        relative_paths = []

        for path in paths:
            common = os.path.commonprefix([root_dir, path])
            path = path[len(common):]
            if path.startswith('/') or path.startswith('\\'):
                path = path[1:]
            relative_paths.append(path)

        self.copy_to_clipboard_and_inform('\n'.join(relative_paths))

    def description(self):
        return 'Copy Relative Path'


class SideBarDuplicateCommand(SideBarCommand):

    def run(self, paths):
        source = self.get_path(paths)
        base, leaf = os.path.split(source)

        name, ext = os.path.splitext(leaf)
        if ext is not '':
            while '.' in name:
                name, _ext = os.path.splitext(name)
                ext = _ext + ext
                if _ext is '':
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
                path = os.path.abspath(view.file_name())
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
