"""Foot-roll component: heel/ball MCH bones driven by a foot_roll property."""
from . import BoneDef, ConstraintDef, PropDef, DriverDef, sided

PROPS_BONE = "properties"


def build_foot_roll(plan, side, props_bone=PROPS_BONE):
    sgn = 1.0 if side == "L" else -1.0
    x = 0.12 * sgn
    ik_ctrl = sided("shin.ik", side)        # leg ik control (foot target)
    heel = sided("roll_heel", side)
    ball = sided("roll_ball", side)
    plan.add_bone(heel, (x, -0.06, 0.0), (x, -0.16, 0.0), parent=ik_ctrl,
                  collection="MCH")
    plan.add_bone(ball, (x, 0.18, 0.0), (x, 0.30, 0.0), parent=heel,
                  collection="MCH")
    plan.add_prop(props_bone, f"foot_roll-{side}", default=0.0,
                  soft_min=-1.0, soft_max=1.0,
                  description=f"Foot roll for {side} (-1 heel .. +1 toe)")
    # heel rotates on negative roll, ball (toe) on positive roll
    plan.add_constraint(heel, "LIMIT_ROTATION", f"BF_ROLL_LIM-heel-{side}",
                        params={"use_limit_x": True, "min_x": -1.2, "max_x": 0.0})
    plan.add_constraint(ball, "LIMIT_ROTATION", f"BF_ROLL_LIM-ball-{side}",
                        params={"use_limit_x": True, "min_x": 0.0, "max_x": 1.2})
    plan.add_driver(heel, "rotation_euler", index=0,
                    expression="min(0.0, v) * 1.2",
                    variables=[{"name": "v", "bone_path":
                                f'pose.bones["{props_bone}"]["foot_roll-{side}"]'}])
    plan.add_driver(ball, "rotation_euler", index=0,
                    expression="max(0.0, v) * 1.2",
                    variables=[{"name": "v", "bone_path":
                                f'pose.bones["{props_bone}"]["foot_roll-{side}"]'}])
    return [heel, ball]
