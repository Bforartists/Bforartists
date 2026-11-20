"""Native RNA regression for mechanism forms (run with Bforartists --background).

Seed once with the published pre-change module, then verify with the new source::

    bforartists --background --factory-startup --python-exit-code 1 --python \
        tests/python/bfa_toolkit_mechanism_forms.py -- --module-root <bonecraft> \
        --fixtures <temporary-directory> --mode seed-legacy

Repeat with --mode verify and the fixed module root on each supported host.
Use an isolated BLENDER_USER_RESOURCES directory; this script writes only to
--fixtures. It registers the real records and operators, without mocking bpy.
"""
import argparse
import json
import math
from pathlib import Path
import shutil
import sys

import addon_utils
import bpy


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--module-root", required=True, type=Path)
    parser.add_argument("--fixtures", required=True, type=Path)
    parser.add_argument("--mode", choices=("seed-legacy", "verify"), required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def load_records(root):
    # A default-module host may already have a different BoneCraft registered.
    if "boneforge" in bpy.context.preferences.addons:
        addon_utils.disable("boneforge", default_set=False)
    for name in list(sys.modules):
        if name == "boneforge" or name.startswith("boneforge."):
            del sys.modules[name]
    sys.path.insert(0, str(root.resolve()))
    from boneforge.mechanisms import build, model, ops, records
    assert Path(records.__file__).resolve().is_relative_to(root.resolve())
    print("FORM_TEST_REGISTRATION_START", flush=True)
    records.register()
    ops.register()
    return build, model, records


def armature(name):
    data = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return ob


def seed_legacy(fixtures):
    ob = armature("LegacyForms")
    form = ob.data.bonecraft_mech.forms.add()
    form.name = "Legacy"
    value = form.values.add()
    value.key, value.value = "hinge", 37.5
    value = form.values.add()
    value.key, value.value = "slide", -2.25
    defaults = ob.data.bonecraft_mech.forms.add()
    defaults.name = "Defaults"
    defaults.values.add()  # Unset RNA fields must still read as "" and 0.0.
    bpy.ops.wm.save_as_mainfile(filepath=str(fixtures / "legacy-forms.blend"))


def model_forms(records, ob):
    return {form.name: form.values for form in records.to_model(ob).forms}


def check_legacy(records, ob):
    form = ob.data.bonecraft_mech.forms["Legacy"]
    before = form.id_properties_ensure().to_dict()
    assert records.form_values(form) == {"hinge": 37.5, "slide": -2.25}
    assert model_forms(records, ob)["Legacy"] == {"hinge": 37.5, "slide": -2.25}
    assert records.form_values(ob.data.bonecraft_mech.forms["Defaults"]) == {"": 0.0}
    assert form.id_properties_ensure().to_dict() == before, "Reading mutated old form storage"
    assert "control_values" not in form, "Legacy reads initialized modern storage"


def add_value(form, key, value):
    item = form.control_values.add()
    item.key, item.value = key, value


def verify(build, model, records, fixtures):
    assert "control_values" in records.BC_PG_MechForm.bl_rna.properties
    assert "values" not in records.BC_PG_MechForm.bl_rna.properties
    legacy_file = fixtures / "legacy-forms.blend"
    assert legacy_file.is_file(), "Run seed-legacy against the original module first"
    bpy.ops.wm.open_mainfile(filepath=str(legacy_file), load_ui=False)
    ob = bpy.data.objects["LegacyForms"]
    check_legacy(records, ob)

    # Appending and linking must read the same armature-carried records without
    # migrating data in a draw callback or requiring a writable linked library.
    library_file = fixtures / "library-forms.blend"
    shutil.copyfile(legacy_file, library_file)
    for linked in (False, True):
        with bpy.data.libraries.load(str(library_file), link=linked) as (source, dest):
            dest.objects = [name for name in source.objects if name == "LegacyForms"]
        loaded = dest.objects[0]
        assert (loaded.library is not None) == linked
        check_legacy(records, loaded)

    forms = ob.data.bonecraft_mech.forms
    modern = forms.add()
    modern.name = "Modern"
    add_value(modern, "hinge", 12.5)
    add_value(modern, "slide", 1.75)
    assert records.form_values(modern) == {"hinge": 12.5, "slide": 1.75}
    conflict = forms.add()
    conflict.name = "Conflict"
    conflict["values"] = forms["Legacy"].get("values")
    add_value(conflict, "hinge", -5.0)
    before = conflict.id_properties_ensure().to_dict()
    assert records.form_values(conflict) == {"hinge": -5.0}
    assert conflict.id_properties_ensure().to_dict() == before
    empty = forms.add()
    empty.name = "EmptyModern"
    empty["values"] = forms["Legacy"].get("values")
    add_value(empty, "temporary", 1.0)
    empty.control_values.clear()
    assert "control_values" in empty, "Native empty collection fixture lost its stored key"
    assert records.form_values(empty) == {}, "Empty modern collection exposed stale legacy values"
    untouched = forms.add()
    untouched.name = "Untouched"
    assert records.form_values(untouched) == {}
    assert "control_values" not in untouched

    # Real Blender pose channels and registered operators exercise capture/apply.
    # Only the small two-control fixture is constructed directly, not a mock RNA.
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for name in ("HingeHandle", "SlideHandle"):
        bone = ob.data.edit_bones.new(name)
        bone.head, bone.tail = (0, 0, 0), (0, 1, 0)
    bpy.ops.object.mode_set(mode='OBJECT')
    for name, cid in (("HingeHandle", "hinge"), ("SlideHandle", "slide")):
        bone = ob.pose.bones[name]
        bone["bc_mech_id"], bone["bc_mech_role"] = cid, "CTRL"
        records.add(ob.data, model.Mechanism(cid, "HINGE" if cid == "hinge" else "SLIDE", cid))
    hinge, slide = ob.pose.bones["HingeHandle"], ob.pose.bones["SlideHandle"]
    hinge.rotation_euler.x, slide.location.y = math.radians(22.5), 3.25
    assert bpy.ops.boneforge.mech_save_form(name="Captured") == {'FINISHED'}
    captured = forms["Captured"]
    assert abs(records.form_values(captured)["hinge"] - 22.5) < 1e-5
    assert records.form_values(captured)["slide"] == 3.25
    hinge.rotation_euler.x, slide.location.y = 0, 0
    assert bpy.ops.boneforge.mech_go_to_form(name="Captured") == {'FINISHED'}
    assert abs(math.degrees(hinge.rotation_euler.x) - 22.5) < 1e-5
    assert slide.location.y == 3.25
    assert bpy.ops.boneforge.mech_go_to_form(name="Legacy", insert_keys=True) == {'FINISHED'}
    assert abs(math.degrees(hinge.rotation_euler.x) - 37.5) < 1e-5
    assert slide.location.y == -2.25
    assert ob.animation_data and ob.animation_data.action, "Insert Keys did not create an Action"

    # Overwrite is the sole migration point. Other old forms stay byte-identical.
    old_defaults = forms["Defaults"].id_properties_ensure().to_dict()
    assert bpy.ops.boneforge.mech_save_form(name="Legacy") == {'FINISHED'}
    assert "values" not in forms["Legacy"]
    assert "control_values" in forms["Legacy"]
    assert forms["Defaults"].id_properties_ensure().to_dict() == old_defaults
    with records.quiet():
        ob.data.bonecraft_mech.mechanisms.clear()
    records.add(ob.data, model.Part("empty", "Part with no controls"))
    assert bpy.ops.boneforge.mech_save_form(name="Conflict") == {'FINISHED'}
    assert records.form_values(forms["Conflict"]) == {}
    assert "values" not in forms["Conflict"]

    expected = model_forms(records, ob)
    output = fixtures / ("roundtrip-" + bpy.app.version_string.replace(" ", "_") + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    bpy.ops.wm.open_mainfile(filepath=str(output), load_ui=False)
    restored = bpy.data.objects["LegacyForms"]
    assert model_forms(records, restored) == expected
    assert "values" not in restored.data.bonecraft_mech.forms["Legacy"]
    assert "values" in restored.data.bonecraft_mech.forms["Defaults"]
    return ["native RNA", "legacy file load", "append", "link", "read-only access",
            "modern precedence", "empty precedence", "operator capture", "operator apply",
            "legacy apply with key insertion", "explicit overwrite", "empty overwrite", "file roundtrip"]


def main():
    args = arguments()
    args.fixtures.mkdir(parents=True, exist_ok=True)
    build, model, records = load_records(args.module_root)
    if args.mode == "seed-legacy":
        seed_legacy(args.fixtures)
        checks = ["original RNA fixture saved"]
    else:
        checks = verify(build, model, records, args.fixtures)
    print("BONECRAFT_FORM_RESULT " + json.dumps({"passed": True, "mode": args.mode,
          "host": bpy.app.version_string, "module": records.__file__, "checks": checks}), flush=True)


if __name__ == "__main__":
    main()
