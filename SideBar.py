import sublime
import sublime_plugin
import subprocess
import os
import threading
import shutil
from functools import partial
from pathlib import PurePath


def get_setting(window_command, setting):
    '''
    Sublime merges everything, including project settings, into view.settings
    Package specific settings can be set via namespaced dot-syntax everywhere
    '''
    defaults = sublime.load_settings("SideBarTools.sublime-settings")
    default_tool = defaults.get(setting)

    try:
        # some views, e.g. of images, don't have settings
        merged_settings = window_command.window.active_view().settings()
        return merged_settings.get('SideBarTools.' + setting, default_tool)
    except Exception:
        return None


class SideBarCommand(sublime_plugin.WindowCommand):

    def is_visible(self, paths=[], context='', style='', **kwargs):
        if context == 'tab' and not get_setting(self, 'tab_context'):
            return False

        paths = self.get_paths(paths, context, **kwargs)
        for path in paths:
            if path is None:
                return False

        return bool(paths)

    def get_paths(self, paths, context='', **kwargs):
        # paths is only filled on side bar context
        # for command palette and tab context we need to find the path
        return paths or [self.get_path(paths, context, **kwargs)]

    def get_path(self, paths=[], context="", group=-1, index=-1):
        try:
            return paths[0]
        except IndexError:
            return self.file_via_window(context, group, index)

    def file_via_window(self, context='', group=-1, index=-1):
        w = self.window
        if context == 'tab':
            try:
                vig = w.views_in_group(group)
                return vig[index].file_name()
            except IndexError:
                sig = w.sheets_in_group(group)
                return sig[index].file_name()
        return w.active_view().file_name()

    def copy_to_clipboard_and_inform(self, paths=[]):
        sublime.set_clipboard('\n'.join(paths))

        lines = len(paths)
        self.window.status_message('Copied {} to clipboard'.format(
            '{} lines'.format(lines) if lines > 1 else '"{}"'.format(paths[0])
        ))

    @staticmethod
    def make_dirs_for(filename):
        destination_dir = os.path.dirname(filename)
        try:
            os.makedirs(destination_dir)
            return True
        except OSError:
            # TODO: It would be nice to surface this error to the user...
            return False


class SideBarCopyNameCommand(SideBarCommand):

    def run(self, paths=[], **kwargs):
        names = [os.path.split(path)[1] for path in self.get_paths(paths, **kwargs)]
        self.copy_to_clipboard_and_inform(names)


class SideBarCopyAbsolutePathCommand(SideBarCommand):

    def is_visible(self, paths=[], context='', **kwargs):
        # in 4158 ST gets the "copy path" sidebar context entry for single files
        # we also want to keep our command palette and tab context entries
        if len(self.get_paths(paths, context, **kwargs)) <= 1:
            if context not in ['palette', 'tab']:
                if int(sublime.version()) >= 4158:
                    return False
        return super().is_visible(paths, context, **kwargs)

    def run(self, paths=[], **kwargs):
        paths = self.get_paths(paths, **kwargs)
        self.copy_to_clipboard_and_inform(paths)


class SideBarCopyRelativePathCommand(SideBarCommand):

    def is_visible(self, paths=[], style='', **kwargs):
        # posix style paths only on windows, and optional
        if style == 'posix':
            if sublime.platform() != 'windows':
                return False
            if not get_setting(self, 'posix_copy_command'):
                return False
        return super().is_visible(paths, **kwargs)

    def run(self, paths=[], style="", **kwargs):
        paths = self.get_paths(paths, **kwargs)
        root_paths = self.window.folders()
        relative_paths = []

        # find the correct relative paths
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

        if style != 'posix':
            self.copy_to_clipboard_and_inform(relative_paths)
            return

        # optional postprocess to posix paths
        posix_paths = []
        for path in relative_paths:
            posix_paths.append(PurePath(path).as_posix())
        self.copy_to_clipboard_and_inform(posix_paths)


class SideBarDeleteCommand(SideBarCommand):

    def is_visible(self, paths=[], context='', **kwargs):
        # can only delete files that exist on disk
        for path in self.get_paths(paths, context, **kwargs):
            if path is None:
                return False
            if not os.path.exists(path):
                return False
        return super().is_visible(paths, context, **kwargs)

    def run(self, paths=[], **kwargs):
        paths = self.get_paths(paths, **kwargs)
        self.window.run_command('delete_file', {'files': paths, 'prompt': True})


class SideBarDuplicateCommand(SideBarCommand):

    def run(self, paths, **kwargs):
        source = self.get_path(paths, **kwargs)
        base, leaf = os.path.split(source)

        name, ext = os.path.splitext(leaf)
        if ext != '':
            while '.' in name:
                name, _ext = os.path.splitext(name)
                ext = _ext + ext
                if _ext == '':
                    break

        source = self.get_path(paths, **kwargs)

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


class SideBarMoveCommand(SideBarCommand):

    def run(self, **kwargs):
        source = self.get_path(**kwargs)

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


class SideBarNewCommand(SideBarCommand):
    NEW_FILENAME = 'New file.txt'

    def run(self, **kwargs):
        source = self.get_path(**kwargs)
        select_extension = False

        if source is None or not os.path.exists(source):
            self.window.status_message('No path to create a new file from.')
            return

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


class SideBarEditCommand(SideBarCommand):

    def is_visible(self, **kwargs):
        if not get_setting(self, 'edit_command'):
            return False
        return super().is_visible(**kwargs)

    def run(self, **kwargs):
        source = self.get_path(**kwargs)
        self.window.open_file(source)


class SideBarCompareCommand(sublime_plugin.WindowCommand):

    def is_visible(self, paths):
        return len(paths) == 2 and bool(get_setting(self, 'difftool'))

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


class RemoveFolderListener(sublime_plugin.EventListener):

    def on_post_window_command(self, window, command_name, args):
        if command_name == 'delete_folder':
            for folder in window.project_data()['folders']:
                if not os.path.exists(os.path.expanduser(folder['path'])):
                    window.run_command(
                        'remove_folder',
                        {
                            'dirs': [folder['path']]
                        })
