"""Mechanisms checks in the Rig Validator (and so the Task Board), spec §8."""
from boneforge.mechanisms import build, checks, records


def rig_checks(arm_obj):
    """[(status, message, bone)]: record checks plus what only the armature can show."""
    if not records.has_records(arm_obj.data):
        return []                                      # not a Mechanisms rig: leave its drivers and constraints alone
    out = checks.record_checks(records.to_model(arm_obj))
    ad = arm_obj.animation_data
    drivers = list(ad.drivers) if ad is not None else []
    for fc in drivers:
        if fc.driver.type == 'SCRIPTED' and not fc.driver.is_simple_expression:
            out.append(("fail", f"The driver on {fc.data_path} needs Python ('Auto Run Python Scripts'); "
                                "use a simple expression so the rig works without scripts.", ""))
    for (rid, role), name in build.bone_tags(arm_obj).items():
        if role != "DEF":
            continue
        extra = [c.name for c in arm_obj.pose.bones[name].constraints if build.tag_of(c.name) is None]
        if extra:
            out.append(("warn", f"{name} is moved by constraints BoneCraft did not add ({', '.join(extra)}); "
                                "engines receive DEF bones.", name))
        if any(fc.data_path.startswith(f'pose.bones["{name}"]') for fc in drivers):
            out.append(("warn", f"{name} has drivers BoneCraft did not add; engines receive DEF bones.", name))
    return out


def check_mechanisms(armature_obj):
    from boneforge.advanced_rigging.rig_validator import ValidationResult
    found = rig_checks(armature_obj)
    results = [ValidationResult(check_name="mechanisms", status=s, affected_bone=b, message=m) for s, m, b in found]
    if not results and records.has_records(armature_obj.data):
        results.append(ValidationResult(check_name="mechanisms", status="pass", message="Mechanisms: no problems found."))
    return results


def register():
    from boneforge.advanced_rigging import rig_validator
    rig_validator.register_custom_check("mechanisms", check_mechanisms)


def unregister():
    try:
        from boneforge.advanced_rigging import rig_validator
        rig_validator._custom_checks.pop("mechanisms", None)
    except ImportError:
        pass
