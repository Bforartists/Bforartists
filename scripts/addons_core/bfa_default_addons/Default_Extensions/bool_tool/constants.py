import os


# Paths
ICONS_PATH = os.path.join(os.path.dirname(__file__), "ui", "icons")

# Object types that can have evaluated mesh, and can be converted to Mesh.
CONVERTABLE_TYPES = (
    'CURVE',
    'CURVES',
    'FONT',
    # 'POINTCLOUD',    # Doesn't work in Blender 5.2
    # 'GREASEPENCIL'   # Doesn't work in Blender 5.2
    'EMPTY',
)
