import bpy
import os
import mathutils
import bmesh
import math
import struct
from enum import Enum
from mathutils import *
from .brg_util import *

def start(context, file_path, addon_prefs):
    #open the file
    file = File(file_path, 'rb', addon_prefs)
    print("\n\n--<{ Importing AoM model \"" + file.nice_name + '" }>--')

    #create a basic mesh object
    mesh = bpy.data.meshes.new(file.nice_name)
    mesh_obj = bpy.data.objects.new(file.nice_name, mesh)
    bpy.context.scene.objects.link(mesh_obj)

    mid = 0
    #reading loop
    head = file.read(4)
    while head:
        print("\n######### Reading:", head,"#########")

        if head == "BANG": #Main file header
            read_file_header(file,mesh_obj)
        elif head == "ASET": #Animation definition
            read_animation_header(file, mesh_obj)
        elif head == "MESI": #Mesh data
            read_mesh(file,mesh_obj,mid)
            mid += 1
        elif head == "MTRL": #Material settings
            read_materials(file,mesh_obj)
        else:
            break

        head = file.read(4)

    #close the file reading
    file.close()
    mesh_obj.select = True
    bpy.context.scene.objects.active = mesh_obj





def read_file_header(file,mesh_obj):
    file.skip(4)

    #add basic materials
    num_materials = file.read_uint()
    print("num_materials:", num_materials)
    for i in range(num_materials):
        mat = bpy.data.materials.new("Temp." + str(i) + ".Mtrl")
        mat.use_nodes = True
        mesh_obj.data.materials.append(mat)

    file.skip(4)

    #add basis for shapekeys
    num_shapekeys = file.read_uint()
    print("num_shapekeys:", num_shapekeys)
    if (num_shapekeys > 1):
        mesh_obj.shape_key_add("0")
        mesh_obj.data.shape_keys.use_relative = False
        mesh_obj.data.shape_keys.eval_time = 0
        # bpy.ops.object.shape_key_retime()
        mesh_obj.active_shape_key_index = 0

    file.skip(8)





def read_animation_header(file, mesh_obj):
    num_frames = file.read_uint()
    file.skip(4)
    animation_time = file.read_float()
    file.skip(4)
    spf = file.read_float()
    fps = file.read_float()
    file.skip(4)
    print("Frames:",num_frames,"Time:",animation_time,"fps:",fps)

    #set animation settings
    scn = bpy.context.scene
    scn.render.fps = 30
    scn.frame_current = 1
    scn.frame_start = 1
    scn.frame_end = math.floor(animation_time * scn.render.fps)
    mesh_obj.data.shape_keys.eval_time = 0;
    mesh_obj.data.shape_keys.keyframe_insert("eval_time", frame = 0)
    mesh_obj.data.shape_keys.eval_time = num_frames * 10;
    mesh_obj.data.shape_keys.keyframe_insert("eval_time", frame = animation_time * scn.render.fps)





def read_mesh(file,mesh_obj,mid):
    version = file.read_short() #2
    mformat = file.read_short() #2
    print("ID:",mid,"- version:", version, "format:", mformat)
    num_vertices = file.read_short() #2
    num_faces = file.read_short() #2
    state = file.read_int() #4
    print("num_vertices:", num_vertices)
    print("num_faces:", num_faces)

    hitbox_pos = file.read_vec3_full() #12
    unknown03 = file.read_float() #4
    unknown03Const = file.read_vec3_full() #12
    origin_pos = file.read_vec3_full() #12

    #properties, Very important!
    props = file.read_flag() #4
    print ("First frame??", "No :(" if props.has(MeshFlags.NOTFIRST) else "Yes! :)")

    neg_mesh_pos = file.read_vec3_full() #12
    mesh_pos = file.read_vec3_full() #12

    if not props.has(MeshFlags.NOTFIRST):
        mesh_obj.data.from_pydata(
             [(0.0,0.0,0.0) for x in range(num_vertices)],
             [],
             [(0,0,0) for x in range(num_faces)])
        uvtex = mesh_obj.data.uv_textures.new("UVMap")
    else:
        mesh_obj.shape_key_add(str(mid))
        mesh_obj.active_shape_key_index = mid


    for x in range(num_vertices):
        mesh_obj.data.vertices[x].co = file.read_vec3()

    for x in range(num_vertices):
        mesh_obj.data.vertices[x].normal = file.read_vec3()

    if not props.has(MeshFlags.NOTFIRST):
        uvs = []
        for x in range(num_vertices):
            uvs.append(file.read_vec2())

        for x in range(num_faces):
            mesh_obj.data.polygons[x].material_index = file.read_short()

        for x in range(num_faces):
            mesh_obj.data.polygons[x].vertices = file.read_face()

        mesh_obj.data.update(calc_edges=True, calc_tessface=True)

        uv_loops = mesh_obj.data.uv_layers[-1].data
        for loop in mesh_obj.data.loops:
            uv_loops[loop.index].uv = uvs[loop.vertex_index]

        if props.has(MeshFlags.MATERIALS):
            vertmats = []
            for x in range(num_vertices):
                vertmats.append(file.read_short())
    else:
        mesh_obj.data.update(calc_edges=True, calc_tessface=True)

    file.skip(24)
    check_space = file.read_uint()

    if not check_space:
        anim_time_mult = file.read_float()
        len_space = file.read_uint()
        num_materials_used = file.read_uint()

    if (((props.has(MeshFlags.TRANSPCOLOR) or
            props.has(MeshFlags.CHANGINGCOL)) and
            not props.has(MeshFlags.NOTFIRST)) or
            props.has(MeshFlags.VERTCOLOR)):
        cols = []
        for x in range(num_vertices):
            cols.append(file.read_color())

        mesh.vertex_colors.new('VertexColor')
        col_loops = mesh_obj.data.vertex_colors[0].data
        for loop in mesh_obj.data.loops:
            col_loops[loop.index].uv = cols[loop.vertex_index]


    #Start reading attachtpoints
    if props.has(MeshFlags.ATTACHPOINTS):
        num_matrix = file.read_short()
        print("Number of matrices:", num_matrix)
        num_index = file.read_short()
        file.skip(2)

        if not props.has(MeshFlags.NOTFIRST):
            bpy.ops.object.armature_add(enter_editmode=True,location=mesh_obj.location)
            arm_obj = bpy.context.object
            arm_obj.parent = mesh_obj
            arm_obj.name = file.nice_name + " Apoints"
            armature = arm_obj.data
            armature.name = file.nice_name + " Apoints"
            # print(arm_obj.name)

            bpy.context.scene.objects.active = arm_obj
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            armature.edit_bones.remove(armature.edit_bones['Bone'])

            for i in range(num_matrix):
                bone = armature.edit_bones.new(str(i))
                bone.head = (0.0, 0.0, 0.0)
                bone.tail = (0.0, 0.0, 0.5)
                # print(bone.name)
                # print(armature.edit_bones['0'])
            bpy.ops.object.mode_set(mode='OBJECT')

            shape = custome_shape()
            for bone in arm_obj.pose.bones:
                bone.custom_shape = shape

        arm_obj = mesh_obj.children[0]
        pose = arm_obj.pose
        for i in range(num_matrix*3):
            file.read_vec3(False)
        for i in range(num_matrix):
            pose.bones[str(i)].location = file.read_vec3(False)
        for i in range(num_matrix*2):
            file.read_vec3(False)

        num_points = 0
        print ("Number of indexes:",num_index)
        for i in range(num_index):
            dupli = file.read_int()
            file.skip(4)

            num_points += dupli

        for i in range(num_points):
            point = file.read_byte()
            # pose.bones[str(i)].name = NODE_NAMES[point]
            print(NODE_NAMES[point], str(i),str(point))

    if not check_space and len_space > 0:
        anim_time_adujst = []
        for i in range(len_space):
            anim_time_adujst[i] = file.read_float()





def read_materials(file, mesh_obj):

    index = next(index for index in mesh_obj.data.materials.keys() if index.startswith('Temp.'))
    mat = mesh_obj.data.materials[index]

    matid = file.read_uint()
    props = file.read_flag()
    mat.name = str(matid)
    print("Material id:",index, matid)

    for face in mesh_obj.data.polygons:
        if face.material_index == matid:
            face.material_index = int(index.split('.')[1])

    file.skip(4)
    name_length = file.read_uint()
    file.skip(48)
    texture_name = file.read(name_length)
    file.skip(4)


    img = load_image(file, texture_name)
    if img:
        # print (img)
        img.use_alpha = False

        nodes = mat.node_tree.nodes
        node_texture = nodes.new(type='ShaderNodeTexImage')
        node_texture.image = img
        node_texture.location = -300,0

        links = mat.node_tree.links
        link = links.new(node_texture.outputs[0], nodes.get("Diffuse BSDF").inputs[0])

    if props.has(MatrFlags.SFX):
        file.skip(2)
        sfx_length = file.read_short()
        sfx_name = file.read(sfx_length)
