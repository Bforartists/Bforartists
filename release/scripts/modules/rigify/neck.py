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
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from rigify import bone_class_instance, copy_bone_simple
from rna_prop_ui import rna_idprop_ui_prop_get


def metarig_template():
    bpy.ops.object.mode_set(mode='EDIT')
    obj = bpy.context.object
    arm = obj.data
    bone = arm.edit_bones.new('body')
    bone.head[:] = -0.0000, -0.2771, -1.3345
    bone.tail[:] = -0.0000, -0.1708, -0.3984
    bone.roll = 0.0000
    bone.connected = False
    bone = arm.edit_bones.new('head')
    bone.head[:] = -0.0000, -0.1708, -0.1984
    bone.tail[:] = 0.0000, -0.1708, 1.6016
    bone.roll = -0.0000
    bone.connected = False
    bone.parent = arm.edit_bones['body']
    bone = arm.edit_bones.new('neck.01')
    bone.head[:] = 0.0000, -0.1708, -0.1984
    bone.tail[:] = -0.0000, -0.0994, 0.1470
    bone.roll = -0.0000
    bone.connected = False
    bone.parent = arm.edit_bones['head']
    bone = arm.edit_bones.new('neck.02')
    bone.head[:] = -0.0000, -0.0994, 0.1470
    bone.tail[:] = 0.0000, -0.2428, 0.5162
    bone.roll = -0.0000
    bone.connected = True
    bone.parent = arm.edit_bones['neck.01']
    bone = arm.edit_bones.new('neck.03')
    bone.head[:] = 0.0000, -0.2428, 0.5162
    bone.tail[:] = 0.0000, -0.4190, 0.8722
    bone.roll = -0.0000
    bone.connected = True
    bone.parent = arm.edit_bones['neck.02']
    bone = arm.edit_bones.new('neck.04')
    bone.head[:] = 0.0000, -0.4190, 0.8722
    bone.tail[:] = 0.0000, -0.5111, 1.1956
    bone.roll = 0.0000
    bone.connected = True
    bone.parent = arm.edit_bones['neck.03']
    bone = arm.edit_bones.new('neck.05')
    bone.head[:] = 0.0000, -0.5111, 1.1956
    bone.tail[:] = 0.0000, -0.5391, 1.6081
    bone.roll = 0.0000
    bone.connected = True
    bone.parent = arm.edit_bones['neck.04']

    bpy.ops.object.mode_set(mode='OBJECT')
    pbone = obj.pose.bones['head']
    pbone['type'] = 'neck'


def main(obj, orig_bone_name):
    from Mathutils import Vector
    
    arm = obj.data

    # Initialize container classes for convenience
    mt = bone_class_instance(obj, ["body", "head"]) # meta
    mt.head = orig_bone_name
    mt.update()
    mt.body = mt.head_e.parent.name
    mt.update()

    # child chain of the 'head'
    children = mt.head_e.children
    if len(children) != 1:
        print("expected the head to have only 1 child.")

    child = children[0]
    neck_chain = [child] + child.children_recursive_basename
    neck_chain = [child.name for child in neck_chain]
    
    mt_chain = bone_class_instance(obj, [("neck_%.2d" % (i + 1)) for i in range(len(neck_chain))]) # 99 bones enough eh?
    for i, child_name in enumerate(neck_chain):
        setattr(mt_chain, ("neck_%.2d" % (i + 1)), child_name)
    mt_chain.update()

    neck_chain_basename = mt_chain.neck_01_e.basename
    neck_chain_segment_length = mt_chain.neck_01_e.length
    
    ex = bone_class_instance(obj, ["body", "head", "head_hinge","neck_socket"]) # hinge & extras
    
    # Add the head hinge at the bodys location, becomes the parent of the original head
    
    
    # Copy the head bone and offset
    ex.head_e = copy_bone_simple(arm, mt.head, "MCH_%s" % mt.head, parent=True)
    ex.head = ex.head_e.name
    # offset
    head_length = ex.head_e.length
    ex.head_e.head.y += head_length / 2.0
    ex.head_e.tail.y += head_length / 2.0
    
    # Yes, use the body bone but call it a head hinge
    ex.head_hinge_e = copy_bone_simple(arm, mt.body, "MCH_%s_hinge" % mt.head, parent=True)
    ex.head_hinge = ex.head_hinge_e.name
    ex.head_hinge_e.head.y += head_length / 4.0
    ex.head_hinge_e.tail.y += head_length / 4.0

    # reparent the head, assume its not connected
    mt.head_e.parent = ex.head_hinge_e
    
    # Insert the neck socket, the head copys this loation
    ex.neck_socket_e = arm.edit_bones.new("MCH-%s_socked" % neck_chain_basename)
    ex.neck_socket = ex.neck_socket_e.name
    ex.neck_socket_e.parent = mt.body_e
    ex.neck_socket_e.head = mt.head_e.head
    ex.neck_socket_e.tail = mt.head_e.head - Vector(0.0, neck_chain_segment_length / 2.0, 0.0)
    ex.neck_socket_e.roll = 0.0
    
    # offset the head, not really needed since it has a copyloc constraint
    mt.head_e.head.y += head_length / 4.0
    mt.head_e.tail.y += head_length / 4.0

    for i in range(len(neck_chain)):
        neck_e = getattr(mt_chain, "neck_%.2d_e" % (i + 1))
        
        # dont store parent names, re-reference as each chain bones parent.
        neck_e_parent = arm.edit_bones.new("MCH-rot_%s" % neck_e.name)
        neck_e_parent.head = neck_e.head
        neck_e_parent.tail = neck_e.head + Vector(0.0, 0.0, neck_chain_segment_length / 2.0)
        neck_e_parent.roll = 0.0
        
        orig_parent = neck_e.parent
        neck_e.connected = False
        neck_e.parent = neck_e_parent
        neck_e_parent.connected = False
        
        if i == 0:
            neck_e_parent.parent = mt.body_e
        else:
            neck_e_parent.parent = orig_parent
    
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    mt.update()
    mt_chain.update()
    ex.update()
    
    # Simple one off constraints, no drivers
    con = mt.head_p.constraints.new('COPY_LOCATION')
    con.target = obj
    con.subtarget = ex.neck_socket
    
    con = ex.head_p.constraints.new('COPY_ROTATION')
    con.target = obj
    con.subtarget = mt.head
    
    # driven hinge
    prop = rna_idprop_ui_prop_get(mt.head_p, "hinge", create=True)
    mt.head_p["hinge"] = 0.0
    prop["soft_min"] = 0.0
    prop["soft_max"] = 1.0
    
    con = ex.head_hinge_p.constraints.new('COPY_ROTATION')
    con.name = "hinge"
    con.target = obj
    con.subtarget = mt.body
    
    # add driver
    hinge_driver_path = mt.head_p.path_to_id() + '["hinge"]'
    
    fcurve = con.driver_add("influence", 0)
    driver = fcurve.driver
    tar = driver.targets.new()
    driver.type = 'AVERAGE'
    tar.name = "var"
    tar.id_type = 'OBJECT'
    tar.id = obj
    tar.rna_path = hinge_driver_path
    
    #mod = fcurve_driver.modifiers.new('GENERATOR')
    mod = fcurve.modifiers[0]
    mod.poly_order = 1
    mod.coefficients[0] = 1.0
    mod.coefficients[1] = -1.0
    
    head_driver_path = mt.head_p.path_to_id()
    
    # b01/max(0.001,b01+b02+b03+b04+b05)
    target_names = [("b%.2d" % (i + 1)) for i in range(len(neck_chain))]
    expression_suffix = "/max(0.001,%s)" % "+".join(target_names)
    
    
    for i in range(len(neck_chain)):
        neck_p = getattr(mt_chain, "neck_%.2d_p" % (i + 1))
        neck_p.lock_location = True, True, True
        neck_p.lock_location = True, True, True
        neck_p.lock_rotations_4d = True
        
        # Add bend prop
        prop_name = "bend_%.2d" % (i + 1)
        prop = rna_idprop_ui_prop_get(mt.head_p, prop_name, create=True)
        mt.head_p[prop_name] = 1.0
        prop["soft_min"] = 0.0
        prop["soft_max"] = 1.0
        
        # add parent constraint
        neck_p_parent = neck_p.parent
        
        # add constraint
        con = neck_p_parent.constraints.new('COPY_ROTATION')
        con.name = "Copy Rotation"
        con.target = obj
        con.subtarget = ex.head
        con.owner_space = 'LOCAL'
        con.target_space = 'LOCAL'
        
        fcurve = con.driver_add("influence", 0)
        driver = fcurve.driver
        driver.type = 'SCRIPTED'
        # b01/max(0.001,b01+b02+b03+b04+b05)
        driver.expression = target_names[i] + expression_suffix
        fcurve.modifiers.remove(0) # grr dont need a modifier

        for j in range(len(neck_chain)):
            tar = driver.targets.new()
            tar.name = target_names[j]
            tar.id_type = 'OBJECT'
            tar.id = obj
            tar.rna_path = head_driver_path + ('["bend_%.2d"]' % (j + 1))
