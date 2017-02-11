import struct
from struct import pack,unpack

'''Quick functions for helping read brg files'''

## Reading util
class File:
    file_object = None
    name = ""

    def __init__(self, file_path, rw):
        self.file_object = open(file_path, rw)
        self.name = file_object.name

    def read(self, length = 1):
        '''read string with length from file'''
        return self.file_object.read(length).decode("utf-8")

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

    def read_float(self, endian = '<'):
        '''read floating point number from file'''
        data = unpack(endian+'f', self.file_object.read(4))[0]
        return data

    def read_half(self, endian = '<'):
        '''read half floating number from file'''
        s =  self.file_object.read(2) + "\x00\x00"
        data = unpack(endian+'f', s)[0]
        return data
