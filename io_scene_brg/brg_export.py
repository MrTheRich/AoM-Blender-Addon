import bpy
import os
import mathutils
import bmesh
import math
import struct
from enum import Enum
from .brg_util import *

def start(context, filepath, addon_prefs):
    file = File(file_path, 'wb')

    file.close()
