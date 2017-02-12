import struct
from struct import pack,unpack
import os
import mathutils
import bpy
import shutil
import subprocess
from enum import Enum

'''Quick functions for helping read brg files'''

## Reading util
class File:
    file_object = None
    name = ""
    nice_name = ""
    file_path = ""
    addon_prefs = None

    def __init__(self, file_path, rw, addon_prefs):
        self.file_object = open(file_path, rw)
        self.name = os.path.basename(self.file_object.name)
        self.file_path = os.path.dirname(self.file_object.name)
        self.nice_name = os.path.splitext(self.name)[0].title()
        self.addon_prefs = addon_prefs

    def close(self):
        '''close the file object'''
        self.file_object.close()

    def read(self, length = 1):
        '''read string with length from file'''
        try:
            return self.file_object.read(length).decode("utf-8")
        except:
            return False

    def read_byte(self, endian = '<'):
        '''read unsigned byte from file'''
        data = unpack(endian+'B', self.file_object.read(1))[0]
        return data

    def read_short(self, endian = '<'):
        '''read unsgned short from file'''
        data = unpack(endian+'H', self.file_object.read(2))[0]
        return data

    def read_uint(self, endian = '<'):
        '''read unsigned integer from file'''
        data = unpack(endian+'I', self.file_object.read(4))[0]
        return data

    def read_int(self, endian = '<'):
        '''read signed integer from file'''
        data = unpack(endian+'i', self.file_object.read(4))[0]
        return data

    def read_flag(self, endian = '<'):
        '''read flag integer from file'''
        i = self.read_int(endian)
        return Flag(i)

    def read_float(self, endian = '<'):
        '''read floating point number from file'''
        data = unpack(endian+'f', self.file_object.read(4))[0]
        return data

    def read_half(self, endian = '<'):
        '''read half floating number from file'''
        s = b'\x00\x00' + self.file_object.read(2)
        data = unpack(endian+'f', s)[0]
        return data

    def read_vec2(self, endian = '<'):
        '''reads a vector with two dimensions'''
        x = self.read_half(endian)
        y = self.read_half(endian)
        return (x,y)

    def read_vec3(self, flip = True, endian = '<'):
        '''reads a vector with three dimensions'''
        x = self.read_half(endian)
        y = self.read_half(endian)
        z = self.read_half(endian)
        if flip:
            return (x,z,y)
        else:
            return (x,y,-z)

    def read_face(self, endian = '<'):
        '''reads a face index with three dimensions'''
        x = self.read_short(endian)
        y = self.read_short(endian)
        z = self.read_short(endian)
        return (x,z,y)

    def read_vec3_full(self, endian = '<'):
        '''reads a vector with three dimensions'''
        x = self.read_float(endian)
        y = self.read_float(endian)
        z = self.read_float(endian)
        return (x,z,y)

    def read_color(self, endian = '<'):
        '''reads a vector with three dimensions'''
        r = self.read_byte(endian)
        g = self.read_byte(endian)
        b = self.read_byte(endian)
        a = self.read_byte(endian)
        return (r/255.0,g/255.0,b/255.0,a/255.0)

    def skip(self, length):
        '''move the read pointer forward with length'''
        self.file_object.seek(length, 1)

#names of attachpoints possible in the game.
NODE_NAMES = "TARGETPOINT LAUNCHPOINT CORPSE DECAL FIRE GATHERPOINT RESERVED9 RESERVED8 RESERVED7 RESERVED6 RESERVED5 RESERVED4 RESERVED3 RESERVED2 RESERVED1 RESERVED0 SMOKE9 SMOKE8 SMOKE7 SMOKE6 SMOKE5 SMOKE4 SMOKE3 SMOKE2 SMOKE1 SMOKE0 GARRISONFLAG HITPOINTBAR RIGHTFOREARM LEFTFOREARM RIGHTFOOT LEFTFOOT RIGHTLEG LEFTLEG RIGHTTHIGH LEFTTHIGH PELVIS BACKABDOMEN FRONTABDOMEN BACKCHEST FRONTCHEST RIGHTSHOULDER LEFTSHOULDER NECK RIGHTEAR LEFTEAR CHIN FACE FOREHEAD TOPOFHEAD RIGHTHAND LEFTHAND RESERVED SMOKEPOINT ATTACHPOINT".split()

class MeshFlags(Enum):
    NONE1        = 0x80000028
    TRANSPCOLOR  = 0x40000028
    NONE2        = 0x20000028
    NONE3        = 0x10000028
    MOVINGTEX    = 0x08000028
    NOTFIRST     = 0x04000028
    NONE4        = 0x02000028
    ATTACHPOINTS = 0x01000028
    NONE5        = 0x00800028
    MATERIALS    = 0x00400028
    CHANGINGCOL  = 0x00200028
    NONE7        = 0x00100028
    NONE8        = 0x00080028
    NONE9        = 0x00040028
    TEXTURE      = 0x00020028
    VERTCOLOR    = 0x00010028

class MatrFlags(Enum):
    SFX          = 0x1C000000
    GLOW         = 0x00200000
    MATNONE1     = 0x00800000
    PLAYERCOLOR  = 0x00040000
    SOLIDCOLOR   = 0x00020000
    MATTEXTURE   = 0x00000030

class Flag:
    value = 0
    def __init__(self, value):
        self.value = value

    def has(self, flag):
        return self.value & flag.value == flag.value

def custome_shape():
    mesh = bpy.data.meshes.new("AttachpointShape")
    object = bpy.data.objects.new("AttachpointShape", mesh)
    w = 0.075
    mesh.from_pydata([(0,0,0),(w,0,0),(0,w,0),(0,0,w),
                              (1,0,0),(1,w,0),(1,0,w),
                              (0,1,0),(w,1,0),(0,1,w),
                              (0,0,1),(w,0,1),(0,w,1)],[],
                     [(0,4,5,2),(0,4,6,3),
                      (0,7,8,1),(0,7,9,3),
                      (0,10,11,1),(0,10,12,2)])
    for x,m in enumerate([0,0,1,1,2,2]):
        object.data.polygons[x].material_index = m
    object.data.update(calc_edges=True, calc_tessface=True)
    object.use_fake_user = True
    mesh.show_double_sided = True
    for i,c in enumerate([(1,0,0),(0,1,0),(0,0,1)]):
        mat = bpy.data.materials.new("_custom_shape." + str(i))
        mat.use_nodes = True
        mat.diffuse_color = c
        mat.diffuse_intensity = 1.0
        mat.specular_color = (0,0,0)
        object.data.materials.append(mat)
    return object


def copy_ddt(file, file_path, texture_name):
    compiler = os.path.join(file.addon_prefs.comp_path, 'TextureExtractor.exe')
    tex_path = os.path.join(file.addon_prefs.aom_path, "textures", texture_name) + '.ddt'
    new_path = os.path.join(file_path, texture_name) + '.tga'

    if os.path.isfile(new_path): #file already exsists localy
        return bpy.data.images.load(new_path)

    if (os.path.isfile(compiler) and os.path.isfile(tex_path)):
        print("Trying to convert image to ddt...")
        FNULL = open(os.devnull, 'w')
        args = '"' + compiler + '" -o "' + new_path + '" -i "' + tex_path + '"'
        # print(args)
        subprocess.call(args, stdout=FNULL, stderr=FNULL, shell=False)
        if os.path.isfile(new_path):
            print("Succefully converted to:")
            print(new_path)
            return bpy.data.images.load(new_path)
        else:
            print("Failed to convert")
    else:
        print("Original .ddt does not exsist.")

    try:
        print("Trying to copy image from AoM install folder...")
        shutil.copy(aom_path, file_path)
        if os.path.isfile(new_path): #file is succesfuly coppied
            return None
        return None
    except:
        return None

def load_image(file, texture_name):
    converted_path = os.path.join(file.addon_prefs.aom_path, "textures\\converted")
    if not os.path.exists(converted_path):
        os.makedirs(converted_path)

    glob_path = file.addon_prefs.tex_path if file.addon_prefs.tex_path else converted_path
    # print(glob_path)
    paths = [
        os.path.join(file.file_path, texture_name),
        os.path.join(bpy.path.abspath("//"), texture_name),
        os.path.join(glob_path, texture_name) if file.addon_prefs.glob_tex else ""
    ]
    exts = [
        '.png',
        '.tga',
        '.bmp',
        '.jpg',
        '.jpeg'
    ]
    # print(paths, file.addon_prefs.tex_path)
    img = None

    for path in paths:
        for ext in exts:
            try:
                img = bpy.data.images.load(path+ext)
                print("Image found:", path+ext)
                return img
            except RuntimeError:
                continue
            else:
                break
    print("Still seraching for:", texture_name)
    # print (file.addon_prefs.glob_tex)
    if not img:
        if file.addon_prefs.glob_tex and os.path.exists(glob_path):
            img = copy_ddt(file, glob_path, texture_name)
        else:
            if os.path.exists(bpy.path.abspath("//")):
                img = copy_ddt(file, bpy.path.abspath("//"), texture_name)
            else:
                img = copy_ddt(file, file.file_path, texture_name)
    if not img:
        print("Can't find %s, add the file to the same folder or specify AoM installation in the preferences" % texture_name)
        #     print("No local file found, %s.ddt copied over from AoM installation forlder. Use an external tool for conversion." % texture_name)
        # else:
    return img
