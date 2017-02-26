# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

#addon info
bl_info = {
    "name": "Age of Mythology Model",
    "description": "Import/Export .brg model files for the game Age of Mythology",
    "author": "Matthijs 'MrEmjeR' de Rijk <mrtherich@gmail.com>",
    "version": (0, 1, 1),
    "blender": (2, 7, 5),
    "warning": "",
    "location": "File > Import-Export",
    "wiki_url": "https://github.com/MrTheRich/AoM-Blender-Addon/wiki",
    "tracker_url": "https://github.com/MrTheRich/AoM-Blender-Addon/issues",
    "support": "OFFICIAL",
    "category": "Import-Export"
    }


#modules
import bpy
import os,sys
from . import brg_import, brg_export, brg_util
from importlib import reload
from bpy.props import *
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty

# addon preferences in blender user preferences
class AoMPreferences(AddonPreferences):
    bl_idname = __name__

    aom_path = StringProperty(
            name="Path to Age of Mythology Installation",
            subtype='FILE_PATH',
            )
    auto_import = BoolProperty(
            name="Autmatically import images from AoM",
            default=True,
            )
    comp_path = StringProperty(
            name="Path to TextureExtractor.exe. (v2)",
            subtype='FILE_PATH',
            )
    glob_tex = BoolProperty(
            name="Default save converted textures globally. Default \"\\[AoM]\\Textures\\Converted\".",
            default=True,
            )
    tex_path = StringProperty(
            name="Path for global texture conversion storage.",
            subtype='FILE_PATH',
            )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Edit here your preferences to use the addon to it's fullest potential.")
        layout.prop(self, "auto_import")
        layout.prop(self, "aom_path")
        layout.prop(self, "comp_path")
        layout.prop(self, "glob_tex")
        layout.prop(self, "tex_path")

#import function
class IMPORT_BRG(bpy.types.Operator, ImportHelper):
    '''Import brg model files from Age of Mythology'''
    bl_idname = "import_scene.brg"
    bl_description = "Import AoM Model"
    bl_label = "Import AoM Model"
    filename_ext = ".brg"
    filter_glob = StringProperty(default="*.brg", options={'HIDDEN'})

    filepath = StringProperty(name="File Path",
        description="Filepath used for importing the brg file",
        maxlen=1024, default="")

    modify_fps = BoolProperty(
            name="Modify frame settings",
            default=False,
            )
    cyclic = BoolProperty(
            name="Cyclic animation",
            default=True,
            )

    def execute(self, context):
        preferences = context.user_preferences
        addon_prefs = preferences.addons[__name__].preferences
        importer = brg_import.BRGImporter(context, self, addon_prefs)

        frame_id = 0 # id for the frame numbers needed for animated objects
        # scan for headers,
        # when one is found, read all the data for the header
        # and scan for the next
        head = importer.read_section_head()
        while head: # reading loop
            print("\n######### Reading:", head,"#########")

            if head == "BANG": #Main file header
                importer.read_file_header()
            elif head == "ASET": #Animation definition
                importer.read_animation_header()
            elif head == "MESI": #Mesh data
                importer.read_mesh(frame_id)
                frame_id += 1
            elif head == "MTRL": #Material settings
                importer.read_materials()
            else:
                break

            head = importer.read_section_head()
        importer.finish_import()

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "modify_fps")
        layout.prop(self, "cyclic")

#export function
class EXPORT_BRG(bpy.types.Operator, ExportHelper):
    '''Export brg model files for Age of Mythology'''
    bl_idname = "export_scene.brg"
    bl_description = "Export AoM Model"
    bl_label = "Export AoM Model"
    filename_ext = ".brg"
    filter_glob = StringProperty(default="*.brg", options={'HIDDEN'})

    filepath = StringProperty(name="File Path",
        description="Filepath used for importing the brg file",
        maxlen=1024, default="")

    def execute(self, context):
        preferences = context.user_preferences
        addon_prefs = preferences.addons[__name__].preferences
        exporter = brg_export.BRGExporter(context, self, addon_prefs)

        frame_id = 0 # id for the frame numbers needed for animated objects
        # scan for headers,
        # when one is found, read all the data for the header
        # and scan for the next
        section_heads = exporter.get_section_heads()
        for head in section_heads: # reading loop
            print("\n######### Reading:", head,"#########")
            exporter.write_section_head(head)

            if head == "BANG": #Main file header
                if not exporter.write_file_header():
                    return {'FINISHED'}
            elif head == "ASET": #Animation definition
                exporter.write_animation_header()
            elif head == "MESI": #Mesh data
                exporter.write_mesh(frame_id)
                frame_id += 1
            elif head == "MTRL": #Material settings
                exporter.write_materials()

        exporter.finish_export()

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

#menu registers
def menu_func_import(self, context):
    self.layout.operator(IMPORT_BRG.bl_idname, text="Age of Mythology (.brg)")

def menu_func_export(self, context):
    self.layout.operator(EXPORT_BRG.bl_idname, text="Age of Mythology (.brg)")

def register():
    bpy.utils.register_module(__name__)
    reload_scripts()
    os.system('cls') # clear the cmd, temponary for debug
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

def reload_scripts(): # reload all subscripts when reloading main script
    reload(brg_util)
    reload(brg_import)
    reload(brg_export)

if __name__ == "__main__":
    register()
