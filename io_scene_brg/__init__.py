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
    "tracker_url": "mailto:mrtherich@gmail.com",
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

    def execute(self, context):

        brg_import.start(context, self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

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
        brg_export.start(context, self.filepath)
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
    os.system('cls')
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

def reload_scripts():
    reload(brg_util)
    reload(brg_import)
    reload(brg_export)

if __name__ == "__main__":
    register()
