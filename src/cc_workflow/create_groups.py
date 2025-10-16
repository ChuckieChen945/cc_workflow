import json
import maya.cmds as cmds

def create_group_hierarchy(node_dict, parent=None):
    """递归创建组层级并将说明文字添加为注释属性"""
    for key, value in node_dict.items():
        if isinstance(value, dict):
            # 创建组
            group_name = cmds.group(empty=True, name=key)
            if parent:
                cmds.parent(group_name, parent)

            # 如果有 notes 字段，添加为注释属性
            notes = value.get("notes", "")
            if notes:
                if not cmds.attributeQuery("notes", node=group_name, exists=True):
                    cmds.addAttr(group_name, ln="notes", dt="string")
                cmds.setAttr(group_name + ".notes", notes, type="string")

            # 递归创建子项
            children = value.get("children", {})
            if children:
                create_group_hierarchy(children, parent=group_name)

        elif isinstance(value, str):
            # 创建叶子节点组
            group_name = cmds.group(empty=True, name=key)
            if parent:
                cmds.parent(group_name, parent)
            # 添加文字描述
            if not cmds.attributeQuery("notes", node=group_name, exists=True):
                cmds.addAttr(group_name, ln="notes", dt="string")
            cmds.setAttr(group_name + ".notes", value, type="string")


def import_json_and_build():
    """弹出更大的输入窗口，让用户输入 JSON 并创建层级"""
    if cmds.window("jsonInputWin", exists=True):
        cmds.deleteUI("jsonInputWin")

    window = cmds.window("jsonInputWin", title="输入 JSON 数据", widthHeight=(600, 400), sizeable=True)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=8, columnAlign="center")
    cmds.text(label="请粘贴 JSON 数据：", align="center")
    json_field = cmds.scrollField(wordWrap=True, text="", height=300)

    cmds.rowLayout(numberOfColumns=2, adjustableColumn=1, columnAlign=(1, "center"))
    cmds.button(label="确定", width=120, command=lambda *args: on_confirm(json_field))
    cmds.button(label="取消", width=120, command=lambda *args: cmds.deleteUI(window))
    cmds.setParent("..")

    cmds.showWindow(window)


def on_confirm(json_field):
    """确认按钮回调：读取文本并创建组"""
    text = cmds.scrollField(json_field, query=True, text=True)
    cmds.deleteUI("jsonInputWin")

    try:
        data = json.loads(text)
    except Exception as e:
        cmds.warning("❌ JSON 解析失败，请检查格式。\n错误信息: {}".format(e))
        return

    create_group_hierarchy(data)
    cmds.inViewMessage(amg='✅ JSON 层级组已成功创建！', pos='topCenter', fade=True)


# 运行入口
import_json_and_build()
