import struct
from struct import pack,unpack
import os
import mathutils
import math
import bpy
import shutil
import subprocess
from enum import Enum

'''Quick functions for helping read brg files'''

# File reading helper with functions to read binary files.
class File:
    def __init__(self, file_path, rw):
        self.file_object = open(file_path, rw)
        self.name = os.path.basename(self.file_object.name)
        self.file_path = os.path.dirname(self.file_object.name)
        self.nice_name = os.path.splitext(self.name)[0].title()

    def close(self):
        '''close the file object'''
        self.file_object.close()

    def read(self, length = 1):
        '''read string with length from file'''
        try:
            return self.file_object.read(length).decode("utf-8")
        except:
            return False

    def read_byte(self):
        '''read unsigned byte from file'''
        data = unpack('B', self.file_object.read(1))[0]
        return data

    def read_short(self):
        '''read unsgned short from file'''
        data = unpack('H', self.file_object.read(2))[0]
        return data

    def read_uint(self):
        '''read unsigned integer from file'''
        data = unpack('I', self.file_object.read(4))[0]
        return data

    def read_int(self):
        '''read signed integer from file'''
        data = unpack('i', self.file_object.read(4))[0]
        return data

    def read_flag(self):
        '''read flag integer from file'''
        i = self.read_int()
        return Flag(i)

    def read_float(self):
        '''read floating point number from file'''
        data = unpack('f', self.file_object.read(4))[0]
        return data

    def read_half(self):
        '''read half floating number from file'''
        s = b'\x00\x00' + self.file_object.read(2)
        data = unpack('f', s)[0]
        return data

    def read_vec2(self):
        '''reads a vector with two dimensions'''
        x = self.read_half()
        y = self.read_half()
        return (x,y)

    def read_vec3(self, flip = True):
        '''reads a vector with three dimensions'''
        x = self.read_half()
        y = self.read_half()
        z = self.read_half()
        return mathutils.Vector((x,z,y))

    def read_face(self):
        '''reads a face index with three dimensions'''
        x = self.read_short()
        y = self.read_short()
        z = self.read_short()
        return (x,z,y)

    def read_vec3_full(self):
        '''reads a vector with three dimensions'''
        x = self.read_float()
        y = self.read_float()
        z = self.read_float()
        return mathutils.Vector((x,z,y))

    def read_color(self):
        '''reads a byte vector with four dimensions'''
        r = self.read_byte()
        g = self.read_byte()
        b = self.read_byte()
        a = self.read_byte()
        return (r/255.0,g/255.0,b/255.0,a/255.0)

    def skip(self, length):
        '''move the read pointer forward with length'''
        self.file_object.seek(length, 1)

    def write_empty(self, length):
        '''move the write pointer forward with length'''
        s = "\x00" * length
        self.file_object.write(s)

    def write(self, data):
        '''write a ascii string'''
        self.file_object.write(str(data).encode('ascii'))

    def write_byte(self, data):
        '''write unsigned byte to file'''
        self.file_object.write(pack('B', data))

    def write_uint(self, data):
        '''write unsigned integer to file'''
        self.file_object.write(pack('I', data))

    def write_int(self, data):
        '''write signed integer to file'''
        self.file_object.write(pack('i', data))

    def write_short(self, data):
        '''write unsigned short to file'''
        self.file_object.write(pack('H', data))

    def write_flag(self, data):
        '''write flag to file'''
        self.write_int(data.value)

    def write_float(self, data):
        '''write floating point to file'''
        self.file_object.write(self, pack('f', data))

    def write_half(self, data):
        '''write half floating point to file'''
        f = pack('f', data)[-2:]
        self.file_object.write(self, f)

    def write_vec2(self, vec):
        '''write a vector with two dimensions'''
        x,y = vec
        self.write_half(x)
        self.write_half(y)

    def write_vec3(self, vec):
        '''write a vector with three dimensions'''
        x,y,z = vec
        self.write_half(x)
        self.write_half(y)
        self.write_half(z)

    def write_vec3_full(self, vec):
        '''write a vector with three dimensions'''
        x,y,z = vec
        self.write_float(x)
        self.write_float(y)
        self.write_float(z)

    def write_face(self, vec):
        '''write a face index with three dimensions'''
        x,y,z = vec
        self.write_short(x)
        self.write_short(y)
        self.write_short(z)

# names of attachpoints possible in the game.
NODE_NAMES = "TARGETPOINT LAUNCHPOINT CORPSE DECAL FIRE GATHERPOINT RESERVED9 RESERVED8 RESERVED7 RESERVED6 RESERVED5 RESERVED4 RESERVED3 RESERVED2 RESERVED1 RESERVED0 SMOKE9 SMOKE8 SMOKE7 SMOKE6 SMOKE5 SMOKE4 SMOKE3 SMOKE2 SMOKE1 SMOKE0 GARRISONFLAG HITPOINTBAR RIGHTFOREARM LEFTFOREARM RIGHTFOOT LEFTFOOT RIGHTLEG LEFTLEG RIGHTTHIGH LEFTTHIGH PELVIS BACKABDOMEN FRONTABDOMEN BACKCHEST FRONTCHEST RIGHTSHOULDER LEFTSHOULDER NECK RIGHTEAR LEFTEAR CHIN FACE FOREHEAD TOPOFHEAD RIGHTHAND LEFTHAND RESERVED SMOKEPOINT ATTACHPOINT".split()

# flags for mesh properties.
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

#flags for material properties
class MatrFlags(Enum):
    SFX          = 0x1C000000
    GLOW         = 0x00200000
    MATNONE1     = 0x00800000
    PLAYERCOLOR  = 0x00040000
    SOLIDCOLOR   = 0x00020000
    MATTEXTURE   = 0x00000030

# helper class for flags
class Flag:
    value = 0
    def __init__(self, value):
        self.value = value

    def has(self, flag):
        return self.value & flag.value == flag.value

# custom generated shape for attachpoint bones
def custome_shape():
    mesh = bpy.data.meshes.new("AttachpointShape")
    cus_obj = bpy.data.objects.new("AttachpointShape", mesh)
    w = 0.05 # width of the axis of the shape
    mesh.from_pydata([(0,0,0),(w,0,0),(0,w,0),(0,0,w),
                              (1,0,0),(1,w,0),(1,0,w),
                              (0,1,0),(w,1,0),(0,1,w),
                              (0,0,1),(w,0,1),(0,w,1)],[],
                     [(0,4,5,2),(0,4,6,3),
                      (0,7,8,1),(0,7,9,3),
                      (0,10,11,1),(0,10,12,2)])
    # set the material index for the sides
    for x,m in enumerate([0,0,1,1,2,2]):
        cus_obj.data.polygons[x].material_index = m
    cus_obj.data.update(calc_edges=True, calc_tessface=True)
    cus_obj.use_fake_user = True
    mesh.show_double_sided = True

    #create three materials for each axis
    for i,c in enumerate([(1,0,0),(0,1,0),(0,0,1)]):
        mat = bpy.data.materials.new("_custom_shape." + str(i))
        mat.use_nodes = True
        mat.diffuse_color = c
        mat.diffuse_intensity = 1.0
        mat.specular_color = (0,0,0)
        cus_obj.data.materials.append(mat)

    return cus_obj


def copy_ddt(file, addon_prefs, file_path, texture_name):
    '''copy the texture from another place, convert it if TextureExtrator is found'''
    compiler = os.path.join(addon_prefs.comp_path, 'TextureExtractor.exe')
    tex_path = os.path.join(addon_prefs.aom_path, "textures", texture_name) + '.ddt'
    new_path = os.path.join(file_path, texture_name) + '.tga'

    if os.path.isfile(os.path.join(file.file_path, texture_name) + '.ddt'):
        tex_path = os.path.join(file.file_path, texture_name) + '.ddt'

    if os.path.isfile(new_path): #file already exsists localy
        return bpy.data.images.load(new_path)

    #try to convert the image from ddt using the TextureExtractor.exe
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
        print("Original .ddt does not exsist or TextureExtractor.exe not found")

    # try ot copy the raw ddt over
    try:
        print("Trying to copy image from AoM install folder...")
        shutil.copy(aom_path, file_path)
        if os.path.isfile(new_path): #file is succesfuly coppied
            return None
    except:
        return None

def load_image(file, addon_prefs, texture_name):
    '''search for the texture nearby or convert it and load it in blender'''
    converted_path = os.path.join(addon_prefs.aom_path, "textures\\converted")
    if (addon_prefs.glob_tex and
            not os.path.exists(converted_path) and
            os.path.exists(addon_prefs.aom_path)):
        os.makedirs(converted_path) # create textures\converted if nonexistent

    # Use specified global path otherwise use default textures\converted.
    glob_path = addon_prefs.tex_path if addon_prefs.tex_path else converted_path
    # print(glob_path)
    paths = [ # all possible paths in a list
        os.path.join(file.file_path, texture_name),
        os.path.join(bpy.path.abspath("//"), texture_name),
        os.path.join(glob_path, texture_name) if addon_prefs.glob_tex else ""]
    exts = [ # all possible extensions in a list
        '.png',
        '.tga',
        '.bmp',
        '.jpg',
        '.jpeg']
    # print(paths, file.addon_prefs.tex_path)
    img = None

    # check for texture exsisting in all possible paths
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
    # if no readable texture found, try to convert one from ddt
    if not img:
        if addon_prefs.glob_tex and os.path.exists(glob_path):
            img = copy_ddt(file, addon_prefs, glob_path, texture_name)
        else:
            if os.path.exists(bpy.path.abspath("//")):
                img = copy_ddt(file, addon_prefs, bpy.path.abspath("//"), texture_name)
            else:
                img = copy_ddt(file, addon_prefs, file.file_path, texture_name)
    # if all else fails let user know
    if not img:
        print("Can't find %s, add the file to the same folder or specify AoM installation in the preferences" % texture_name)
        #     print("No local file found, %s.ddt copied over from AoM installation forlder. Use an external tool for conversion." % texture_name)
        # else:
    return img
