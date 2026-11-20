"""Face component: eyes (aim), lids, brows, jaw, and lips with soft/sticky
behaviour. Optional muzzle for creatures.

Plan-computed like the other components so the structure (bones, constraints,
drivers, props, widgets) is unit-testable headlessly; the driven deform is
verified in-host. Front of the face is -Y; everything parents off ``head``.

Clean-room: original BoneCraft-native facial layout and a first-principles
soft/sticky-lips model (the lower lip follows the jaw by ``soft_lips``, reduced
toward zero as ``sticky_lips`` rises so the lips stay sealed while the jaw
opens). No third-party face rig is referenced.
"""
from . import sided

PROPS_BONE = "face_props"
_HEAD = "head"


def build_face(plan, head=_HEAD, muzzle=False):
    # hidden property holder for the soft/sticky-lips controls
    plan.add_bone(PROPS_BONE, (0.0, 0.10, 1.66), (0.0, 0.10, 1.70),
                  parent=head, collection="MCH")
    plan.add_prop(PROPS_BONE, "soft_lips", default=0.6, soft_min=0.0,
                  soft_max=1.0, description="Lower lip follow on jaw open")
    plan.add_prop(PROPS_BONE, "sticky_lips", default=0.0, soft_min=0.0,
                  soft_max=1.0, description="Keep lips sealed as jaw opens")

    # -- jaw (deform control with an open/close limit) --
    plan.add_bone("jaw", (0.0, -0.02, 1.61), (0.0, -0.10, 1.55),
                  parent=head, deform=True, collection="Face")
    plan.add_widget("jaw", "jaw", "face", 1.0)
    plan.add_constraint("jaw", "LIMIT_ROTATION", "BF_JAW_LIMIT",
                        params={"use_limit_x": True, "min_x": -0.7,
                                "max_x": 0.15, "owner_space": "LOCAL"})

    # -- lips --
    plan.add_bone("lip.upper", (0.0, -0.105, 1.585), (0.0, -0.107, 1.583),
                  parent=head, deform=True, collection="Face")
    plan.add_widget("lip.upper", "lip", "face", 0.6)
    # lower lip follows the jaw by a driven amount (soft + sticky)
    plan.add_bone("lip.lower", (0.0, -0.105, 1.575), (0.0, -0.107, 1.573),
                  parent=head, deform=True, collection="Face")
    plan.add_widget("lip.lower", "lip", "face", 0.6)
    plan.add_constraint("lip.lower", "COPY_ROTATION", "BF_LIP_FOLLOW",
                        subtarget="jaw", params={"influence": 0.0})
    plan.add_driver("lip.lower", 'constraints["BF_LIP_FOLLOW"].influence',
                    index=-1, expression="s * (1.0 - k)",
                    variables=[
                        {"name": "s", "bone_path":
                         'pose.bones["%s"]["soft_lips"]' % PROPS_BONE},
                        {"name": "k", "bone_path":
                         'pose.bones["%s"]["sticky_lips"]' % PROPS_BONE},
                    ])
    for side in ("L", "R"):
        x = 0.025 if side == "L" else -0.025
        corner = sided("lip.corner", side)
        plan.add_bone(corner, (x, -0.10, 1.58), (x * 1.1, -0.10, 1.58),
                      parent=head, deform=True, collection="Face")
        plan.add_widget(corner, "circle_small", "face", 0.5)

    # -- eyes (aim via damped track to an eye target) --
    plan.add_bone("eye_master", (0.0, -0.30, 1.665), (0.0, -0.33, 1.665),
                  parent=head, collection="Face")
    plan.add_widget("eye_master", "circle", "face", 1.2)
    for side in ("L", "R"):
        x = 0.035 if side == "L" else -0.035
        eye = sided("eye", side)
        target = sided("eye.ik", side)
        plan.add_bone(target, (x, -0.30, 1.665), (x, -0.33, 1.665),
                      parent="eye_master", collection="Face")
        plan.add_widget(target, "eye_target", "face", 0.8)
        plan.add_bone(eye, (x, -0.085, 1.665), (x, -0.105, 1.665),
                      parent=head, deform=True, collection="Face")
        plan.add_widget(eye, "sphere", "face", 0.5)
        plan.add_constraint(eye, "DAMPED_TRACK", "BF_EYE_AIM",
                            subtarget=target)
        # lids + brow per side
        for which, dz in (("upper", 0.012), ("lower", -0.012)):
            lid = sided("lid.%s" % which, side)
            plan.add_bone(lid, (x, -0.10, 1.665 + dz), (x, -0.105, 1.665 + dz),
                          parent=head, deform=True, collection="Face")
            plan.add_widget(lid, "eyelid", "face", 0.5)
        brow = sided("brow", side)
        plan.add_bone(brow, (x, -0.095, 1.69), (x, -0.10, 1.69),
                      parent=head, deform=True, collection="Face")
        plan.add_widget(brow, "brow", "face", 0.6)
    plan.add_bone("brow.C", (0.0, -0.10, 1.695), (0.0, -0.105, 1.695),
                  parent=head, deform=True, collection="Face")
    plan.add_widget("brow.C", "brow", "face", 0.5)

    if muzzle:
        plan.add_bone("muzzle", (0.0, -0.13, 1.62), (0.0, -0.20, 1.60),
                      parent=head, deform=True, collection="Face")
        plan.add_widget("muzzle", "circle", "face", 1.0)
    return PROPS_BONE
