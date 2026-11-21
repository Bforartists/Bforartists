"""One planner function per mechanism type: fn(plan, mech, rig). POST runs after every type."""
from boneforge.mechanisms.recipes import follow, gear, hinge, piston, sequence, slide, telescope

RECIPES = {"HINGE": hinge.plan, "SLIDE": slide.plan, "TELESCOPE": telescope.plan,
           "PISTON": piston.plan, "GEAR": gear.plan, "FOLLOW": follow.plan}
POST = (gear.plan_drivers, sequence.plan_all)
