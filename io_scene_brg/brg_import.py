import bpy
import os
import mathutils
import bmesh
import math
import struct
from .brg_util import *

def start(context, file_path):
    file = File(file_path, 'rb')
    print("Importing Age of Mythology Model " + file.name)
    print("File Header:", file.read(4))
