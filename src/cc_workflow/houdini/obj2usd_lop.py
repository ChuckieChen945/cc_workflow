from pathlib import Path

import hou

# 根目录：.hip 所在路径/../obj
hip_dir = Path(hou.hipFile.path()).parent.parent
root_folder = (hip_dir / "obj").resolve()


# 清空已有子节点
parent = hou.pwd().parent()
for child in parent.children():
    if child.name().startswith("import_"):
        child.destroy()

# 遍历 obj 文件
obj_folders = [f for f in root_folder.iterdir() if f.is_dir()]
obj_files = []
for folder in obj_folders:
    obj_files.extend(folder.glob("*.obj"))

for path in obj_files:
    # 在 Houdini 中用相对路径表示层级
    rel_path = path.relative_to(root_folder)
    # 替换路径分隔符为下划线创建节点名
    name = "import_" + "_".join(rel_path.with_suffix("").parts)

    node = parent.createNode("create_assets", name)
    node.parm("file_path").set(str(path))

    out_null = parent.createNode(
        "null",
        "out_" + "_".join(rel_path.with_suffix("").parts),
    )
    out_null.setInput(0, node)
    out_null.moveToGoodPosition()

parent.layoutChildren()
