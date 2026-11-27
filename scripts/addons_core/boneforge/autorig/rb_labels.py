"""Short labels for Rig Builder's compact (narrow Tool Shelf) layout.

Pure Python. Keys are the exact English strings Rig Builder draws with
``T()``; values are the short forms (an empty value hides the line when
compact). ``tests/test_rb_labels.py`` checks every key still exists in
the Rig Builder source files, so renamed labels are caught.
"""

MAX_SHORT = 15

SOURCES = (
    "taskboard/sidebar.py",
    "autorig/wizard.py",
    "autorig/mannequin.py",
)

SHORT = {
    # Quick Rig (taskboard/sidebar.py)
    "Pick a rig source below to start.": "Pick a source",
    "Quick Rig - premade armatures": "Quick Rig",
    "Rigify must be enabled to select Rigify default rigs.": "Rigify is off",
    "No Rigify required:": "No Rigify:",
    "BoneCraft Basic Humanoid (19 bones)": "Basic Humanoid",
    "Options for the next click:": "Options:",
    "Fit Rig to Active Mesh": "Fit to Mesh",
    "Add IK/FK Controllers": "IK/FK",
    "Generate Control Rig (active metarig)": "Make Controls",
    "Inspect Active Rig Controls": "Inspect Rig",
    "Need precise marker placement? Use the Auto-Rig Wizard below.": "",
    "Switch active rig's rest pose:": "Rest pose:",
    "Select an armature to enable T-Pose / A-Pose.": "Pick armature",
    "Diagnose Quick Rig (print to console)": "Diagnose",
    "Auto-Rig Wizard": "Wizard",
    "Dropped rig: fit it to a mesh": "Dropped rig",
    # Auto-Rig Wizard (autorig/wizard.py)
    "Select the mesh to rig:": "Mesh to rig:",
    "What should be generated?": "Generate:",
    "Generation Options:": "Options:",
    "Generate Control Shapes": "Ctrl Shapes",
    "Viewport Display": "Display",
    "(no armature active)": "(no armature)",
    "In-Front redraws every frame — toggle off if laggy.": "",
    "Place body markers on the mesh:": "Body markers:",
    "Guess Markers from Mesh": "Guess",
    "Mirror Symmetry": "Mirror",
    "Smart Detection": "Detect",
    "No detection results yet": "No results",
    "No finger bones will be generated.": "No fingers",
    "Wrist will be a terminal bone.": "Wrist = end",
    "Click Next to continue.": "Then Next",
    "Mirror left hand to right": "Mirror L→R",
    "Guess Finger Markers": "Guess",
    "Right Hand (mirrored):": "Right (mirror):",
    "Confirm All Placed": "Confirm",
    "Place facial markers:": "Face markers:",
    "Guess Face Markers": "Guess",
    "Precision Markers (Optional)": "Precision",
    "Guess Precision": "Guess",
    "Review marker placement:": "Review:",
    "All checks passed": "All OK",
    "Controller Density:": "Density:",
    "Generating rig...": "Generating…",
    "Rig generated successfully!": "Rig ready!",
    "Rigify-compatible bone names": "Rigify names",
    "Collection UI populated": "Collections",
    "Visibility bookmarks created": "Bookmarks",
    "Switch to the BoneCraft tab for posing,": "Next: BoneCraft",
    "weight tools, and VRChat optimization.": "",
    "Retarget and Cats cleanup all live there.": "",
    "No mesh yet? Add a Mannequin to preview deformation.": "No mesh?",
    "Quick Mannequin": "Mannequin",
    # Mannequin (autorig/mannequin.py)
    "Select an armature to generate a mannequin for it.": "Pick armature",
}


def trim(text, limit=MAX_SHORT):
    """Fit *text* into *limit* characters (ellipsis included), cutting at a word."""
    if len(text) <= limit:
        return text
    head = text[:limit - 1]
    if " " in head:
        head = head.rsplit(" ", 1)[0]
    return head.rstrip(" :,;-(") + "…"


def make_shortener(translate, current_lang):
    """Return ``shorten(text)`` mapping translated full labels to short ones.

    *translate* is ``T``; *current_lang* returns the active language code.
    The translated table is rebuilt when the language changes. Text not in
    the table (names found at runtime, step titles) is trimmed instead.
    """
    cache = {}

    def shorten(text):
        if not text:
            return text
        lang = current_lang()
        table = cache.get(lang)
        if table is None:
            table = {translate(k): (translate(v) if v else "")
                     for k, v in SHORT.items()}
            cache.clear()
            cache[lang] = table
        short = table.get(text)
        return trim(text if short is None else short)

    return shorten
