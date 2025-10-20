from pathlib import Path

import maya.OpenMaya as om
from maya import cmds


def clean_filename(name: str) -> str:
    """清理 Maya 节点名为合法文件名。"""
    illegal = set(r'<>:"/\|?*')
    if any(c in illegal for c in name):
        msg = f'Node name "{name}" contains illegal characters.'
        om.MGlobal.displayError(msg)
        raise ValueError(msg)
    return name.strip(" :|").replace(":", "_").replace("|", "_")


def ensure_dir(path: str) -> bool:
    """验证或创建目录。"""
    if not path:
        return False
    dir_path = Path(path).resolve()
    try:
        dir_path.mkdir(parents=True, exist_ok=True, mode=0o777)
        return True
    except Exception:
        om.MGlobal.displayError(f"Failed to create directory {dir_path}")
        return False


class SimpleObjExporter:
    def __init__(self) -> None:
        scene_file = cmds.file(q=True, sn=True)
        if not scene_file:
            om.MGlobal.displayError("Please save the scene before exporting.")
            raise RuntimeError("Scene not saved.")

        scene_dir = Path(scene_file).parent
        obj_dir = (scene_dir / ".." / "obj").resolve()

        self.params = {
            "batch_export_path": str(obj_dir),
            "batch_import_path": str(obj_dir),
            "groups": True,
            "ptgroups": True,
            "materials": False,
            "smoothing": True,
            "normals": True,
        }

    def export_pressed(self) -> None:
        """导出所有场景中的 mesh。"""
        meshes = [
            obj
            for obj in cmds.ls(type="transform")
            if any(
                cmds.nodeType(s) == "mesh"
                for s in cmds.listRelatives(obj, s=True) or []
            )
        ]
        meshes = [cmds.ls(obj, long=True)[0] for obj in meshes]
        if not meshes:
            om.MGlobal.displayWarning("No mesh objects found to export.")
            return
        self.export_batch(meshes)

    def export_batch(self, meshes: list[str]) -> None:
        """批量导出 mesh。"""
        batch_path = self.params["batch_export_path"]
        if not ensure_dir(batch_path):
            om.MGlobal.displayError(f"Invalid export path: {batch_path}")
            return

        success = sum(self.export_mesh(m) for m in meshes)
        total = len(meshes)
        msg = f"Exported {success}/{total} meshes successfully."
        (om.MGlobal.displayInfo if success == total else om.MGlobal.displayWarning)(msg)

    def export_mesh(self, mesh: str) -> bool:
        """导出单个 mesh。"""
        parts = [clean_filename(p) for p in mesh.split("|") if p]
        mesh_name = parts[-1]
        out_dir = Path(self.params["batch_export_path"]).joinpath(*parts[:-1])

        if not ensure_dir(out_dir):
            om.MGlobal.displayError(f"Failed to create export path for {mesh}")
            return False

        out_file = out_dir / f"{mesh_name}.obj"
        dupe = cmds.duplicate(mesh, name=f"{mesh}_export")[0]
        cmds.select(dupe, r=True)

        try:
            cmds.file(
                out_file,
                exportSelected=True,
                type="OBJexport",
                force=True,
                options=self.obj_options(),
            )
            om.MGlobal.displayInfo(f"Exported: {out_file}")
            return True
        except RuntimeError as e:
            om.MGlobal.displayError(f"Failed to export {mesh}: {e}")
            return False
        finally:
            cmds.delete(dupe)
            cmds.select(mesh, r=True)

    def obj_options(self) -> str:
        """构建 OBJ 导出选项字符串。"""
        return ";".join(
            f"{k}={'1' if v else '0'}"
            for k, v in self.params.items()
            if k in {"groups", "ptgroups", "materials", "smoothing", "normals"}
        )

    def import_pressed(self) -> None:
        """导入所有 OBJ 文件并重建层级结构。"""
        base = Path(self.params["batch_import_path"])
        if not ensure_dir(base):
            om.MGlobal.displayWarning("No valid import path set!")
            return

        for obj_file in base.rglob("*.obj"):
            hierarchy = str(obj_file.relative_to(base).parent).replace("/", "|")
            try:
                nodes = cmds.file(
                    str(obj_file),
                    i=True,
                    type="OBJ",
                    renameAll=True,
                    mergeNamespacesOnClash=True,
                    namespace=":",
                    options="mo=1",
                    returnNewNodes=True,
                    importTimeRange="keep",
                )
                if hierarchy:
                    cmds.group(nodes, name=obj_file.parent.name)
                om.MGlobal.displayInfo(f"Imported: {obj_file}")
            except RuntimeError as e:
                om.MGlobal.displayError(f'Unable to import "{obj_file}": {e}')

    def debug_print(self) -> None:
        """打印调试信息。"""
        print("\n--- SimpleObjExporter Settings ---")
        for k, v in self.params.items():
            print(f"{k}: {v}")
        print("---------------------------------\n")


if __name__ == "__main__":
    SimpleObjExporter().export_pressed()
