"""Maya Image Plane and Camera Setup Tool.

--------------------------------------

This script allows users to quickly create orthographic cameras and image planes
in Autodesk Maya for modeling reference setup. It automates the process of
positioning reference images (front, back, left, right, top, bottom, or extra
images) and aligning them with cameras for an efficient modeling workflow.

Main Features:
    - Creates six orthographic cameras (front, back, left, right, top, bottom).
    - Creates an additional render camera.
    - Imports user-selected images as image planes.
    - Aligns image planes automatically with cameras to avoid overlap.
    - Groups cameras and image planes for easy scene management.
    - Assigns all image planes to a dedicated display layer for visibility control.

Raises:
    RuntimeError: If the user cancels image selection or no files are selected.
    ValueError: For invalid parameters passed to functions.

Returns:
    None (The script creates objects in the Maya scene).

"""

from typing import Any

from maya import cmds

views = {
    "front": (0, 0, 1, 0, 0, 0),
    "back": (0, 0, -1, 0, 180, 0),
    "left": (-1, 0, 0, 0, -90, 0),
    "right": (1, 0, 0, 0, 90, 0),
    "top": (0, 1, 0, 90, 0, 0),
    "bottom": (0, -1, 0, -90, 0, 0),
}


def create_camera(view_name, translation, rotation) -> Any:
    """Create a camera for the specified view.

    :param view_name: The name of the view (e.g., 'front', 'back').
    :param translation: A list containing the translation values (x, y, z).
    :param rotation: A list containing the rotation values (x, y, z).
    :return: The created camera name.
    """
    cam_name = f"_{view_name}_cam"
    camera, _ = cmds.camera(name=cam_name, orthographic=True)
    cmds.setAttr(f"{camera}.translate", *translation)
    cmds.setAttr(f"{camera}.rotate", *rotation)
    cmds.setAttr(f"{camera}.visibility", 0)  # Set camera visibility to off
    return camera


def create_image_plane(image_file, rotation, alpha_gain=0.5) -> Any:
    """Create an image plane with specified parameters.

    :param image_file: The file path of the image.
    :param rotation: A list containing the rotation values (x, y, z).
    :param alpha_gain: The alpha gain for the image plane.
    :return: The created image plane name.
    """
    image_plane = cmds.imagePlane(fileName=image_file)[0]
    cmds.setAttr(f"{image_plane}.rotate", *rotation)
    cmds.setAttr(f"{image_plane}.alphaGain", alpha_gain)

    return image_plane


def position_image_planes(image_planes, spacing, ground_offset) -> None:
    """Position image planes to avoid overlap based on the number of images.

    :param image_planes: A list of image plane names.
    :param spacing: The spacing value to prevent overlap.
    :param ground_offset: The offset to position image planes above the ground.
    """
    for i, image_plane in enumerate(image_planes):
        if i < 6:
            view = list(views.keys())[i]
            translation = [val * spacing * 1.2 for val in views[view][:3]]
            translation[1] += ground_offset  # Raise Y coordinate to ensure above ground
        else:
            z_position = spacing * 1.2 + (i - 5) * 5
            translation = [0, ground_offset, z_position]

        cmds.setAttr(f"{image_plane}.translate", *translation)
        # Set pivot point to (0, 0, 0)
        cmds.xform(image_plane, ws=True, piv=(0, ground_offset, 0))


def create_cameras():
    """Create 6 cameras and 1 render camera."""
    cameras_group = cmds.group(em=True, name="Cameras_Group")

    for i in range(6):
        view = list(views.keys())[i]
        translation = [val * 100 for val in views[view][:3]]
        rotation = views[view][3:]
        camera = create_camera(view, translation, rotation)
        cmds.parent(camera, cameras_group)

    camera, _ = cmds.camera(name="__render_cam")
    cmds.setAttr(f"{camera}.translate", *(10, 10, 10))
    cmds.setAttr(f"{camera}.visibility", 0)  # Set camera visibility to off
    cmds.parent(camera, cameras_group)


def create_image_planes_for_views(image_files) -> None:
    """Create image planes in Maya based on the number of images selected.

    :param image_files: A list of image file paths.
    """
    image_planes_group = cmds.group(em=True, name="Image_Planes_Group")
    image_planes_layer = cmds.createDisplayLayer(name="Image_Planes_Layer", empty=True)

    image_planes = []
    spacing = 0
    ground_offset = 0

    # Create image planes
    for i, image_file in enumerate(image_files):
        if i < 6:
            view = list(views.keys())[i]
            rotation = views[view][3:]
            image_plane = create_image_plane(image_file, rotation)
        else:
            rotation = [0, 0, 0]
            image_plane = create_image_plane(image_file, rotation)

        spacing = max(
            spacing,
            cmds.getAttr(f"{image_plane}.width"),
            cmds.getAttr(f"{image_plane}.height"),
        )
        ground_offset = max(ground_offset, cmds.getAttr(f"{image_plane}.height") / 2)

        cmds.parent(image_plane, image_planes_group)
        cmds.editDisplayLayerMembers(image_planes_layer, image_plane)
        image_planes.append(image_plane)

    # Position image planes to avoid overlap
    position_image_planes(image_planes, spacing, ground_offset)

    # 创建一个立方体，用于帮助调整image planes的位置
    cube = cmds.polyCube()[0]
    # 移动立方体
    cmds.setAttr(f"{cube}.translate", 0, ground_offset, 0)


def select_images() -> Any:
    """Prompts the user to select image files and returns the list of file paths."""
    image_files = cmds.fileDialog2(
        fileFilter="Images (*.jpg *.png *.tiff *.bmp)",
        dialogStyle=2,
        cap="Select images for views",
        fileMode=4,
    )

    if not image_files:
        raise RuntimeError("Selection canceled or no files selected.")

    return image_files


# Example usage: Prompt the user to select images and then create the image planes
try:
    image_files = select_images()  # Get image file paths from the user
    create_image_planes_for_views(
        image_files,
    )  # Create the image planes based on the user's selections
    create_cameras()

    print(
        f"{len(image_files)} image planes and corresponding cameras have been created successfully!",
    )
except RuntimeError as e:
    print(f"Error: {e}")
except ValueError as e:
    print(f"Error: {e}")
