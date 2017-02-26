import bpy
import os
from mathutils import *
import bmesh
import math
import struct
from enum import Enum
from .brg_util import *

class BRGExporter:
    def __init__(self, context, settings, addon_prefs):
        self.context = context
        self.addon_prefs = addon_prefs
        self.settings = settings

        # open the file
        self.file = File(self.settings.filepath, 'wb')
        print("\n\n--<{ Exporting AoM model \"" + self.file.nice_name + '" }>--')

        active = bpy.context.scene.objects.active

        if not active or active.type != 'MESH' or active.select == False:
            settings.report({'ERROR'}, "No model selected")
            return None

        self.model = active
        self.mesh = self.model.data


    def finish_export(self):
        '''close file reading and round up scene'''
        self.file.close()


    def get_section_heads(self):
        '''collect a list of sections for exporting'''
        heads = []
        heads.append("HEAD")

        if self.mesh.shape_keys:
            heads.append("ANIM")
            for s in self.mesh.shape_keys:
                heads.append("MESH")
        else:
            heads.append("MESH")

        for m in self.mesh.materials:
            heads.append("MATR")
        return heads


    def write_section_head(self, head):
        '''write a four letter header'''
        self.file.write(head)


    def write_file_header(self):
        '''read the fileheader containing basic information'''
        file, model, mesh = self.file, self.model, self.mesh
        file.empty(4)

        num_materials = len(self.mesh.materials)
        file.write_uint(num_materials)
        print("Number of materials:", num_materials)


        file.empty(4)
        num_shape_keys = 1
        if self.mesh.shape_keys:
            num_shape_keys = len(self.mesh.shape_keys)
        file.write_uint(num_shape_keys)
        print("Number of shape keys:", num_shape_keys)
        file.empty(8)


    def write_animation_header(self):
        pass

    def write_mesh(frame_id):
        pass

    def write_materials():
        pass
