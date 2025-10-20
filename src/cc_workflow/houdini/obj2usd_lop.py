from pathlib import Path

import hou

hip_dir = Path(hou.hipFile.path()).parent.parent
root_folder = (hip_dir / "obj").resolve()
lopnet = hou.pwd().parent()

# 删除旧节点
for child in lopnet.children():
    if child.name().startswith("imp_"):
        child.destroy()


def find_sop_out_nodes(node):
    """递归查找所有名字以 'out_' 开头的 SOP null 节点"""
    out_nodes = []
    for child in node.children():
        if child.type().name() == "null" and child.name().startswith("out_"):
            out_nodes.append(child)
        out_nodes.extend(find_sop_out_nodes(child))
    return out_nodes


# 找到 SOP 输出节点
sop_out_nodes = find_sop_out_nodes(hou.node("/obj"))

for sop_null in sop_out_nodes:
    # 从 null 节点名字还原层级
    rel_name_parts = sop_null.name()[4:].split("_")  # 去掉 "out_"
    primpath = "/World/" + "/".join(rel_name_parts)

    # 创建 SOP Import LOP
    imp = lopnet.createNode("sopimport", "imp_" + "_".join(rel_name_parts))
    # TODO: 勾选 “Load as reference”
    imp.parm("soppath").set(sop_null.path())
    imp.parm("primpath").set(primpath)

    # 设置 layer save path
    layer_path = (hip_dir / "outputs" / ("/".join(rel_name_parts) + ".usd")).as_posix()
    # imp.parm("filepath").set(layer_path)

    # 创建材质节点
    mat = lopnet.createNode("materiallibrary", "mat_" + "_".join(rel_name_parts))
    mat.setNextInput(imp)


# 可选：创建 merge (sublayer LOP)
merge = lopnet.createNode("sublayer", "merge_all")
for n in lopnet.children():
    if n.name().startswith("imp_"):
        merge.setNextInput(n)
merge.moveToGoodPosition()
