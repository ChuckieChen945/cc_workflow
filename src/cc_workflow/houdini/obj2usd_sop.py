# === SOP 网络部分 ===
from pathlib import Path

import hou

# 根目录：.hip 所在路径/../obj
hip_dir = Path(hou.hipFile.path()).parent.parent
root_folder = (hip_dir / "obj").resolve()

geo = hou.pwd().geometry()

# 清空已有子节点
parent = hou.pwd().parent()
for child in parent.children():
    if child.name().startswith("obj_"):
        child.destroy()

# 遍历 obj 文件
obj_files = list(root_folder.rglob("*.obj"))

for path in obj_files:
    # 在 Houdini 中用相对路径表示层级
    rel_path = path.relative_to(root_folder)
    # 替换路径分隔符为下划线创建节点名
    name = "obj_" + "_".join(rel_path.with_suffix("").parts)

    node = parent.createNode("file", name)
    node.parm("file").set(str(path))

    out_null = parent.createNode(
        "null",
        "out_" + "_".join(rel_path.with_suffix("").parts),
    )
    out_null.setInput(0, node)
    out_null.moveToGoodPosition()


# === LOP 网络部分 ===
