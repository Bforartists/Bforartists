script = """
controls = [%s]
tweaks   = [%s]
ik_ctrl  = '%s'
fk_ctrl  = '%s'
parent   = '%s'

# IK/FK Switch on all Control Bones
if is_selected( controls ):
    layout.prop( pose_bones[ parent ], '["%s"]', slider = True )

# BBone rubber hose on each Respective Tweak
for t in tweaks:
    if is_selected( t ):
        layout.prop( pose_bones[ t ], '["%s"]', slider = True )
        
# IK Stretch on IK Control bone
if is_selected( ik_ctrl ):
    layout.prop( pose_bones[ parent ], '["%s"]', slider = True )
    
# FK limb follow
if is_selected( fk_ctrl ):
    layout.prop( pose_bones[ parent ], '["%s"]', slider = True )
""" 

def create_script( bones):
    # All ctrls have IK/FK switch
    controls =  [ bones['ik']['ctrl']['limb'] ] + bones['fk']['ctrl']
    controls += bones['ik']['ctrl']['terminal']

    controls_string = ", ".join(["'" + x + "'" for x in controls])

    # All tweaks have their own bbone prop
    tweaks        = bones['tweak']['ctrl'][1:-1]
    tweaks_string = ", ".join(["'" + x + "'" for x in tweaks])
    
    # IK ctrl has IK stretch 
    ik_ctrl = bones['ik']['ctrl']['terminal'][-1]

    return script % ( 
        controls_string, 
        tweaks_string, 
        ik_ctrl,
        bones['fk']['ctrl'][0],
        bones['parent'],
        'IK/FK',
        'rubber_tweak',
        'IK_Strertch',
        'FK_limb_follow'
    )

