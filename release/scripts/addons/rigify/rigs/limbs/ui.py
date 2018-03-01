script_arm = """
controls = [%s]
tweaks   = [%s]
ik_ctrl  = [%s]
fk_ctrl  = '%s'
parent   = '%s'
hand_fk   = '%s'
pole = '%s'

# IK/FK Switch on all Control Bones
if is_selected( controls ):
    layout.prop( pose_bones[parent], '["%s"]', slider = True )
    props = layout.operator("pose.rigify_arm_fk2ik_" + rig_id, text="Snap FK->IK (" + fk_ctrl + ")")
    props.uarm_fk = controls[1]
    props.farm_fk = controls[2]
    props.hand_fk = controls[3]
    props.uarm_ik = controls[0]
    props.farm_ik = ik_ctrl[1]
    props.hand_ik = controls[4]
    props = layout.operator("pose.rigify_arm_ik2fk_" + rig_id, text="Snap IK->FK (" + fk_ctrl + ")")
    props.uarm_fk = controls[1]
    props.farm_fk = controls[2]
    props.hand_fk = controls[3]
    props.uarm_ik = controls[0]
    props.farm_ik = ik_ctrl[1]
    props.hand_ik = controls[4]
    props.pole = pole
    props.main_parent = parent
    props = layout.operator("pose.rigify_rot2pole_" + rig_id, text="Switch Rotation-Pole")
    props.bone_name = controls[1]
    props.limb_type = "arm"
    props.controls = str(controls)
    props.ik_ctrl = str(ik_ctrl)
    props.fk_ctrl = str(fk_ctrl)
    props.parent = str(parent)
    props.pole = str(pole)


# BBone rubber hose on each Respective Tweak
for t in tweaks:
    if is_selected( t ):
        layout.prop( pose_bones[ t ], '["%s"]', slider = True )

# IK Stretch and pole_vector on IK Control bone
if is_selected( ik_ctrl ) or is_selected(parent):
    layout.prop( pose_bones[ parent ], '["%s"]', slider = True )
    layout.prop( pose_bones[ parent ], '["%s"]')

# FK limb follow
if is_selected( fk_ctrl ) or is_selected(parent):
    layout.prop( pose_bones[ parent ], '["%s"]', slider = True )
"""

script_leg = """
controls = [%s]
tweaks   = [%s]
ik_ctrl  = [%s]
fk_ctrl  = '%s'
parent   = '%s'
foot_fk = '%s'
pole = '%s'

# IK/FK Switch on all Control Bones
if is_selected( controls ):
    layout.prop( pose_bones[parent], '["%s"]', slider = True )
    props = layout.operator("pose.rigify_leg_fk2ik_" + rig_id, text="Snap FK->IK (" + fk_ctrl + ")")
    props.thigh_fk = controls[1]
    props.shin_fk  = controls[2]
    props.foot_fk  = controls[3]
    props.mfoot_fk = controls[7]
    props.thigh_ik = controls[0]
    props.shin_ik  = ik_ctrl[1]
    props.foot_ik = ik_ctrl[2]
    props.mfoot_ik = ik_ctrl[2]
    props = layout.operator("pose.rigify_leg_ik2fk_" + rig_id, text="Snap IK->FK (" + fk_ctrl + ")")
    props.thigh_fk  = controls[1]
    props.shin_fk   = controls[2]
    props.foot_fk  = controls[3]
    props.mfoot_fk  = controls[7]
    props.thigh_ik  = controls[0]
    props.shin_ik   = ik_ctrl[1]
    props.foot_ik   = controls[6]
    props.pole      = pole
    props.footroll  = controls[5]
    props.mfoot_ik  = ik_ctrl[2]
    props.main_parent = parent
    props = layout.operator("pose.rigify_rot2pole_" + rig_id, text="Toggle Rotation and Pole")
    props.bone_name = controls[1]
    props.limb_type = "leg"
    props.controls = str(controls)
    props.ik_ctrl = str(ik_ctrl)
    props.fk_ctrl = str(fk_ctrl)
    props.parent = str(parent)
    props.pole = str(pole)

# BBone rubber hose on each Respective Tweak
for t in tweaks:
    if is_selected( t ):
        layout.prop( pose_bones[ t ], '["%s"]', slider = True )

# IK Stretch and pole_vector on IK Control bone
if is_selected( ik_ctrl ) or is_selected(parent):
    layout.prop( pose_bones[ parent ], '["%s"]', slider = True )
    layout.prop( pose_bones[ parent ], '["%s"]')

# FK limb follow
if is_selected( fk_ctrl ) or is_selected(parent):
    layout.prop( pose_bones[ parent ], '["%s"]', slider = True )
"""

def create_script( bones, limb_type=None):
    # All ctrls have IK/FK switch
    controls = [bones['ik']['ctrl']['limb']] + bones['fk']['ctrl']
    controls += bones['ik']['ctrl']['terminal']
    controls += [bones['fk']['mch']]
    controls += [bones['main_parent']]

    controls_string = ", ".join(["'" + x + "'" for x in controls])

    # All tweaks have their own bbone prop
    tweaks        = bones['tweak']['ctrl'][1:-1]
    tweaks_string = ", ".join(["'" + x + "'" for x in tweaks])

    # IK ctrl has IK stretch
    ik_ctrl = [ bones['ik']['ctrl']['terminal'][-1] ]
    ik_ctrl += [ bones['ik']['mch_ik'] ]
    ik_ctrl += [ bones['ik']['mch_target'] ]

    ik_ctrl_string = ", ".join(["'" + x + "'" for x in ik_ctrl])

    if 'ik_target' in bones['ik']['ctrl'].keys():
        pole = bones['ik']['ctrl']['ik_target']
    else:
        pole = ''

    if limb_type == 'arm':
        return script_arm % (
            controls_string,
            tweaks_string,
            ik_ctrl_string,
            bones['fk']['ctrl'][0],
            bones['main_parent'],
            bones['fk']['ctrl'][-1],
            pole,
            'IK_FK',
            'rubber_tweak',
            'IK_Stretch',
            'pole_vector',
            'FK_limb_follow'
        )

    elif limb_type == 'leg':
        return script_leg % (
            controls_string,
            tweaks_string,
            ik_ctrl_string,
            bones['fk']['ctrl'][0],
            bones['main_parent'],
            bones['fk']['ctrl'][-1],
            pole,
            'IK_FK',
            'rubber_tweak',
            'IK_Stretch',
            'pole_vector',
            'FK_limb_follow'
        )

    elif limb_type == 'paw':
        return script_leg % (
            controls_string,
            tweaks_string,
            ik_ctrl_string,
            bones['fk']['ctrl'][0],
            bones['main_parent'],
            bones['fk']['ctrl'][-1],
            pole,
            'IK_FK',
            'rubber_tweak',
            'IK_Stretch',
            'pole_vector',
            'FK_limb_follow'
        )
