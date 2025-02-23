import bpy
import bmesh
from math import sin, cos, pi
import colorsys
import os

TAU = 2 * pi

def remove_object(obj):
    """
    Remove a mesh object from the scene.

    Parameters:
    obj (bpy.types.Object): The object to remove.

    Raises:
    NotImplementedError: If the object type is not 'MESH'.
    """
    if obj.type == 'MESH':
        if obj.data.name in bpy.data.meshes:
            bpy.data.meshes.remove(obj.data)
        if obj.name in bpy.context.scene.objects:
            bpy.context.scene.objects.unlink(obj)
        bpy.data.objects.remove(obj)
    else:
        raise NotImplementedError("Other types not implemented yet besides 'MESH'")

def track_to_constraint(obj, target):
    """
    Add a 'Track To' constraint to an object.

    Parameters:
    obj (bpy.types.Object): The object to add the constraint to.
    target (bpy.types.Object): The target object for the constraint.

    Returns:
    bpy.types.Constraint: The created constraint.
    """
    constraint = obj.constraints.new('TRACK_TO')
    constraint.target = target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'
    return constraint

def create_target(origin=(0, 0, 0)):
    """
    Create an empty target object at a specified location.

    Parameters:
    origin (tuple): The location to place the target object.

    Returns:
    bpy.types.Object: The created target object.
    """
    target = bpy.data.objects.new('Target', None)
    bpy.context.collection.objects.link(target)
    target.location = origin
    return target

def create_camera(origin, target=None, lens=35, clip_start=0.1, clip_end=200, type='PERSP', ortho_scale=6):
    """
    Create a camera object with specified properties.

    Parameters:
    origin (tuple): The location to place the camera.
    target (bpy.types.Object, optional): The target object for the camera to track.
    lens (float): The focal length of the camera lens.
    clip_start (float): The near clipping distance.
    clip_end (float): The far clipping distance.
    type (str): The type of camera ('PERSP', 'ORTHO', 'PANO').
    ortho_scale (float): The orthographic scale (if type is 'ORTHO').

    Returns:
    bpy.types.Object: The created camera object.
    """
    camera = bpy.data.cameras.new("Camera")
    camera.lens = lens
    camera.clip_start = clip_start
    camera.clip_end = clip_end
    camera.type = type
    if type == 'ORTHO':
        camera.ortho_scale = ortho_scale

    obj = bpy.data.objects.new("CameraObj", camera)
    obj.location = origin
    bpy.context.collection.objects.link(obj)
    bpy.context.scene.camera = obj

    if target:
        track_to_constraint(obj, target)
    return obj

def create_light(origin, type='POINT', energy=1, color=(1, 1, 1), target=None):
    """
    Create a light object with specified properties.

    Parameters:
    origin (tuple): The location to place the light.
    type (str): The type of light ('POINT', 'SUN', 'SPOT', 'HEMI', 'AREA').
    energy (float): The energy of the light.
    color (tuple): The color of the light.
    target (bpy.types.Object, optional): The target object for the light to track.

    Returns:
    bpy.types.Object: The created light object.
    """
    bpy.ops.object.add(type='LIGHT', location=origin)
    obj = bpy.context.object
    obj.data.type = type
    obj.data.energy = energy
    obj.data.color = color

    if target:
        track_to_constraint(obj, target)
    return obj

def simple_scene(target_coords, camera_coords, sun_coords, lens=35):
    """
    Set up a simple scene with a target, camera, and sun light.

    Parameters:
    target_coords (tuple): The location of the target object.
    camera_coords (tuple): The location of the camera object.
    sun_coords (tuple): The location of the sun light object.
    lens (float): The focal length of the camera lens.

    Returns:
    tuple: The created target, camera, and sun objects.
    """
    target = create_target(target_coords)
    camera = create_camera(camera_coords, target, lens)
    sun = create_light(sun_coords, 'SUN', target=target)
    return target, camera, sun

def set_smooth(obj, level=None, smooth=True):
    """
    Apply a subsurf modifier and smooth shading to a mesh object.

    Parameters:
    obj (bpy.types.Object): The object to modify.
    level (int, optional): The level of the subsurf modifier.
    smooth (bool): Whether to apply smooth shading.
    """
    if level:
        modifier = obj.modifiers.new('Subsurf', 'SUBSURF')
        modifier.levels = level
        modifier.render_levels = level

    mesh = obj.data
    for p in mesh.polygons:
        p.use_smooth = smooth

def rainbow_lights(r=5, n=100, freq=2, energy=0.1):
    """
    Create a series of point lights arranged in a rainbow pattern.

    Parameters:
    r (float): The radius of the circle.
    n (int): The number of lights.
    freq (float): The frequency of the sine wave.
    energy (float): The energy of the lights.
    """
    for i in range(n):
        t = float(i) / float(n)
        pos = (r * sin(TAU * t), r * cos(TAU * t), r * sin(freq * TAU * t))

        bpy.ops.object.add(type='LIGHT', location=pos)
        obj = bpy.context.object
        obj.data.type = 'POINT'

        color = tuple(pow(c, 2.2) for c in colorsys.hsv_to_rgb(t, 0.6, 1))
        obj.data.color = color
        obj.data.energy = energy

def remove_all(type=None):
    """
    Remove all objects of a specified type or all objects in the scene.

    Parameters:
    type (str, optional): The type of objects to remove.
    """
    if type:
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_by_type(type=type)
        bpy.ops.object.delete()
    else:
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete(use_global=False)

def create_material(base_color=(1, 1, 1, 1), metalic=0.0, roughness=0.5):
    """
    Create a new material with specified properties.

    Parameters:
    base_color (tuple): The base color of the material.
    metalic (float): The metallic property of the material.
    roughness (float): The roughness property of the material.

    Returns:
    bpy.types.Material: The created material.
    """
    mat = bpy.data.materials.new('Material')

    if len(base_color) == 3:
        base_color = list(base_color)
        base_color.append(1)

    mat.use_nodes = True
    node = mat.node_tree.nodes[0]
    node.inputs[0].default_value = base_color
    node.inputs[4].default_value = metalic
    node.inputs[7].default_value = roughness

    return mat

def colorRGB_256(color):
    """
    Convert an RGB color from 0-255 range to 0-1 range with gamma correction.

    Parameters:
    color (tuple): The RGB color in 0-255 range.

    Returns:
    tuple: The RGB color in 0-1 range with gamma correction.
    """
    return tuple(pow(float(c) / 255.0, 2.2) for c in color)

def render(
    render_folder='rendering',
    render_name='render',
    resolution_x=800,
    resolution_y=800,
    resolution_percentage=100,
    animation=False,
    frame_end=None,
    render_engine='CYCLES'
):
    """
    Render the current scene to a specified folder and file name.

    Parameters:
    render_folder (str): The folder to save the rendering.
    render_name (str): The name of the rendered file.
    resolution_x (int): The horizontal resolution.
    resolution_y (int): The vertical resolution.
    resolution_percentage (int): The resolution percentage.
    animation (bool): Whether to render an animation.
    frame_end (int, optional): The end frame for the animation.
    render_engine (str): The render engine to use ('CYCLES', 'BLENDER_EEVEE', etc.).
    """
    scene = bpy.context.scene
    scene.render.resolution_x = resolution_x
    scene.render.resolution_y = resolution_y
    scene.render.resolution_percentage = resolution_percentage
    scene.render.engine = render_engine
    if frame_end:
        scene.frame_end = frame_end

    if bpy.context.space_data is None:
        render_folder = os.path.join(os.getcwd(), render_folder)
        if not os.path.exists(render_folder):
            os.mkdir(render_folder)

        if animation:
            scene.render.filepath = os.path.join(render_folder, render_name)
            bpy.ops.render.render(animation=True)
        else:
            scene.render.filepath = os.path.join(render_folder, render_name + '.png')
            bpy.ops.render.render(write_still=True)

def bmesh_to_object(bm, name='Object'):
    """
    Convert a BMesh to a mesh object and link it to the scene.

    Parameters:
    bm (bmesh.types.BMesh): The BMesh to convert.
    name (str): The name of the created object.

    Returns:
    bpy.types.Object: The created mesh object.
    """
    mesh = bpy.data.meshes.new(name + 'Mesh')
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    return obj
