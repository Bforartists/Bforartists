"""VRM import operator — wraps upstream + runs BoneCraft post-import passes.

Post-import passes run *after* the upstream importer succeeds:

1. **Source format detection** — was this VRM 0.x or 1.0?
2. **Bone-name aliasing** — stamp parallel VRChat-style aliases on every
   humanoid bone via custom properties so existing BoneCraft tools
   (weight transfer, rig validator, picker) work without a rename.
3. **Viseme blendshape surface** — copy ``A/I/U/E/O`` references into
   ``boneforge_viseme_*`` custom properties so the existing VRChat
   viseme mapper finds them.
4. **Meta / spring / blendshape preservation** — snapshot upstream data
   onto the armature as JSON custom properties (the Phase-3 unanimous
   addition).

The post-import passes are *non-destructive* — they only add data; they
do not rename, reparent, or restructure anything the upstream importer
produced. Round-tripping through the BoneCraft bridge yields a VRM that
is byte-identical to the source when nothing is edited in between.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import zipfile

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from . import bridge, meta, vroid_project

logger = logging.getLogger(__name__)


# Canonical VRM 1.0 humanoid bones → VRChat / Unity humanoid alias.
# Both VRM 0.x and VRM 1.0 share these humanoid slot names; the underlying
# Blender bone names from VRoid usually look like ``J_Bip_C_Hips`` etc.,
# but the upstream importer attaches the humanoid mapping as a property
# group we read here.
_VRM_HUMANOID_TO_VRCHAT = {
    "hips": "Hips",
    "spine": "Spine",
    "chest": "Chest",
    "upperChest": "UpperChest",
    "neck": "Neck",
    "head": "Head",
    "leftEye": "LeftEye",
    "rightEye": "RightEye",
    "jaw": "Jaw",
    "leftShoulder": "LeftShoulder",
    "leftUpperArm": "LeftUpperArm",
    "leftLowerArm": "LeftLowerArm",
    "leftHand": "LeftHand",
    "rightShoulder": "RightShoulder",
    "rightUpperArm": "RightUpperArm",
    "rightLowerArm": "RightLowerArm",
    "rightHand": "RightHand",
    "leftUpperLeg": "LeftUpperLeg",
    "leftLowerLeg": "LeftLowerLeg",
    "leftFoot": "LeftFoot",
    "leftToes": "LeftToes",
    "rightUpperLeg": "RightUpperLeg",
    "rightLowerLeg": "RightLowerLeg",
    "rightFoot": "RightFoot",
    "rightToes": "RightToes",
}

# VRM viseme mouth-shape names (VRM 0.x preset names; VRM 1.0 uses the
# same human-readable expression keys).
_VRM_VISEMES = ("a", "i", "u", "e", "o", "neutral", "blink",
                "blink_l", "blink_r", "lookup", "lookdown",
                "lookleft", "lookright")


def _humanoid_bone_map(armature_obj):
    """Read upstream humanoid bone mapping → ``{slot_name: bone_name}``.

    Tries both upstream shapes; returns ``{}`` if no map is reachable.
    """
    arm_data = armature_obj.data
    for ext_attr in ("vrm_addon_extension", "vrm_extension"):
        ext = getattr(arm_data, ext_attr, None)
        if ext is None:
            continue
        # VRM 1.0
        humanoid = (
            getattr(getattr(ext, "vrm1", None), "humanoid", None)
            or getattr(getattr(ext, "vrm0", None), "humanoid", None)
        )
        if humanoid is None:
            continue
        bones = getattr(humanoid, "human_bones", None)
        if bones is None:
            continue
        result = {}
        # VRM 1.0 puts each slot on a named attribute.
        for slot in _VRM_HUMANOID_TO_VRCHAT:
            slot_attr = getattr(bones, slot, None)
            if slot_attr is None:
                continue
            node = getattr(slot_attr, "node", None)
            if node is None:
                continue
            bone_name = getattr(node, "bone_name", None) or getattr(node, "value", None)
            if bone_name:
                result[slot] = bone_name
        if result:
            return result
    return {}


def _stamp_humanoid_aliases(armature_obj):
    """Write VRChat-style aliases onto each humanoid bone as a custom prop.

    Adds ``boneforge_humanoid_alias`` to every mapped pose bone. The
    weight transfer + validator already look up bones by VRChat name;
    this pass lets them work on a freshly imported VRoid avatar without
    a rename pass.
    """
    mapping = _humanoid_bone_map(armature_obj)
    stamped = 0
    for slot, bone_name in mapping.items():
        bone = armature_obj.data.bones.get(bone_name)
        if bone is None:
            continue
        bone["boneforge_humanoid_alias"] = _VRM_HUMANOID_TO_VRCHAT.get(slot, slot)
        stamped += 1
    return stamped


def _surface_visemes(armature_obj):
    """Stamp viseme references onto the meshes parented under the armature.

    For each mesh child, look at its shape keys; if a key name (case-
    insensitive) matches a VRM viseme, write
    ``boneforge_viseme_<name>`` = shape_key_name on the mesh object.
    Existing BoneCraft viseme tooling reads these.
    """
    surfaced = 0
    for child in armature_obj.children:
        if child.type != "MESH":
            continue
        sk = child.data.shape_keys
        if sk is None:
            continue
        names_lower = {k.name.lower(): k.name for k in sk.key_blocks}
        for viseme in _VRM_VISEMES:
            if viseme in names_lower:
                child[f"boneforge_viseme_{viseme}"] = names_lower[viseme]
                surfaced += 1
    return surfaced


def _seed_vrchat_humanoid_mapping(armature_obj):
    """Populate the VRChat humanoid mapping from the VRM humanoid data.

    A VRM carries an authoritative humanoid bone map, so the VRChat
    exporter should never make the user re-derive it by hand. Without
    this, a freshly imported avatar reports all 15 required slots
    missing until "Auto-Map Humanoid" is clicked.

    Returns the number of slots written; 0 when the VRChat phase is
    disabled or the VRM carried no humanoid map.
    """
    mapping = _humanoid_bone_map(armature_obj)
    if not mapping:
        return 0

    # Lazy import: the VRChat phase is togglable in the Tool Registry,
    # and the VRM bridge must keep working when it is switched off.
    try:
        from boneforge.vrchat.humanoid.mapper import (
            HumanoidMapping, get_mapping, save_mapping,
        )
    except ImportError:
        logger.info(
            "[BoneCraft] VRChat phase unavailable; skipped humanoid seed"
        )
        return 0

    bone_names = {bone.name for bone in armature_obj.data.bones}
    # Never clobber a mapping the user already curated by hand.
    existing = get_mapping(armature_obj).to_dict()
    seeded = dict(existing)

    written = 0
    for vrm_slot, bone_name in mapping.items():
        unity_slot = _VRM_HUMANOID_TO_VRCHAT.get(vrm_slot)
        if not unity_slot or bone_name not in bone_names:
            continue
        if existing.get(unity_slot):
            continue
        seeded[unity_slot] = bone_name
        written += 1

    if written:
        save_mapping(armature_obj, HumanoidMapping(seeded))
    return written


def _import_vrm_and_run_passes(op, context, filepath):
    """Import ``filepath`` via upstream, run post-import passes.

    Shared by :class:`BF_OT_VRMImport` and :class:`BF_OT_VRoidImport` so
    a VRM pulled out of a VRoid archive gets exactly the same treatment
    as one picked directly. Reports through ``op`` and returns the list
    of armatures the upstream importer produced, or ``None`` on failure.
    """
    # Snapshot the set of armatures so we can identify what the
    # upstream importer added. ``import_scene.vrm`` does not return
    # the new object on its own.
    before = {o.name for o in bpy.data.objects if o.type == "ARMATURE"}

    try:
        bpy.ops.import_scene.vrm(filepath=filepath)
    except (RuntimeError, AttributeError) as exc:
        op.report({"ERROR"}, f"VRM import failed: {exc}")
        logger.exception("[BoneCraft] VRM import failed")
        return None

    after = {o.name for o in bpy.data.objects if o.type == "ARMATURE"}
    new_arms = [bpy.data.objects[name] for name in (after - before)]
    if not new_arms:
        # Some upstream versions reuse an existing armature object;
        # fall back to the active object.
        obj = context.active_object
        if obj is not None and obj.type == "ARMATURE":
            new_arms = [obj]

    for arm in new_arms:
        try:
            meta.preserve_to_armature(arm)
            aliases = _stamp_humanoid_aliases(arm)
            visemes = _surface_visemes(arm)
            slots = _seed_vrchat_humanoid_mapping(arm)
            logger.info(
                "[BoneCraft] post-import passes on %s: "
                "%d humanoid aliases, %d visemes surfaced, "
                "%d VRChat humanoid slots seeded",
                arm.name, aliases, visemes, slots,
            )
        except Exception as exc:
            # Post-import passes are best-effort. Never let them
            # break a successful upstream import.
            logger.warning(
                "[BoneCraft] post-import pass failed on %s: %s",
                arm.name, exc,
            )

    return new_arms


class BF_OT_VRMImport(Operator):
    """Import a .vrm via the upstream add-on, then run BoneCraft passes."""

    bl_idname = "boneforge.vrm_import"
    bl_label = "Import VRM…"
    bl_description = (
        "Import a VRM file via vrm-addon-for-blender, then preserve "
        "license / spring / expression data on the armature and stamp "
        "VRChat-compatible humanoid aliases for use with BoneCraft tools"
    )
    bl_options = {"REGISTER", "UNDO"}

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.vrm", options={"HIDDEN"})

    def invoke(self, context, event):
        # Fail fast if upstream isn't there — better than silently
        # opening a file dialog that leads nowhere.
        if bridge.find_vrm_addon() is None:
            self.report(
                {"ERROR"},
                "VRM Add-on for Blender not detected. Click "
                "'Install / Enable VRM Add-on' in the BoneCraft VRM "
                "panel first.",
            )
            return {"CANCELLED"}
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if not self.filepath:
            self.report({"ERROR"}, "No file selected")
            return {"CANCELLED"}
        if bridge.find_vrm_addon() is None:
            self.report({"ERROR"}, "VRM Add-on not available")
            return {"CANCELLED"}

        new_arms = _import_vrm_and_run_passes(self, context, self.filepath)
        if new_arms is None:
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            f"Imported VRM ({len(new_arms)} armature(s)); "
            "license + spring data preserved on armature.",
        )
        return {"FINISHED"}


# ── VRoid download handling ──────────────────────────────────────
#
# VRoid Studio's own project format (``.vroid``) is proprietary and
# undocumented: no Blender add-on can read it, and nothing can write it
# either — VRoid Studio cannot re-import a .vrm back into a project. It
# is a one-way source format. Selecting one here therefore cannot import
# geometry; the best we can do is say so precisely and point at the
# Export → VRM step that produces something Blender *can* read.
#
# The ``.zip`` half is the part that does real work: VRoid Hub and Booth
# commonly ship avatars as an archive with the .vrm nested inside, which
# the plain "Import VRM…" browser filters out of sight entirely.

_VROID_EXPORT_HELP = "https://vroid.com/en/studio"


def _find_vrm_in_zip(zip_path, dest_dir):
    """Extract ``zip_path`` into ``dest_dir``; return the .vrm paths found.

    Returns ``(vrm_paths, member_names)``. ``member_names`` is used to
    build a useful error message when the archive holds no VRM at all.
    """
    with zipfile.ZipFile(zip_path) as archive:
        member_names = archive.namelist()
        # Refuse absolute paths and parent-directory traversal rather
        # than trusting archive member names on disk.
        safe_members = []
        for name in member_names:
            if name.endswith("/"):
                continue
            normalized = os.path.normpath(name).replace("\\", "/")
            if normalized.startswith(("/", "../")) or os.path.isabs(normalized):
                logger.warning(
                    "[BoneCraft] skipping unsafe archive member: %s", name
                )
                continue
            safe_members.append(name)
        archive.extractall(dest_dir, members=safe_members)

    vrm_paths = []
    for root, _dirs, files in os.walk(dest_dir):
        for filename in files:
            if filename.lower().endswith(".vrm"):
                vrm_paths.append(os.path.join(root, filename))
    return sorted(vrm_paths), member_names


class BF_OT_VRoidImport(Operator):
    """Import a VRoid download — unpacks a .zip, explains a .vroid."""

    bl_idname = "boneforge.vroid_import"
    bl_label = "Import VRoid Download…"
    bl_description = (
        "Import a VRoid Hub / Booth avatar download. Accepts a .zip "
        "archive and imports the .vrm nested inside it. A .vroid "
        "project file cannot be read by Blender and is explained rather "
        "than imported"
    )
    bl_options = {"REGISTER", "UNDO"}

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(
        default="*.zip;*.vroid", options={"HIDDEN"}
    )

    def invoke(self, context, event):
        # Same fail-fast gate as the plain VRM importer: a .zip is only
        # useful to us if the upstream add-on can read what's inside.
        if bridge.find_vrm_addon() is None:
            self.report(
                {"ERROR"},
                "VRM Add-on for Blender not detected. Click "
                "'Install / Enable VRM Add-on' in the BoneCraft VRM "
                "panel first.",
            )
            return {"CANCELLED"}
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def _inspect_vroid_project(self, context):
        """Read the .vroid wrapper and populate the hand-off card.

        BoneCraft cannot convert the project — see ``vroid_project`` for
        why — so the useful move is to confirm the file, show the user
        which avatar it is, and put VRoid Studio one click away.
        """
        settings = getattr(context.scene, "boneforge_vrm_settings", None)
        info = vroid_project.read_project_meta(self.filepath)

        if info is None:
            self.report(
                {"ERROR"},
                "This does not look like a valid VRoid Studio project "
                "(no readable meta.json inside).",
            )
            return {"CANCELLED"}

        icon_id = 0
        if info["has_thumbnail"]:
            thumb = vroid_project.extract_thumbnail(self.filepath)
            if thumb:
                icon_id = vroid_project.load_thumbnail_preview(thumb)

        if settings is not None:
            settings.vroid_project_path = self.filepath
            settings.vroid_project_version = info["version"]
            settings.vroid_project_summary = (
                f"{os.path.basename(self.filepath)} — "
                f"{info['size_mb']:.1f} MB"
            )
            settings.vroid_thumbnail_icon = icon_id
            # Pre-point the VRM importer at the project's folder, since
            # VRoid Studio defaults its export there.
            settings.vroid_last_folder = os.path.dirname(self.filepath)

        self.report(
            {"INFO"},
            f"VRoid Studio {info['version']} project loaded. BoneCraft "
            "cannot convert .vroid directly — use 'Open in VRoid Studio' "
            "in the VRM panel, run Export -> VRM, then import that .vrm.",
        )
        logger.info(
            "[BoneCraft] inspected .vroid project: %s (VRoid %s)",
            self.filepath, info["version"],
        )
        return {"FINISHED"}

    def execute(self, context):
        if not self.filepath:
            self.report({"ERROR"}, "No file selected")
            return {"CANCELLED"}
        if bridge.find_vrm_addon() is None:
            self.report({"ERROR"}, "VRM Add-on not available")
            return {"CANCELLED"}

        extension = os.path.splitext(self.filepath)[1].lower()

        if extension == ".vroid":
            # The wrapper is readable even though the model payload is
            # not, so inspect it and hand off rather than dead-ending.
            return self._inspect_vroid_project(context)

        if extension != ".zip":
            self.report(
                {"ERROR"},
                "Select a .zip VRoid download, or use 'Import VRM…' for "
                "a plain .vrm file.",
            )
            return {"CANCELLED"}

        temp_dir = tempfile.mkdtemp(prefix="boneforge_vroid_")
        try:
            try:
                vrm_paths, member_names = _find_vrm_in_zip(
                    self.filepath, temp_dir
                )
            except (zipfile.BadZipFile, OSError) as exc:
                self.report({"ERROR"}, f"Could not read archive: {exc}")
                logger.exception("[BoneCraft] VRoid archive read failed")
                return {"CANCELLED"}

            if not vrm_paths:
                if any(n.lower().endswith(".vroid") for n in member_names):
                    self.report(
                        {"ERROR"},
                        "This archive contains a .vroid project file but "
                        "no .vrm. Extract it, then select the .vroid here "
                        "to open it in VRoid Studio and Export -> VRM.",
                    )
                else:
                    self.report(
                        {"ERROR"},
                        f"No .vrm found inside the archive "
                        f"({len(member_names)} entries).",
                    )
                return {"CANCELLED"}

            chosen = vrm_paths[0]
            if len(vrm_paths) > 1:
                logger.info(
                    "[BoneCraft] archive holds %d VRM files; importing %s",
                    len(vrm_paths), os.path.basename(chosen),
                )

            new_arms = _import_vrm_and_run_passes(self, context, chosen)
            if new_arms is None:
                return {"CANCELLED"}

            extra = ""
            if len(vrm_paths) > 1:
                extra = (
                    f" ({len(vrm_paths)} VRM files in archive — imported "
                    f"'{os.path.basename(chosen)}'; extract the archive "
                    "manually to pick a different one)"
                )
            self.report(
                {"INFO"},
                f"Imported '{os.path.basename(chosen)}' from archive "
                f"({len(new_arms)} armature(s)){extra}.",
            )
            return {"FINISHED"}
        finally:
            # A .vrm is a self-contained GLB — textures ride inside the
            # binary, so nothing references the temp copy after import.
            shutil.rmtree(temp_dir, ignore_errors=True)
