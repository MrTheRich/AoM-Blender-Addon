import bpy
import os
from mathutils import *
import bmesh
import math
import struct
from enum import Enum
from mathutils import *
from .brg_util import *

class BRGImporter:
    def __init__(self, context, settings, addon_prefs):
        '''set up variables, open file for reading and create new mesh'''
        self.context = context
        self.addon_prefs = addon_prefs
        self.settings = settings

        # open the file
        self.file = File(self.settings.filepath, 'rb')
        print("\n\n--<{ Importing AoM model \"" + self.file.nice_name + '" }>--')

        # create a basic mesh object
        self.mesh = bpy.data.meshes.new(self.file.nice_name)
        self.model = bpy.data.objects.new(self.file.nice_name, self.mesh)
        bpy.context.scene.objects.link(self.model)
        self.model.select = True
        bpy.context.scene.objects.active = self.model
        self.model.location = bpy.context.scene.cursor_location #Needs preference
        bpy.ops.object.mode_set(mode='OBJECT')



    def finish_import(self):
        '''close file reading and round up scene'''
        self.file.close()
        # Select the imported objects
        self.model.select = True
        bpy.context.scene.objects.active = self.model
        if hasattr(self, "frames"):
            bpy.ops.object.shape_key_retime()



    def read_section_head(self):
        '''read a four letter header'''
        return self.file.read(4)



    def read_file_header(self):
        '''read the fileheader containing basic information'''
        file, model, mesh = self.file, self.model, self.mesh
        file.skip(4)

        #add basic materials
        num_materials = file.read_uint()
        self.materials = []
        print("Number of materials:", num_materials)


        file.skip(4)
        #add basis for shapekeys
        num_shape_keys = file.read_uint()
        print("Number of shape keys:", num_shape_keys)
        file.skip(8)




    def read_animation_header(self):
        '''read animation info and set up framesettings'''
        file, model, mesh = self.file, self.model, self.mesh
        self.frames = file.read_uint() # amount of frames in the file for animation
        file.skip(4)
        self.anim_time = file.read_float()
        file.skip(4)
        self.spf = file.read_float()
        self.fps = file.read_float()
        file.skip(4)
        print("Frames:", self.frames,"Time:", self.anim_time, "fps:", self.fps)

        # set animation settings of the scene.
        scn = bpy.context.scene
        if self.settings.modify_fps:
            scn.render.fps = 30 # default for the game
            scn.frame_current = 1
            scn.frame_start = 1
            scn.frame_end = math.floor(self.anim_time * scn.render.fps)
        self.frame_len = self.anim_time * scn.render.fps / self.frames
        print ("frame length", self.frame_len)



    def read_mesh(self, frame_id):
        '''load a single frame, add shapekey if necessary'''
        file, model, mesh = self.file, self.model, self.mesh

        self.frame_id = frame_id
        self.version = file.read_short() #2
        self.format = file.read_short() #2
        print("Frame:", frame_id, "- version:", self.version, "format:", self.format)

        #vertex and face info
        self.num_vertices = file.read_short() #2
        self.num_faces = file.read_short() #2
        self.state = file.read_int() #4
        print("vertices:", self.num_vertices, "faces:", self.num_faces, "state:", self.state)

        # bounding box and position
        self.bb_center = file.read_vec3_full() #12
        self.bb_height = file.read_float() #4
        self.unknown_vector = file.read_vec3_full() #12
        self.ground_pos = file.read_vec3_full() #12
        self.ground_pos.negate()
        if frame_id == 0:
            model.delta_location = self.ground_pos
        # bpy.data.objects['pos4'].parent = model
        # bpy.data.objects['pos4'].location = (0,0,unknown03)
        # bpy.data.objects['pos4'].keyframe_insert(data_path="location", index=-1, frame=frame_id+1)

        # property flags, Very important!
        self.props = file.read_flag() #4
        first_frame = not self.props.has(MeshFlags.NOTFIRST) # used often
        print ("First frame??", "No :(" if first_frame else "Yes! :)")

        # bounding box corners
        self.bb_corner_positive = file.read_vec3_full() #12
        self.bb_corner_negative = file.read_vec3_full() #12

        # if this is the first frame, create the vertices.
        # otherwise add an extra shapekey.
        if first_frame:
            mesh.from_pydata(
                 [(0.0,0.0,0.0) for x in range(self.num_vertices)],
                 [], [(0,0,0) for x in range(self.num_faces)])
            mesh.uv_textures.new("UVMap")
            print(mesh.shape_keys)
            # if this is an animation, add shapekey
            if hasattr(self, 'frames'):
                for frame in range(1,self.frames+1):
                    model.shape_key_add(str(frame))

                mesh.shape_keys.animation_data_create()
                action = bpy.data.actions.new(name="Shapekey Driver")
                mesh.shape_keys.animation_data.action = action
                fcurve = action.fcurves.new("eval_time")

                for frame in range(1,self.frames+1):
                    key = fcurve.keyframe_points.insert((frame) * self.frame_len, (frame) * 10)
                    key.interpolation = 'LINEAR'

                if self.settings.cyclic:
                    fcurve.modifiers.new('CYCLES')

                mesh.shape_keys.use_relative = False

        # load the vertex placeholders
        vertices = []
        if hasattr(self, 'frames'):
            model.active_shape_key_index = frame_id
            vertices = model.active_shape_key.data
        else:
            vertices = model.data.vertices

        # read all the vertex positions and normals
        for vertex in vertices:
            vertex.co = file.read_vec3()
        for vertex in vertices:
            file.read_vec3() # not needed in Blender

        # this data only appears once at the first frame.
        if first_frame:
            # uv coordinates, resolved later on.
            uvs = [file.read_vec2() for v in vertices]

            # material index for faces.
            # it's set to a very high value in default brg files
            # corrected during the material reading pass
            for face in mesh.polygons:
                face.material_index = file.read_short()

            # face data
            for face in mesh.polygons:
                face.vertices = file.read_face()

            # update the mesh data for uv loops.
            mesh.update(calc_edges=True, calc_tessface=True)
            uv_loops = mesh.uv_layers[-1].data
            for loop in mesh.loops:
                uv_loops[loop.index].uv = uvs[loop.vertex_index]

            if self.props.has(MeshFlags.MATERIALS): # no vertex materials in blender
                vertmats = [file.read_short() for v in vertices]

        # update mesh data in memory
        mesh.update(calc_edges=True, calc_tessface=True)

        file.skip(24)
        check_space = file.read_uint() # Unkown but important flag for edge cases

        if not check_space: # some optional read data, meaning not sure
            anim_time_mult = file.read_float()
            len_space = file.read_uint()
            num_materials_used = file.read_uint()

        # vertex colors, can be animated or not
        if (((self.props.has(MeshFlags.TRANSPCOLOR) or
              self.props.has(MeshFlags.CHANGINGCOL)) and
              not self.props.has(MeshFlags.NOTFIRST)) or
              self.props.has(MeshFlags.VERTCOLOR)):
            cols = [file.read_color() for v in vertices]

            model.data.vertex_colors.new('VertexColor')
            col_loops = model.data.vertex_colors[0].data
            for loop in model.data.loops:
                col_loops[loop.index].uv = cols[loop.vertex_index]

        if self.props.has(MeshFlags.ATTACHPOINTS):
            self.read_attachpoints()

        bpy.context.scene.objects.active = model
        #optional extra space in some edge cases, meaning unsure
        if not check_space and len_space > 0:
            anim_time_adujst = [file.read_float() for i in range(len_space)]






    def read_attachpoints(self):
        '''create an armature with attachpoint bones'''
        file, model, mesh = self.file, self.model, self.mesh
        self.num_matrix = file.read_short()
        self.num_index = file.read_short()
        print("Matrices:", self.num_matrix, "Indexcount:", self.num_index)
        file.skip(2)

        # attachpoint definitions, only happen at first frame
        if not self.props.has(MeshFlags.NOTFIRST):
            bpy.ops.object.armature_add(enter_editmode=True,location=(0,0,0))
            self.armature = bpy.context.object
            self.armature.parent = model
            self.armature.name = file.nice_name + " Apoints"
            self.armature.data.name = file.nice_name + " Apoints"

            # Remove default bone
            edit_bones = self.armature.data.edit_bones
            edit_bones.remove(edit_bones['Bone'])

            # Add new bones
            for i in range(self.num_matrix):
                bone = edit_bones.new(str(i))
                bone.head = (0.0, 0.0, 0.0)
                bone.tail = (0.0, 0.25, 0.0)
            bpy.ops.object.mode_set(mode='OBJECT')

            # Create and set custom shape for bones
            shape = custome_shape()
            for bone in self.armature.pose.bones:
                bone.custom_shape = shape

        bpy.context.scene.objects.active = self.armature

        # Read armature matrix data
        xs = [file.read_vec3() for i in range(self.num_matrix)]
        ys = [file.read_vec3() for i in range(self.num_matrix)]
        zs = [file.read_vec3() for i in range(self.num_matrix)]

        # Read location, compile matrix and keyframe. Needs to change to fcurves!
        bpy.ops.object.mode_set(mode='POSE')
        if hasattr(self, 'frames'):
            bpy.context.scene.frame_set((self.frame_id + 1) * self.frame_len)
        for i,m in enumerate(zip(zs,ys,xs)):
            m = Matrix(m).transposed().to_4x4()
            m.translation = file.read_vec3()
            self.armature.pose.bones[str(i)].matrix = m

        unknown_vectors = [file.read_vec3() for i in range(self.num_matrix*2)]

        if hasattr(self, 'frames'):
            bpy.ops.pose.select_all(action='SELECT')
            bpy.ops.anim.keyframe_insert(type='LocRotScale')
        bpy.ops.object.mode_set(mode='OBJECT')

        # Read attachpoint names. Not correct yet!
        num_points = 0
        print ("Number of indexes:",self.num_index)
        for i in range(self.num_index):
            dupli = file.read_int()
            file.skip(4)
            num_points += dupli

        for i in range(num_points):
            point = file.read_byte()
            # pose.bones[str(i)].name = NODE_NAMES[point]
            # print(NODE_NAMES[point], str(i),str(point))





    def read_materials(self):
        '''fill in material data and add nodes'''
        file, model, mesh = self.file, self.model, self.mesh

        # read the material header data
        index = len(mesh.materials)
        self.matid = file.read_uint()
        self.props = file.read_flag()
        print("Material", index, "with id:", self.matid)

        # Create new material and add to mesh
        self.material = bpy.data.materials.new(str(self.matid))
        self.material.use_nodes = True
        node_tree = self.material.node_tree
        mesh.materials.append(self.material)

        # update the face material index data to the blender index.
        for face in mesh.polygons:
            if face.material_index == self.matid:
                face.material_index = index

        # texture settings
        file.skip(4)
        name_length = file.read_uint()
        file.skip(48) # unknown data
        texture_name = file.read(name_length)
        file.skip(4)

        # load or convert the image.
        img = load_image(file, self.addon_prefs, texture_name)
        if img:
            # setup the cycles material
            node_texture = node_tree.nodes.new(type='ShaderNodeTexImage')
            node_texture.image = img
            node_texture.location = -300,350

            links = node_tree.links
            link = links.new(node_texture.outputs[0], node_tree.nodes.get("Diffuse BSDF").inputs[0])

        # optional sfx data
        if self.props.has(MatrFlags.SFX):
            file.skip(2)
            sfx_length = file.read_short()
            sfx_name = file.read(sfx_length)
