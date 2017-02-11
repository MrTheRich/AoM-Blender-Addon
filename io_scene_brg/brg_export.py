import bpy
import os
import mathutils
import bmesh
import math
import struct
from .brg_util import *

def start(context, filepath):
    file = File(file_path, 'wb')
