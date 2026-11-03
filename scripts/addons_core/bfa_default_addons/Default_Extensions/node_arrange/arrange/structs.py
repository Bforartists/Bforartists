# SPDX-License-Identifier: GPL-2.0-or-later

import ctypes
import platform

import bpy


class bNodeStack(ctypes.Structure):
    vec: ctypes.c_float * 4
    min: ctypes.c_float
    max: ctypes.c_float
    data: ctypes.c_void_p
    hasinput: ctypes.c_short
    hasoutput: ctypes.c_short
    datatype: ctypes.c_short
    sockettype: ctypes.c_short
    is_copy: ctypes.c_short
    external: ctypes.c_short
    _pad: ctypes.c_char * 4


class bNodeSocketRuntime(ctypes.Structure):
    if platform.system() == 'Windows':
        _pad0: ctypes.c_char * 8
    declaration: ctypes.c_void_p
    if bpy.app.version >= (5, 2, 0):
        identifier_ustr: ctypes.c_char * 8
    changed_flag: ctypes.c_uint32
    total_inputs: ctypes.c_short
    if bpy.app.version >= (5, 0, 0):
        inferred_structure_type: ctypes.c_int8
    _pad1: ctypes.c_byte * 1
    location: ctypes.c_float * 2


class bNodeSocket(ctypes.Structure):
    next: ctypes.c_void_p
    prev: ctypes.c_void_p
    prop: ctypes.c_void_p
    identifier: ctypes.c_char * 64
    name: ctypes.c_char * 64
    storage: ctypes.c_void_p
    type: ctypes.c_short
    flag: ctypes.c_short
    limit: ctypes.c_short
    in_out: ctypes.c_short
    typeinfo: ctypes.c_void_p
    idname: ctypes.c_char * 64
    default_value: ctypes.c_void_p
    if bpy.app.version >= (5, 0, 0):
        stack_index: ctypes.c_int
    else:
        stack_index: ctypes.c_short
    display_shape: ctypes.c_char
    attribute_domain: ctypes.c_char
    if bpy.app.version >= (5, 0, 0):
        _pad: ctypes.c_char * 2
    else:
        _pad: ctypes.c_char * 4
    label: ctypes.c_char * 64
    description: ctypes.c_char * 64
    if bpy.app.version < (5, 1, 0):
        short_label: ctypes.c_char * 64
    default_attribute_name: ctypes.POINTER(ctypes.c_char)
    own_index: ctypes.c_int
    to_index: ctypes.c_int
    link: ctypes.c_void_p
    ns: bNodeStack
    runtime: ctypes.POINTER(bNodeSocketRuntime)


for cls in (bNodeStack, bNodeSocketRuntime, bNodeSocket):
    cls._fields_ = list(cls.__annotations__.items())
