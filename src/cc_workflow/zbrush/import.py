"""Helpers to import OBJ files into ZBrush as SubTools.

This module provides a small, focused ZBrush importer used by the UI script.
It avoids heavy dependencies and only calls the `zbrush.commands` helpers.
"""

from __future__ import annotations

from pathlib import Path

from zbrush import commands as zbc


def on_button_pressed(sender: str) -> None:
    pass


class ZBrushImporter:
    """Importer for OBJ files into ZBrush SubTools.

    Behavior (concise):
    - Optionally import a placeholder OBJ at init and keep its subtool id.
    - Import single OBJ via Tool:Import.
    - Duplicate a subtool by locating, selecting and pressing Duplicate.
    - Create a named SubTool folder by setting a temporary UI button and
      pressing the paired ZScript button.
    """

    NEW_FOLDER_NAME_STORE_BUTTON = "ZPlugin:MyTools:New Folder Name"
    RENAMESETNEXT_BUTTON = "ZPlugin:MyTools:RenameSetNext"

    def __init__(
        self,
        placeholder_obj: Path = Path(
            r"D:\chezmoi\scoop\persist\zbrush-np\placeholder.obj",
        ),
    ) -> None:
        """Initialize importer.

        Args:
            placeholder_obj: path to an OBJ used as a placeholder when
                creating new subtool folders.

        """
        self.placeholder_obj = placeholder_obj
        self.placeholder_subtool_id = self._import_obj(placeholder_obj)

    def _import_obj(self, path: Path) -> int:
        """Import an OBJ and return the imported subtool id (or -1)."""
        zbc.set_next_filename(str(path))
        zbc.press("Tool:Import")
        try:
            return int(zbc.get_subtool_id())
        except (AttributeError, TypeError, ValueError):
            return -1

    def rename_subtool(self, subtool_id: int, new_name: str) -> None:
        """Rename a subtool identified by its id to `new_name`."""
        index = zbc.locate_subtool(subtool_id)
        zbc.select_subtool(index)

        # Provide the new name via a temporary UI button and trigger ZScript.
        # The C-extension implementation of `add_button` may not accept keyword
        # arguments; call it with positional arguments to avoid a TypeError.
        zbc.add_button(self.NEW_FOLDER_NAME_STORE_BUTTON, new_name, on_button_pressed)
        zbc.press(self.RENAMESETNEXT_BUTTON)
        zbc.press("Tool:SubTool:Rename")
        zbc.delete_interface_item(self.NEW_FOLDER_NAME_STORE_BUTTON)

    def _duplicate_subtool(self, subtool_id: int) -> int:
        """Locate a subtool by id, select it and duplicate it. Returns new id."""
        index = zbc.locate_subtool(subtool_id)

        zbc.select_subtool(index)
        zbc.press("Tool:SubTool:Duplicate")
        try:
            return int(zbc.get_subtool_id())
        except (AttributeError, TypeError, ValueError):
            return -1

    def _create_folder(self, name: str) -> None:
        """Create a new subtool folder named `name`.

        If use_placeholder and a placeholder subtool exists, duplicate it first
        so the new folder contains a mesh to start with.
        """
        index = zbc.locate_subtool(self.placeholder_subtool_id)

        zbc.select_subtool(index)

        # Provide the folder name via a temporary UI button and trigger ZScript.
        # The C-extension implementation of `add_button` may not accept keyword
        # arguments; call it with positional arguments to avoid a TypeError.
        zbc.add_button(self.NEW_FOLDER_NAME_STORE_BUTTON, name, on_button_pressed)
        zbc.press(self.RENAMESETNEXT_BUTTON)
        zbc.press("Tool:SubTool:New Folder")
        zbc.delete_interface_item(self.NEW_FOLDER_NAME_STORE_BUTTON)

    # Public API
    def import_single(self, path: Path) -> int:
        """Import a single OBJ, duplicating placeholder beforehand."""
        self._duplicate_subtool(self.placeholder_subtool_id)
        return self._import_obj(path)

    def import_single_and_rename(self, path: Path) -> int:
        """Import a single OBJ, duplicating placeholder beforehand, and rename it."""
        new_subtool_id = self.import_single(path)
        # 从path中减去self.current_folder部分
        relative_path = str(path.relative_to(self.current_folder))
        new_name = relative_path.removeprefix(".\\\\").replace("\\\\", "\\").replace("\\", "%5C")
        self.rename_subtool(new_subtool_id, new_name)
        return new_subtool_id

    def import_objs(self, folder: Path) -> None:
        """Import all OBJ files in `folder` and create named subfolders for subfolders.

        Root .obj files are imported into the current tool. For each subfolder a new
        SubTool folder is created (optionally using the placeholder) and its .obj
        files are imported into it.
        """
        zbc.set_notebar_text(f"Processing folder: {folder}")
        self.obj_counts = 0

        root_objs = sorted(folder.glob("*.obj"))
        if root_objs:
            # bind the list to avoid late-binding in the lambda
            self.obj_counts += len(root_objs)
            zbc.freeze(lambda objs=root_objs: [self.import_single(p) for p in objs])

        for sub in sorted(folder.iterdir(), key=lambda p: p.name):
            print("Processing subfolder:", sub)
            if not sub.is_dir():
                continue
            self.current_folder = sub
            zbc.set_notebar_text(f"Processing subfolder: {sub.name}")
            self._create_folder(sub.name)
            sub_objs = sorted(sub.rglob("*.obj"))
            if sub_objs:
                self.obj_counts += len(sub_objs)
                zbc.freeze(
                    lambda objs=sub_objs: [self.import_single_and_rename(p) for p in objs],
                )

        self.move_placeholder_to_top()

    def move_placeholder_to_top(self) -> None:
        """_summary_."""
        index = zbc.locate_subtool(self.placeholder_subtool_id)
        # print("Moving placeholder subtool to top, starting at index:", index)
        for _ in range(self.obj_counts):
            # print("Curent index:", index)
            index = zbc.locate_subtool(self.placeholder_subtool_id)
            zbc.select_subtool(index)
            zbc.press("Tool:SubTool:Move Up")

    def delete_subtool(self, subtool_id: int) -> None:
        """Delete a subtool by its id."""
        index = zbc.locate_subtool(subtool_id)
        zbc.select_subtool(index)
        zbc.press("Tool:SubTool:Delete")

    def start_import(self) -> None:
        """Trigger handler (wired to UI button)."""
        selected = zbc.ask_string(
            initial_string="D:\\0_workspace\\0_cg_bridge",
            title="input path to import",
        )
        if not selected:
            return
        folder = Path(selected)
        if not folder.exists():
            zbc.message_ok(f"Folder does not exist: {folder}")
            return
        self.import_objs(folder)
        zbc.message_ok("OBJ import complete!")


if __name__ == "__main__":
    importer = ZBrushImporter()
    importer.start_import()
